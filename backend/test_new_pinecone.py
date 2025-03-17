import os
from dotenv import load_dotenv
from pinecone import Pinecone

# Load environment variables
load_dotenv()

def test_new_pinecone_client():
    # Get Pinecone credentials from environment
    api_key = os.getenv('PINECONE_API_KEY')
    index_name = os.getenv('PINECONE_INDEX', 'radiant-documents')
    
    if not api_key:
        print("ERROR: PINECONE_API_KEY not set in environment variables")
        return False
    
    print(f"Testing Pinecone connection with new client:")
    print(f"  API Key: {api_key[:5]}...{api_key[-5:]} (length: {len(api_key)})")
    print(f"  Index Name: {index_name}")
    
    try:
        # Initialize Pinecone with the new client
        print("Initializing Pinecone...")
        pc = Pinecone(api_key=api_key)
        
        # List indexes
        print("Listing indexes...")
        indexes = pc.list_indexes()
        print(f"Available indexes: {indexes}")
        
        # Check if our index exists
        index_names = [index.name for index in indexes]
        if index_name in index_names:
            print(f"Index '{index_name}' exists")
            
            # Connect to the index
            print(f"Connecting to index '{index_name}'...")
            index = pc.Index(index_name)
            
            # Get index stats
            print("Getting index stats...")
            stats = index.describe_index_stats()
            print(f"Index stats: {stats}")
            
            # Test upsert
            print("Testing upsert operation...")
            test_vector = {
                "id": "test_vector",
                "values": [0.1] * 1536,  # Match your embedding dimension
                "metadata": {"test": "data"}
            }
            
            result = index.upsert(vectors=[test_vector])
            print(f"Upsert result: {result}")
            
            # Test query
            print("Testing query operation...")
            query_result = index.query(
                vector=[0.1] * 1536,
                top_k=1,
                include_metadata=True
            )
            print(f"Query result: {query_result}")
            
            # Clean up test vector
            print("Cleaning up test vector...")
            index.delete(ids=["test_vector"])
            
            print("Pinecone connection test successful!")
            return True
        else:
            print(f"Index '{index_name}' does not exist")
            print("Please create the index in the Pinecone console.")
            return False
    except Exception as e:
        print(f"Error connecting to Pinecone: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    test_new_pinecone_client() 