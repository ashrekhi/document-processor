from fastapi import APIRouter, File, Form, UploadFile, Depends, HTTPException
import uuid
from app.services.document_service import DocumentService
from app.services.s3_service import S3Service
from app.services.utils import get_document_service
import json

router = APIRouter()

@router.post("/documents/upload")
async def upload_document(
    file: UploadFile = File(...),
    folder: str = Form(None),
    document_service: DocumentService = Depends(get_document_service)
):
    """Upload a document"""
    try:
        print(f"ROUTER UPLOAD: Starting upload of document: {file.filename} to folder: {folder}")
        
        # Read the file content
        content = await file.read()
        print(f"ROUTER UPLOAD: Read {len(content)} bytes from file")
        
        # Check file size
        max_size = 10 * 1024 * 1024  # 10 MB
        if len(content) > max_size:
            print(f"ROUTER UPLOAD: File too large: {len(content)} bytes")
            raise HTTPException(status_code=400, detail="File too large (max 10 MB)")
        
        # Process the document
        print(f"ROUTER UPLOAD: Calling document_service.process_document for {file.filename}")
        # Print the signature of the method
        import inspect
        print(f"ROUTER UPLOAD: Method signature: {inspect.signature(document_service.process_document)}")
        
        doc_id = document_service.process_document(file.filename, content, folder)
        print(f"ROUTER UPLOAD: Document processed successfully with ID: {doc_id}")
        
        # Check document status
        status = document_service.get_document_status(doc_id)
        print(f"ROUTER UPLOAD: Document status after processing: {status}")
        
        return {
            "message": "Document uploaded successfully", 
            "doc_id": doc_id,
            "status": status
        }
    except Exception as e:
        print(f"ROUTER UPLOAD ERROR: {str(e)}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/documents/{doc_id}/status")
async def get_document_status(
    doc_id: str,
    document_service: DocumentService = Depends(get_document_service)
):
    """Get the processing status of a document"""
    try:
        status = document_service.get_document_status(doc_id)
        
        # Get more detailed information if available
        try:
            # Get metadata from S3
            metadata_key = f"metadata/{doc_id}.json"
            metadata_obj = document_service.s3_service.s3_client.get_object(
                Bucket=document_service.s3_service.master_bucket,
                Key=metadata_key
            )
            metadata = json.loads(metadata_obj['Body'].read().decode('utf-8'))
            
            return {
                "status": status,
                "metadata": metadata,
                "filename": metadata.get("filename", ""),
                "upload_date": metadata.get("upload_date", ""),
                "processed": metadata.get("processed", False),
                "processing": metadata.get("processing", False),
                "error": metadata.get("error", "")
            }
        except Exception as metadata_error:
            print(f"Error getting metadata for document {doc_id}: {str(metadata_error)}")
            return {"status": status}
    except Exception as e:
        print(f"Error getting document status: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/documents/namespaces")
async def list_namespaces(
    document_service: DocumentService = Depends(get_document_service)
):
    """List all available namespaces"""
    try:
        namespaces = document_service.vector_db_service.list_namespaces()
        return {"namespaces": namespaces}
    except Exception as e:
        print(f"Error listing namespaces: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/documents/by-namespace/{namespace}")
async def get_documents_by_namespace(
    namespace: str,
    document_service: DocumentService = Depends(get_document_service)
):
    """Get all documents in a namespace"""
    try:
        documents = document_service.get_documents_by_namespace(namespace)
        return {"documents": documents}
    except Exception as e:
        print(f"Error getting documents by namespace: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/documents/similarity")
async def compare_documents(
    request_data: dict,
    document_service: DocumentService = Depends(get_document_service)
):
    """Compare two documents for similarity"""
    try:
        doc1_id = request_data.get("doc1_id")
        doc2_id = request_data.get("doc2_id")
        method = request_data.get("method", "hybrid")
        namespace = request_data.get("namespace")
        
        if not doc1_id or not doc2_id:
            raise HTTPException(status_code=400, detail="Both doc1_id and doc2_id are required")
        
        # Validate the method
        valid_methods = ["embedding", "text", "hybrid", "chunked"]
        if method not in valid_methods:
            raise HTTPException(
                status_code=400, 
                detail=f"Invalid method. Must be one of: {', '.join(valid_methods)}"
            )
        
        print(f"SIMILARITY: Comparing documents {doc1_id} and {doc2_id} using method {method}")
        
        # Get the similarity result
        result = document_service.vector_db_service.calculate_document_similarity_by_id(
            doc1_id, doc2_id, method, namespace
        )
        
        return {
            "similarity": result.get("similarity", 0.0),
            "method": result.get("method", method),
            "comparison_time": result.get("comparison_time", 0.0),
            "doc1_id": doc1_id,
            "doc2_id": doc2_id,
            "namespace": namespace,
            "details": result
        }
    except Exception as e:
        print(f"Error comparing documents: {str(e)}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/documents/{doc_id}/similar")
async def get_similar_documents(
    doc_id: str,
    namespace: str = None,
    top_k: int = 5,
    document_service: DocumentService = Depends(get_document_service)
):
    """Find documents similar to a given document"""
    try:
        # Check if document exists
        status = document_service.get_document_status(doc_id)
        if not status:
            raise HTTPException(status_code=404, detail=f"Document {doc_id} not found")
        
        # Get similar documents
        similar_docs = document_service.vector_db_service.get_similar_documents(
            doc_id, top_k, namespace
        )
        
        return {
            "doc_id": doc_id,
            "namespace": namespace,
            "similar_documents": similar_docs
        }
    except Exception as e:
        print(f"Error finding similar documents: {str(e)}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e)) 