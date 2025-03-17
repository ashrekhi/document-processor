from fastapi import APIRouter, HTTPException, Depends
from app.models.models import QuestionRequest, QuestionResponse
from app.services.rag_service import RAGService
from app.services.document_service import DocumentService
from app.services.utils import get_document_service

router = APIRouter()

# Initialize RAG service
rag_service = RAGService()

@router.post("/", response_model=QuestionResponse)
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

@router.post("/questions")
async def ask_question(
    request: QuestionRequest,
    document_service: DocumentService = Depends(get_document_service)
):
    """Ask a question about documents"""
    try:
        # Get the answer
        result = document_service.ask_question(
            question=request.question,
            doc_ids=request.doc_ids,
            folder=request.folder
        )
        
        return result
    except Exception as e:
        print(f"Error asking question: {str(e)}")
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