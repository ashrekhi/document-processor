from pydantic import BaseModel
from typing import List, Dict, Any, Optional
from datetime import datetime

class SessionCreate(BaseModel):
    name: str
    description: Optional[str] = None
    similarity_threshold: Optional[float] = 0.7  # Default similarity threshold for auto-grouping

class SessionUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    similarity_threshold: Optional[float] = None
    active: Optional[bool] = None

class SessionResponse(BaseModel):
    id: str
    name: str
    description: Optional[str] = None
    similarity_threshold: float = 0.7
    created_at: str
    updated_at: Optional[str] = None
    active: bool = True
    folder_path: str
    document_count: int
    folder_count: int
    
class SessionDocumentAssociation(BaseModel):
    session_id: str
    document_id: str
    folder: str
    document_name: str
    similarity_score: Optional[float] = None
