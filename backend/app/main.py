from fastapi import FastAPI, UploadFile, File, HTTPException, Depends, Form, Query
from fastapi.middleware.cors import CORSMiddleware
from typing import List, Optional
import uuid
import os
from dotenv import load_dotenv

# Import services after FastAPI initialization
from app.services.s3_service import S3Service
from app.services.document_service import DocumentService
from app.services.rag_service import RAGService
from app.models.models import DocumentResponse, QuestionRequest, QuestionResponse, FolderInfo

load_dotenv()

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
document_service = DocumentService(s3_service)
rag_service = RAGService()

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
        # Generate a unique ID for the document
        doc_id = str(uuid.uuid4())
        
        # Read file content
        content = await file.read()
        
        # Process document for RAG
        document_info = document_service.process_document(
            doc_id=doc_id,
            filename=file.filename,
            content=content,
            source_name=source_name,
            description=description
        )
        
        return DocumentResponse(
            id=doc_id,
            filename=file.filename,
            source=source_name,
            description=description,
            s3_url=document_info["s3_url"]
        )
    
    except Exception as e:
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

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True) 