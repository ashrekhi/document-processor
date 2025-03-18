import os
from dotenv import load_dotenv
from app.services.s3_service import S3Service
from app.services.document_service import DocumentService
import sys

# Load environment variables
load_dotenv()

def test_document_upload(filename, content_path):
    """Test document upload"""
    try:
        print(f"Testing document upload for {filename}")
        
        # Initialize services
        s3_service = S3Service()
        document_service = DocumentService(s3_service)
        
        # Read the file content
        with open(content_path, 'rb') as f:
            content = f.read()
        print(f"Read {len(content)} bytes from file")
        
        # Process the document
        print(f"Calling document_service.process_document for {filename}")
        # Print the signature of the method
        import inspect
        print(f"Method signature: {inspect.signature(document_service.process_document)}")
        
        # Call the method with the correct parameters
        doc_id = document_service.process_document(filename, content, "root")
        print(f"Document processed successfully with ID: {doc_id}")
        
        return doc_id
    except Exception as e:
        print(f"Error in test document upload: {str(e)}")
        import traceback
        traceback.print_exc()
        return None

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: python test_document_upload.py <filename> <content_path>")
        sys.exit(1)
    
    filename = sys.argv[1]
    content_path = sys.argv[2]
    test_document_upload(filename, content_path) 