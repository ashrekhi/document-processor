from fastapi import APIRouter, HTTPException, Depends
from app.models.models import QuestionRequest, QuestionResponse
from app.services.rag_service import RAGService
from app.services.document_service import DocumentService
from app.services.utils import get_document_service
import time
import traceback
from typing import Dict, Any, List, Optional

router = APIRouter()

# Initialize RAG service
rag_service = RAGService()

@router.post("/", response_model=QuestionResponse)
async def ask_question(request: QuestionRequest):
    """
    Ask a question about the uploaded documents.
    """
    try:
        print(f"\n{'#'*100}")
        print(f"ROUTER /ask/ - REQUEST RECEIVED:")
        print(f"Question: '{request.question}'")
        print(f"Model: '{request.model}'")
        
        # Debug document ID handling - this is likely the issue
        print(f"Request object fields: {request.dict()}")
        print(f"Document IDs (document_ids): {request.document_ids}")
        print(f"Document IDs (doc_ids): {request.doc_ids}")
        
        # Handle both document_ids and doc_ids to ensure we're getting all IDs
        actual_doc_ids = request.document_ids if request.document_ids else request.doc_ids
        print(f"ROUTER /ask/ - USING DOCUMENT IDs: {actual_doc_ids}")
        
        request_time = time.time()
        
        # Log the model details
        if request.model == "gpt-4-turbo":
            print(f"ROUTER /ask/ - USING GPT-4 TURBO MODEL")
            print(f"Checking if model name is correct - should be 'gpt-4-turbo-preview' instead of 'gpt-4-turbo'")
            # Auto-correct model name if needed
            model = "gpt-4-turbo-preview"
            print(f"ROUTER /ask/ - ADJUSTED MODEL to '{model}'")
        else:
            model = request.model
            
        # Process the question, using actual_doc_ids to ensure we get all IDs
        answer = rag_service.answer_question(
            question=request.question,
            doc_ids=actual_doc_ids,
            model=model
        )
        
        response_time = time.time() - request_time
        print(f"ROUTER /ask/ - GOT RESPONSE in {response_time:.2f} seconds")
        print(f"Answer length: {len(answer)} characters")
        answer_sample = answer[:200] + "..." if len(answer) > 200 else answer
        print(f"Answer sample: '{answer_sample}'")
        
        # Create the response
        response = QuestionResponse(
            question=request.question,
            answer=answer,
            document_ids=actual_doc_ids,
            model=request.model
        )
        
        print(f"ROUTER /ask/ - RETURNING RESPONSE")
        print(f"{'#'*100}")
        return response
    except Exception as e:
        error_type = type(e).__name__
        print(f"ROUTER /ask/ - ERROR ({error_type}): {str(e)}")
        print(f"ROUTER /ask/ - ERROR TRACEBACK:")
        print(traceback.format_exc())
        print(f"{'#'*100}")
        raise HTTPException(status_code=500, detail=f"Error processing question: {str(e)}")

# Explicit route handler for the exact /ask endpoint
@router.post("", response_model=QuestionResponse)
async def ask_question_root(request: QuestionRequest):
    """
    Ask a question at the root of the router (/ask instead of /ask/)
    """
    print(f"\n{'$'*100}")
    print(f"ROUTER /ask (ROOT) - REQUEST RECEIVED")
    print(f"Request object fields: {request.dict()}")
    print(f"This handler specifically targets the /ask URL without trailing slash")
    print(f"{'$'*100}")
    # Route to the main handler
    return await ask_question(request)

@router.post("/questions")
async def ask_question_specific(
    request: QuestionRequest,
    document_service: DocumentService = Depends(get_document_service)
):
    """Ask a question about documents"""
    try:
        print(f"\n{'%'*100}")
        print(f"ROUTER /ask/questions - REQUEST RECEIVED:")
        print(f"Question: '{request.question}'")
        print(f"Model: '{request.model}'")
        print(f"Folder: '{request.folder}'")
        print(f"Doc IDs: {request.doc_ids}")
        print(f"{'%'*100}")
        
        # Get the answer
        result = document_service.ask_question(
            question=request.question,
            doc_ids=request.doc_ids,
            folder=request.folder,
            model=request.model  # Pass the model parameter
        )
        
        print(f"ROUTER /ask/questions - RETURNING RESPONSE")
        print(f"{'%'*100}")
        
        return result
    except Exception as e:
        print(f"Error asking question: {str(e)}")
        import traceback
        print(f"ROUTER /ask/questions - ERROR TRACEBACK:\n{traceback.format_exc()}")
        print(f"{'%'*100}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/questions/across-namespaces")
async def ask_question_across_namespaces(
    request: QuestionRequest,
    document_service: DocumentService = Depends(get_document_service)
):
    """Ask a question across all namespaces"""
    try:
        # Get the answer
        result = document_service.ask_question_across_namespaces(
            question=request.question,
            doc_ids=request.doc_ids
        )
        
        return result
    except Exception as e:
        print(f"Error asking question across namespaces: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e)) 