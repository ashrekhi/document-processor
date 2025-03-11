from pydantic import BaseModel
from typing import List, Optional

class DocumentResponse(BaseModel):
    id: str
    filename: str
    source: str
    description: Optional[str] = None
    s3_url: str

class QuestionRequest(BaseModel):
    question: str
    document_ids: List[str]

class QuestionResponse(BaseModel):
    question: str
    answer: str
    document_ids: List[str] 