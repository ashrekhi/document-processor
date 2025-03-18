import os
import pinecone
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def test_pinecone_connection():
    # Get Pinecone credentials from environment
    api_key = os.getenv('PINECONE_API_KEY')
    environment = os.getenv('PINECONE_ENVIRONMENT', 'us-east-1-aws')
    index_name = os.getenv('PINECONE_INDEX', 'radiant-documents')
    
    if not api_key:
        print("ERROR: PINECONE_API_KEY not set in environment variables")
        return False
    
    print(f"Testing Pinecone connection with:")
    print(f"  API Key: {api_key[:5]}...{api_key[-5:]} (length: {len(api_key)})")
    print(f"  Environment: {environment}")
    print(f"  Index Name: {index_name}")
    
    try:
        # Initialize Pinecone
        print("Initializing Pinecone...")
        pinecone.init(api_key=api_key, environment=environment)
        
        # List indexes
        print("Listing indexes...")
        indexes = pinecone.list_indexes()
        print(f"Available indexes: {indexes}")
        
        # Check if our index exists
        if index_name in indexes:
            print(f"Index '{index_name}' exists")
            
            # Connect to the index
            print(f"Connecting to index '{index_name}'...")
            index = pinecone.Index(index_name)
            
            # Get index stats
            print("Getting index stats...")
            stats = index.describe_index_stats()
            print(f"Index stats: {stats}")
            
            print("Pinecone connection test successful!")
            return True
        else:
            print(f"Index '{index_name}' does not exist")
            print("Please create the index in the Pinecone console.")
            return False
    except Exception as e:
        print(f"Error connecting to Pinecone: {str(e)}")
        return False

if __name__ == "__main__":
    test_pinecone_connection() 