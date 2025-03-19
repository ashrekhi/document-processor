import os
from dotenv import load_dotenv
from pinecone import Pinecone
import json
import traceback

# Load environment variables
load_dotenv()

# Get Pinecone credentials
api_key = os.getenv('PINECONE_API_KEY')
index_name = os.getenv('PINECONE_INDEX', 'radiant-documents')
cloud = os.getenv('PINECONE_CLOUD', 'aws')
region = os.getenv('PINECONE_REGION', 'us-east-1')

print("Running detailed Pinecone test...")
print(f"Using index: {index_name}")
print(f"Cloud: {cloud}")
print(f"Region: {region}")

try:
    # Initialize Pinecone
    pc = Pinecone(api_key=api_key, cloud=cloud)
    print("Successfully initialized Pinecone client")
    
    # List available indexes
    print("\nListing indexes...")
    indexes = pc.list_indexes()
    print(f"Available indexes: {json.dumps(indexes, indent=2)}")
    
    if index_name:
        # Connect to the index
        print(f"\nConnecting to index '{index_name}'...")
        index = pc.Index(index_name)
        print("Successfully connected to index")
        
        # Get index stats
        print("\nGetting index stats...")
        stats = index.describe_index_stats()
        print(f"Index stats: {json.dumps(stats, indent=2)}")
        
        # Test vector operations if the index exists
        print("\nTesting vector operations...")
        test_vector = [0.1] * 1536  # OpenAI ada-002 dimension
        test_metadata = {"test": "metadata"}
        
        # Upsert test
        print("Testing upsert...")
        upsert_response = index.upsert(
            vectors=[{
                "id": "test_vector",
                "values": test_vector,
                "metadata": test_metadata
            }],
            namespace="test"
        )
        print(f"Upsert response: {json.dumps(upsert_response, indent=2)}")
        
        # Query test
        print("\nTesting query...")
        query_response = index.query(
            vector=test_vector,
            top_k=1,
            namespace="test",
            include_metadata=True
        )
        print(f"Query response: {json.dumps(query_response.to_dict(), indent=2)}")
        
        # Cleanup
        print("\nCleaning up test data...")
        delete_response = index.delete(
            filter={"test": "metadata"},
            namespace="test"
        )
        print(f"Delete response: {json.dumps(delete_response, indent=2)}")
    
    print("\nPinecone test completed successfully!")
except Exception as e:
    print(f"Error during Pinecone test: {str(e)}")
    print("Full error details:")
    traceback.print_exc()

if __name__ == "__main__":
    test_pinecone_connection_detailed() 