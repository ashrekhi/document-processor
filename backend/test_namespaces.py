import os
from dotenv import load_dotenv
from app.services.s3_service import S3Service
from app.services.document_service import DocumentService
from app.services.vector_db_service import VectorDBService

# Load environment variables
load_dotenv()

def test_namespaces():
    """Test namespace functionality"""
    try:
        # Initialize services
        s3_service = S3Service()
        document_service = DocumentService(s3_service)
        vector_db_service = VectorDBService()
        
        # List all namespaces
        print("Listing all namespaces...")
        namespaces = vector_db_service.list_namespaces()
        print(f"Available namespaces: {namespaces}")
        
        # For each namespace, list documents
        for namespace in namespaces:
            print(f"\nListing documents in namespace '{namespace}'...")
            documents = document_service.get_documents_by_namespace(namespace)
            print(f"Found {len(documents)} documents in namespace '{namespace}':")
            for doc in documents:
                print(f"  - {doc.get('filename')} (ID: {doc.get('id')})")
        
        # Test search in a specific namespace
        if namespaces:
            test_namespace = namespaces[0]
            print(f"\nTesting search in namespace '{test_namespace}'...")
            
            # Get a document in this namespace
            documents = document_service.get_documents_by_namespace(test_namespace)
            if documents:
                test_doc_id = documents[0].get('id')
                print(f"Using document ID: {test_doc_id}")
                
                # Test search
                print("Searching for 'test'...")
                results = vector_db_service.search_similar_chunks(
                    query="test",
                    top_k=3,
                    filter_doc_ids=[test_doc_id],
                    namespace=test_namespace
                )
                
                print(f"Found {len(results)} results:")
                for result in results:
                    print(f"  - Score: {result.get('score')}, Text: {result.get('text')[:50]}...")
            else:
                print(f"No documents found in namespace '{test_namespace}'")
        
        # Test search across all namespaces
        print("\nTesting search across all namespaces...")
        results = vector_db_service.search_across_namespaces(
            query="test",
            top_k=5
        )
        
        print(f"Found {len(results)} results across all namespaces:")
        for result in results:
            print(f"  - Namespace: {result.get('namespace')}, Score: {result.get('score')}, Text: {result.get('text')[:50]}...")
        
        print("\nNamespace test completed successfully!")
    except Exception as e:
        print(f"Error testing namespaces: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_namespaces() 