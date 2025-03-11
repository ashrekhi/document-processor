from fastapi import FastAPI, UploadFile, File, HTTPException, Depends, Form
from fastapi.middleware.cors import CORSMiddleware
from typing import List, Optional
import uuid
import os
from dotenv import load_dotenv

from app.services.document_service import DocumentService
from app.services.s3_service import S3Service
from app.services.rag_service import RAGService
from app.models.models import DocumentResponse, QuestionRequest, QuestionResponse

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
    Upload a document to a dedicated S3 bucket and process it for RAG.
    Each document gets its own bucket for isolation.
    """
    try:
        # Generate a unique ID for the document
        doc_id = str(uuid.uuid4())
        
        # Create a new bucket for this document
        bucket_name = f"doc-processor-{doc_id}"
        s3_service.create_bucket(bucket_name)
        
        # Save file to S3
        content = await file.read()
        file_extension = os.path.splitext(file.filename)[1]
        s3_key = f"{doc_id}{file_extension}"
        
        s3_url = s3_service.upload_file(bucket_name, s3_key, content)
        
        # Process document for RAG
        document_info = document_service.process_document(
            doc_id=doc_id,
            filename=file.filename,
            bucket_name=bucket_name,
            s3_key=s3_key,
            source_name=source_name,
            description=description
        )
        
        return DocumentResponse(
            id=doc_id,
            filename=file.filename,
            source=source_name,
            description=description,
            s3_url=s3_url
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
    Delete a document and its associated bucket.
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
            doc_ids=request.document_ids
        )
        return QuestionResponse(
            question=request.question,
            answer=answer,
            document_ids=request.document_ids
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing question: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True) 