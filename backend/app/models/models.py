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
    folder: str  # Required
    model: Optional[str] = "gpt-4"

class QuestionResponse(BaseModel):
    question: str
    answer: str
    model: Optional[str] = "gpt-4"

class FolderInfo(BaseModel):
    name: str
    s3_url: str 