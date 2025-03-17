import os
import inspect
from dotenv import load_dotenv
from app.services.s3_service import S3Service
from app.services.document_service import DocumentService

# Load environment variables
load_dotenv()

def debug_document_service():
    """Debug the DocumentService class"""
    try:
        print("Debugging DocumentService...")
        
        # Initialize services
        s3_service = S3Service()
        document_service = DocumentService(s3_service)
        
        # Print the signature of the process_document method
        print(f"process_document signature: {inspect.signature(document_service.process_document)}")
        
        # Print the source code of the process_document method
        print(f"process_document source code:")
        print(inspect.getsource(document_service.process_document))
        
        # Print all methods in the DocumentService class
        print(f"All methods in DocumentService:")
        for name, method in inspect.getmembers(document_service, predicate=inspect.ismethod):
            print(f"  {name}: {inspect.signature(method)}")
        
        print("DocumentService debug complete!")
    except Exception as e:
        print(f"Error debugging DocumentService: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    debug_document_service() 