import os
from dotenv import load_dotenv
import sys
import time

# Load environment variables
load_dotenv()

# Import the DocumentService class
from app.services.s3_service import S3Service
from app.services.document_service import DocumentService

def test_ask_question():
    """Test the ask_question method with logging"""
    print("\n===== TESTING ASK_QUESTION WITH LOGGING =====")
    
    # Initialize services
    s3_service = S3Service()
    document_service = DocumentService(s3_service)
    
    # Define a test question
    question = "What is the meaning of life according to the documents?"
    
    try:
        # Get all documents to find some doc_ids for testing
        print("\nListing all documents...")
        documents = document_service.list_documents()
        
        if not documents:
            print("No documents found. Please upload a document first.")
            return
        
        # Use the first document for testing
        doc_id = documents[0]["id"]
        folder = documents[0]["folder"]
        filename = documents[0]["filename"]
        
        print(f"\nFound document: {filename} (ID: {doc_id}, Folder: {folder})")
        
        # Test ask_question with a specific document
        print("\n===== Testing question with specific document =====")
        print(f"Asking question: '{question}'")
        print(f"Using document ID: {doc_id}")
        
        result = document_service.ask_question(
            question=question,
            doc_ids=[doc_id]
        )
        
        # Print the result
        print("\nResult:")
        print(f"Answer: {result['answer']}")
        print(f"Sources: {len(result['sources'])}")
        
        # Test ask_question with a specific folder
        if folder:
            print("\n===== Testing question with specific folder =====")
            print(f"Asking question: '{question}'")
            print(f"Using folder: {folder}")
            
            result = document_service.ask_question(
                question=question,
                folder=folder
            )
            
            # Print the result
            print("\nResult:")
            print(f"Answer: {result['answer']}")
            print(f"Sources: {len(result['sources'])}")
        
        # Test ask_question_across_namespaces
        print("\n===== Testing question across namespaces =====")
        print(f"Asking question: '{question}'")
        
        result = document_service.ask_question_across_namespaces(
            question=question
        )
        
        # Print the result
        print("\nResult:")
        print(f"Answer: {result['answer']}")
        print(f"Sources: {len(result['sources'])}")
        
        print("\n===== TESTING COMPLETED SUCCESSFULLY =====")
        
    except Exception as e:
        print(f"Error testing ask_question: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_ask_question() 