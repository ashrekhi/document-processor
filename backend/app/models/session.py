from pydantic import BaseModel
from typing import List, Dict, Any, Optional
from datetime import datetime

class SessionCreate(BaseModel):
    name: str
    description: Optional[str] = None
    similarity_threshold: Optional[float] = 0.7  # Default similarity threshold for auto-grouping
    custom_prompt: Optional[str] = None  # Optional prompt for document text preprocessing
    prompt_model: Optional[str] = "gpt-3.5-turbo"  # Model to use for prompt processing

class SessionUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    similarity_threshold: Optional[float] = None
    active: Optional[bool] = None
    custom_prompt: Optional[str] = None  # Optional prompt for document text preprocessing
    prompt_model: Optional[str] = None  # Model to use for prompt processing

class SessionResponse(BaseModel):
    id: str
    name: str
    description: Optional[str] = None
    similarity_threshold: float = 0.7
    custom_prompt: Optional[str] = None  # Optional prompt for document text preprocessing
    prompt_model: Optional[str] = "gpt-3.5-turbo"  # Model to use for prompt processing
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
