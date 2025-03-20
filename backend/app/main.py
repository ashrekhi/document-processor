from fastapi import FastAPI, UploadFile, File, HTTPException, Depends, Form, Query
from fastapi.middleware.cors import CORSMiddleware
from typing import List, Optional
import uuid
import os
import sys
from dotenv import load_dotenv
import pathlib
from fastapi.responses import JSONResponse
import time
import re

# Add module path for imports to work in different contexts
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(os.path.dirname(current_dir))
if parent_dir not in sys.path:
    sys.path.append(parent_dir)

# Try to import modules with different import styles
try:
    from backend.app.routers import documents, folders, sessions
except ImportError:
    try:
        from app.routers import documents, folders, sessions
    except ImportError:
        print("Import error with sessions module")
        # Use a fallback import strategy if the above fails
        import importlib
        documents = importlib.import_module("backend.app.routers.documents")
        folders = importlib.import_module("backend.app.routers.folders")
        try:
            sessions = importlib.import_module("backend.app.routers.sessions")
        except ImportError:
            try:
                sessions = importlib.import_module("app.routers.sessions")
            except ImportError:
                print("Warning: Could not import sessions module, some features may not be available")
                sessions = None

# Import services after FastAPI initialization
try:
    from backend.app.services.document_service import DocumentService
    from backend.app.services.rag_service import RAGService
    from backend.app.services.s3_service import S3Service
    from backend.app.models.models import DocumentResponse, QuestionRequest, QuestionResponse, FolderInfo
except ImportError:
    from app.services.document_service import DocumentService
    from app.services.rag_service import RAGService
    from app.services.s3_service import S3Service
    from app.models.models import DocumentResponse, QuestionRequest, QuestionResponse, FolderInfo

# Load environment variables - for local development and production
load_dotenv()

# Check if environment variables are loaded
openai_api_key = os.getenv('OPENAI_API_KEY')
pinecone_api_key = os.getenv('PINECONE_API_KEY')

print(f"OPENAI_API_KEY loaded: {'Yes' if openai_api_key else 'No'}")
print(f"PINECONE_API_KEY loaded: {'Yes' if pinecone_api_key else 'No'}")

app = FastAPI(title="Document Processor API")

# Configure CORS - extract allowed origins from environment variables or use default
allowed_origins = os.getenv("ALLOWED_ORIGINS", "*").split(",")
print(f"CORS allowed origins: {allowed_origins}")

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
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
app.include_router(documents.router, prefix="/api/documents", tags=["documents"])
app.include_router(folders.router, prefix="/api/folders", tags=["folders"])
if sessions:
    print("Including sessions router")
    app.include_router(sessions.router, prefix="/api/sessions", tags=["sessions"])
else:
    print("Sessions router not available, skipping")

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

@app.post("/ask", response_model=QuestionResponse, tags=["questions"])
async def unified_ask_question(request: QuestionRequest) -> QuestionResponse:
    """Endpoint to ask a question about documents in a specific folder"""
    # Start timer
    start_time = time.time()
    
    # Print detailed request information
    print(f"{'='*80}")
    print(f"ENDPOINT /ask: Request received at {time.strftime('%H:%M:%S')}")
    print(f"ENDPOINT /ask: Full request object: {request}")
    print(f"ENDPOINT /ask: Question: '{request.question}'")
    print(f"ENDPOINT /ask: Model: '{request.model}'")
    print(f"ENDPOINT /ask: Folder: '{request.folder}'")
    
    # Validate the request
    if not request.question or request.question.strip() == "":
        error_msg = "Question cannot be empty"
        print(f"ENDPOINT /ask ERROR: {error_msg}")
        return QuestionResponse(
            question="Empty Question", 
            answer=f"Error: {error_msg}",
            model=request.model
        )
        
    if not request.model or request.model.strip() == "":
        request.model = "gpt-3.5-turbo"
        print(f"ENDPOINT /ask: No model specified, defaulting to {request.model}")
    
    if not request.folder or request.folder.strip() == "":
        error_msg = "Folder name cannot be empty"
        print(f"ENDPOINT /ask ERROR: {error_msg}")
        return QuestionResponse(
            question=request.question,
            answer=f"Error: {error_msg}. Please specify a folder to search in.",
            model=request.model
        )
    
    # Process folder-based question
    try:
        print(f"ENDPOINT /ask: Processing folder-based question for folder '{request.folder}'")
        
        # Call DocumentService
        print(f"ENDPOINT /ask: Calling DocumentService at {time.strftime('%H:%M:%S')}")
        answer = document_service.ask_question_in_folder(
            request.question,
            request.folder,
            request.model
        )
        elapsed = time.time() - start_time
        print(f"ENDPOINT /ask: DocumentService returned answer in {elapsed:.2f} seconds")
        
        # Preview the answer for logging
        answer_preview = answer[:150].replace('\n', ' ') + '...' if len(answer) > 150 else answer
        print(f"ENDPOINT /ask: Answer preview: '{answer_preview}'")
        
        return QuestionResponse(
            question=request.question,
            answer=answer,
            model=request.model
        )
        
    except Exception as e:
        # Catch-all for unexpected errors
        error_type = type(e).__name__
        error_msg = f"Unexpected {error_type} while processing question: {str(e)}"
        print(f"ENDPOINT /ask ERROR: {error_msg}")
        import traceback
        print(f"ENDPOINT /ask ERROR: Full error details:\n{traceback.format_exc()}")
        elapsed = time.time() - start_time
        print(f"ENDPOINT /ask ERROR: Request failed after {elapsed:.2f} seconds")
        return QuestionResponse(
            question=request.question,
            answer=f"An unexpected error occurred: {str(e)}",
            model=request.model
        )

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
    start_time = time.time()
    request_id = str(uuid.uuid4())
    
    print(f"REQUEST [{request_id}]: {request.method} {request.url.path}")
    print(f"REQUEST HEADERS [{request_id}]: {request.headers.get('content-type', '')}")
    
    # Process the request WITHOUT consuming the body
    try:
        response = await call_next(request)
        process_time = time.time() - start_time
        print(f"RESPONSE [{request_id}]: {response.status_code} (took {process_time:.2f}s)")
        return response
    except Exception as e:
        print(f"ERROR [{request_id}]: {str(e)}")
        import traceback
        print(f"ERROR TRACEBACK [{request_id}]:\n{traceback.format_exc()}")
        # Re-raise the exception to be handled by the global exception handler
        raise

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True) 