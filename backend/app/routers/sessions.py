from fastapi import APIRouter, File, Form, UploadFile, Depends, HTTPException, Body
import uuid
from typing import List, Dict, Any, Optional
from pydantic import BaseModel

from app.services.document_service import DocumentService
from app.services.s3_service import S3Service
from app.services.session_service import SessionService
from app.services.utils import get_document_service
from app.models.session import SessionCreate, SessionUpdate, SessionResponse

router = APIRouter()

def get_session_service():
    # Create and return a session service
    s3_service = S3Service()
    return SessionService(s3_service)

@router.post("/", response_model=SessionResponse)
async def create_session(
    session_data: SessionCreate,
    session_service: SessionService = Depends(get_session_service)
):
    """Create a new document processing session"""
    try:
        session = session_service.create_session(
            name=session_data.name,
            description=session_data.description,
            similarity_threshold=session_data.similarity_threshold or 0.7,
            custom_prompt=session_data.custom_prompt,
            prompt_model=session_data.prompt_model
        )
        return session
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/", response_model=List[SessionResponse])
async def list_sessions(
    session_service: SessionService = Depends(get_session_service)
):
    """List all available sessions"""
    try:
        sessions = session_service.list_sessions()
        return sessions
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{session_id}", response_model=SessionResponse)
async def get_session(
    session_id: str,
    session_service: SessionService = Depends(get_session_service)
):
    """Get a session by ID"""
    try:
        session = session_service.get_session(session_id)
        return session
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.put("/{session_id}", response_model=SessionResponse)
async def update_session(
    session_id: str,
    session_data: SessionUpdate,
    session_service: SessionService = Depends(get_session_service)
):
    """Update a session"""
    try:
        session = session_service.update_session(
            session_id=session_id,
            name=session_data.name,
            description=session_data.description,
            similarity_threshold=session_data.similarity_threshold,
            active=session_data.active,
            custom_prompt=session_data.custom_prompt,
            prompt_model=session_data.prompt_model
        )
        return session
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/{session_id}")
async def delete_session(
    session_id: str,
    session_service: SessionService = Depends(get_session_service)
):
    """Delete a session and all its contents"""
    try:
        success = session_service.delete_session(session_id)
        if success:
            return {"message": f"Session {session_id} deleted successfully"}
        else:
            raise HTTPException(status_code=500, detail="Failed to delete session")
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/{session_id}/documents")
async def upload_document_to_session(
    session_id: str,
    file: UploadFile = File(...),
    session_service: SessionService = Depends(get_session_service)
):
    """Upload a document to a session with automatic folder organization"""
    try:
        # Read the file content
        content = await file.read()
        
        # Check file size
        max_size = 10 * 1024 * 1024  # 10 MB
        if len(content) > max_size:
            raise HTTPException(status_code=400, detail="File too large (max 10 MB)")
        
        # Process the document in the session
        document = session_service.process_document_in_session(
            session_id=session_id,
            filename=file.filename,
            content=content
        )
        
        return {
            "message": "Document uploaded and organized successfully",
            "document_id": document["id"],
            "folder": document["folder"],
            "session_id": session_id,
            "similarity_logs": document.get("similarity_logs", {})
        }
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{session_id}/documents")
async def get_session_documents(
    session_id: str,
    session_service: SessionService = Depends(get_session_service)
):
    """Get all documents in a session"""
    try:
        documents = session_service.get_session_documents(session_id)
        return {"documents": documents}
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{session_id}/folders")
async def get_session_folders(
    session_id: str,
    session_service: SessionService = Depends(get_session_service)
):
    """Get folders and their statistics in a session"""
    try:
        folder_stats = session_service.get_session_folder_stats(session_id)
        return {"folders": folder_stats}
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
