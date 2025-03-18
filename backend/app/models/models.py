from pydantic import BaseModel
from typing import List, Optional

class DocumentResponse(BaseModel):
    id: str
    filename: str
    source: str
    description: Optional[str] = None
    s3_url: Optional[str] = None
    folder: Optional[str] = None
    created_at: Optional[str] = None

class QuestionRequest(BaseModel):
    question: str
    folder: str  # Now required
    model: Optional[str] = "gpt-4"
    doc_ids: Optional[List[str]] = None  # Kept for backward compatibility but deprecated
    document_ids: Optional[List[str]] = None  # Kept for backward compatibility but deprecated

class QuestionResponse(BaseModel):
    question: str
    answer: str
    document_ids: Optional[List[str]] = None
    model: Optional[str] = "gpt-4"

class FolderInfo(BaseModel):
    name: str
    s3_url: str 