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
    doc_ids: Optional[List[str]] = None
    folder: Optional[str] = None
    model: Optional[str] = "gpt-4"
    document_ids: Optional[List[str]] = None  # For backward compatibility

class QuestionResponse(BaseModel):
    question: str
    answer: str
    document_ids: Optional[List[str]] = None
    model: Optional[str] = "gpt-4"

class FolderInfo(BaseModel):
    name: str
    s3_url: str 