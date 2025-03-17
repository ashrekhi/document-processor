import os
import pinecone
from dotenv import load_dotenv
import traceback

# Load environment variables
load_dotenv()

def test_pinecone_connection_detailed():
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
        
        # List indexes with detailed error handling
        print("Listing indexes...")
        try:
            indexes = pinecone.list_indexes()
            print(f"Available indexes: {indexes}")
        except Exception as list_error:
            print(f"Error listing indexes: {str(list_error)}")
            print("Detailed error:")
            traceback.print_exc()
            return False
        
        # Try to create the index with detailed error handling
        if index_name not in indexes:
            print(f"Index '{index_name}' does not exist. Attempting to create it...")
            try:
                pinecone.create_index(
                    name=index_name,
                    dimension=1536,
                    metric="cosine"
                )
                print(f"Successfully created index: {index_name}")
            except Exception as create_error:
                print(f"Error creating index: {str(create_error)}")
                print("Detailed error:")
                traceback.print_exc()
                return False
        
        # Connect to the index with detailed error handling
        print(f"Connecting to index '{index_name}'...")
        try:
            index = pinecone.Index(index_name)
        except Exception as connect_error:
            print(f"Error connecting to index: {str(connect_error)}")
            print("Detailed error:")
            traceback.print_exc()
            return False
        
        # Get index stats with detailed error handling
        print("Getting index stats...")
        try:
            stats = index.describe_index_stats()
            print(f"Index stats: {stats}")
        except Exception as stats_error:
            print(f"Error getting index stats: {str(stats_error)}")
            print("Detailed error:")
            traceback.print_exc()
            return False
        
        print("Pinecone connection test successful!")
        return True
    except Exception as e:
        print(f"Error in Pinecone connection test: {str(e)}")
        print("Detailed error:")
        traceback.print_exc()
        return False

if __name__ == "__main__":
    test_pinecone_connection_detailed() 