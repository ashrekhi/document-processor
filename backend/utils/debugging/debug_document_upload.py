import os
import json
import uuid
from dotenv import load_dotenv
import sys
import traceback
from app.services.s3_service import S3Service
from app.services.vector_db_service import VectorDBService
from datetime import datetime
from app.services.document_service import DocumentService

# Load environment variables
load_dotenv()

def debug_document_upload(filename, content_path):
    """Debug the document upload process"""
    try:
        print(f"Debugging document upload for {filename}")
        
        # Initialize services
        s3_service = S3Service()
        document_service = DocumentService(s3_service)
        
        # Read the file content
        with open(content_path, 'rb') as f:
            content = f.read()
        print(f"Read {len(content)} bytes from file")
        
        # Process the document
        print(f"Calling document_service.process_document for {filename}")
        doc_id = document_service.process_document(filename, content, "root")
        print(f"Document processed successfully with ID: {doc_id}")
        
        print(f"Document upload debug complete. Document ID: {doc_id}")
        return doc_id
    except Exception as e:
        print(f"Error in debug document upload: {str(e)}")
        traceback.print_exc()
        return None

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: python debug_document_upload.py <filename> <content_path>")
        sys.exit(1)
    
    filename = sys.argv[1]
    content_path = sys.argv[2]
    debug_document_upload(filename, content_path) 