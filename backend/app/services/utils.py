from app.services.s3_service import S3Service
from app.services.document_service import DocumentService

def get_document_service():
    """
    Dependency function to get a DocumentService instance.
    This can be used with FastAPI's Depends() to inject a DocumentService.
    """
    s3_service = S3Service()
    return DocumentService(s3_service) 