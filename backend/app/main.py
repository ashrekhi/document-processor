from fastapi import FastAPI, UploadFile, File, HTTPException, Depends, Form, Query
from fastapi.middleware.cors import CORSMiddleware
from typing import List, Optional
import uuid
import os
from dotenv import load_dotenv
from app.routers import documents, folders, questions
from app.services.s3_service import S3Service
import pathlib
from fastapi.responses import JSONResponse

# Import services after FastAPI initialization
from app.services.document_service import DocumentService
from app.services.rag_service import RAGService
from app.models.models import DocumentResponse, QuestionRequest, QuestionResponse, FolderInfo

# Use absolute path to .env file
env_path = "/Users/arekhi/Documents/GitHub/document-processor/.env"
print(f"Looking for .env file at: {env_path}")

# Load environment variables from the specified path
load_dotenv(dotenv_path=env_path)

# Check if environment variables are loaded
openai_api_key = os.getenv('OPENAI_API_KEY')
pinecone_api_key = os.getenv('PINECONE_API_KEY')

print(f"OPENAI_API_KEY loaded: {'Yes' if openai_api_key else 'No'}")
print(f"PINECONE_API_KEY loaded: {'Yes' if pinecone_api_key else 'No'}")

app = FastAPI(title="Document Processor API")

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, replace with specific origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize services
s3_service = S3Service()
s3_service.ensure_required_folders()
document_service = DocumentService(s3_service)
rag_service = RAGService()

# Include routers
app.include_router(documents.router, prefix="/documents", tags=["documents"])
app.include_router(folders.router, prefix="/folders", tags=["folders"])
app.include_router(questions.router, prefix="/ask", tags=["questions"])

@app.get("/")
def read_root():
    return {"message": "Document Processor API"}

@app.post("/documents/upload", response_model=DocumentResponse)
async def upload_document(
    file: UploadFile = File(...),
    source_name: str = Form(...),
    description: Optional[str] = Form(None)
):
    """
    Upload a document to the master bucket and process it for RAG.
    """
    try:
        print(f"UPLOAD ENDPOINT: Starting upload for file={file.filename}, source_name={source_name}, description={description}")
        
        # Read file content
        content = await file.read()
        print(f"UPLOAD ENDPOINT: Read {len(content)} bytes from file")
        
        # Process document for RAG (let the method generate the doc_id)
        print(f"UPLOAD ENDPOINT: Calling process_document with filename={file.filename}, content_length={len(content)}, folder={source_name}")
        doc_id = document_service.process_document(
            filename=file.filename,
            content=content,
            folder=source_name  # Use source_name as folder
        )
        print(f"UPLOAD ENDPOINT: process_document returned doc_id={doc_id}")
        
        # Get the document info
        document_info = {
            "id": doc_id,
            "filename": file.filename,
            "source": source_name,
            "description": description,
            "s3_url": f"s3://{s3_service.master_bucket}/{source_name}/{doc_id}_{file.filename}"
        }
        print(f"UPLOAD ENDPOINT: Created document_info={document_info}")
        
        return DocumentResponse(
            id=doc_id,
            filename=file.filename,
            source=source_name,
            description=description,
            s3_url=document_info["s3_url"]
        )
    
    except Exception as e:
        print(f"UPLOAD ENDPOINT ERROR: {str(e)}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Error uploading document: {str(e)}")

@app.get("/documents", response_model=List[DocumentResponse])
async def list_documents():
    """
    List all uploaded documents.
    """
    try:
        documents = document_service.list_documents()
        return documents
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error listing documents: {str(e)}")

@app.delete("/documents/{doc_id}")
async def delete_document(doc_id: str):
    """
    Delete a document and its associated data.
    """
    try:
        document_service.delete_document(doc_id)
        return {"message": f"Document {doc_id} deleted successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error deleting document: {str(e)}")

@app.post("/ask", response_model=QuestionResponse)
async def ask_question(request: QuestionRequest):
    """
    Ask a question about the uploaded documents.
    """
    try:
        answer = rag_service.answer_question(
            question=request.question,
            doc_ids=request.document_ids,
            model=request.model
        )
        return QuestionResponse(
            question=request.question,
            answer=answer,
            document_ids=request.document_ids,
            model=request.model
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing question: {str(e)}")

@app.get("/folders")
async def get_folders():
    """
    Get information about available folders in the master bucket.
    """
    try:
        folder_info = document_service.get_folder_info()
        return folder_info
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting folder info: {str(e)}")

@app.post("/folders")
async def create_folder(folder_name: str = Form(...)):
    """
    Create a new folder in the master bucket.
    """
    try:
        s3_url = s3_service.create_folder(folder_name)
        return {"message": f"Folder {folder_name} created successfully", "s3_url": s3_url}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error creating folder: {str(e)}")

@app.delete("/folders/{folder_name}")
async def delete_folder(folder_name: str):
    """
    Delete a folder and all its contents.
    """
    try:
        s3_service.delete_folder(folder_name)
        return {"message": f"Folder {folder_name} deleted successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error deleting folder: {str(e)}")

@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    """Global exception handler to capture more details about errors"""
    import traceback
    error_details = {
        "error": str(exc),
        "type": type(exc).__name__,
        "path": request.url.path,
        "method": request.method,
        "traceback": traceback.format_exc()
    }
    print(f"GLOBAL EXCEPTION HANDLER: {error_details}")
    return JSONResponse(
        status_code=500,
        content={"detail": f"Error: {str(exc)}"}
    )

@app.middleware("http")
async def log_requests(request, call_next):
    """Middleware to log all requests"""
    print(f"REQUEST: {request.method} {request.url.path}")
    try:
        # For multipart/form-data requests (file uploads), don't try to decode the body
        content_type = request.headers.get("content-type", "")
        if content_type and "multipart/form-data" in content_type:
            print(f"REQUEST BODY: [Binary data - multipart/form-data]")
        else:
            # For other requests, try to decode the body as UTF-8
            body = await request.body()
            if body:
                try:
                    print(f"REQUEST BODY: {body.decode()}")
                except UnicodeDecodeError:
                    print(f"REQUEST BODY: [Binary data - {len(body)} bytes]")
    except Exception as e:
        print(f"Error reading request body: {str(e)}")
    
    # Process the request
    response = await call_next(request)
    
    print(f"RESPONSE: {response.status_code}")
    return response

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True) 