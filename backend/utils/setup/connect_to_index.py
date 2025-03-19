import os
from dotenv import load_dotenv
from pinecone import Pinecone
import traceback

# Load environment variables
load_dotenv()

# Get Pinecone credentials
api_key = os.getenv('PINECONE_API_KEY')
index_name = os.getenv('PINECONE_INDEX', 'radiant-documents')
cloud = os.getenv('PINECONE_CLOUD', 'aws')
region = os.getenv('PINECONE_REGION', 'us-east-1')

# Initialize Pinecone
pc = Pinecone(api_key=api_key, cloud=cloud)

try:
    # Connect to the index
    index = pc.Index(index_name)
    print(f"Successfully connected to index: {index_name}")
    
    # Get index stats
    stats = index.describe_index_stats()
    print(f"Index stats: {stats}")
except Exception as e:
    print(f"Error connecting to index: {str(e)}")

def connect_to_index():
    # Get Pinecone credentials from environment
    api_key = os.getenv('PINECONE_API_KEY')
    environment = os.getenv('PINECONE_ENVIRONMENT', 'us-east-1-aws')
    index_name = os.getenv('PINECONE_INDEX', 'radiant-documents')
    
    if not api_key:
        print("ERROR: PINECONE_API_KEY not set in environment variables")
        return False
    
    print(f"Attempting to connect to Pinecone index:")
    print(f"  API Key: {api_key[:5]}...{api_key[-5:]} (length: {len(api_key)})")
    print(f"  Environment: {environment}")
    print(f"  Index Name: {index_name}")
    
    try:
        # Initialize Pinecone
        print("Initializing Pinecone...")
        pinecone.init(api_key=api_key, environment=environment)
        
        # Try to connect directly to the index
        print(f"Connecting to index '{index_name}'...")
        try:
            index = pinecone.Index(index_name)
            
            # Get index stats
            print("Getting index stats...")
            stats = index.describe_index_stats()
            print(f"Index stats: {stats}")
            
            print("Successfully connected to the index!")
            return True
        except Exception as connect_error:
            print(f"Error connecting to index: {str(connect_error)}")
            print("Detailed error:")
            traceback.print_exc()
            
            # Try to list all indexes to see what's available
            print("\nListing all available indexes...")
            try:
                indexes = pinecone.list_indexes()
                print(f"Available indexes: {indexes}")
                
                if not indexes:
                    print("\nNo indexes found. This could be because:")
                    print("1. You haven't created any indexes yet")
                    print("2. You're using a different environment than where your indexes are located")
                    print("3. Your API key doesn't have access to the indexes")
                    print("4. Your Pinecone account has limitations on index creation")
                    
                    print("\nSuggestions:")
                    print("1. Check the Pinecone console to verify the index exists")
                    print("2. Make sure you're using the correct API key and environment")
                    print("3. If you're on a free tier, you might have limitations on index creation")
                    print("4. Consider using a mock vector database for development")
            except Exception as list_error:
                print(f"Error listing indexes: {str(list_error)}")
            
            return False
    except Exception as e:
        print(f"Error in Pinecone connection: {str(e)}")
        print("Detailed error:")
        traceback.print_exc()
        return False

if __name__ == "__main__":
    connect_to_index() 