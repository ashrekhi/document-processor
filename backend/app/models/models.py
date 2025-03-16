from pydantic import BaseModel
from typing import List, Optional, Dict

class DocumentResponse(BaseModel):
    id: str
    filename: str
    source: str
    description: Optional[str] = None
    s3_url: str

class QuestionRequest(BaseModel):
    question: str
    document_ids: List[str]
    model: Optional[str] = "gpt-3.5-turbo"

class QuestionResponse(BaseModel):
    question: str
    answer: str
    document_ids: List[str]
    model: Optional[str] = "gpt-3.5-turbo"

class FolderInfo(BaseModel):
    master_bucket: str
    folders: List[str] 