import os
from dotenv import load_dotenv
from pinecone import Pinecone
import json

# Load environment variables
load_dotenv()

# Get Pinecone credentials
api_key = os.getenv('PINECONE_API_KEY')
cloud = os.getenv('PINECONE_CLOUD', 'aws')
region = os.getenv('PINECONE_REGION', 'us-east-1')

print("Checking Pinecone account status...")
print(f"Cloud: {cloud}")
print(f"Region: {region}")

try:
    # Initialize Pinecone
    pc = Pinecone(api_key=api_key, cloud=cloud)
    
    # List available indexes
    indexes = pc.list_indexes()
    print(f"Available indexes: {json.dumps(indexes, indent=2)}")
    
    # Get detailed information about each index
    for index_info in indexes.get('indexes', []):
        index_name = index_info.get('name')
        if index_name:
            index = pc.Index(index_name)
            stats = index.describe_index_stats()
            print(f"\nIndex '{index_name}' stats:")
            print(f"  - Vector count: {stats.get('total_vector_count', 0)}")
            print(f"  - Dimension: {stats.get('dimension', 'unknown')}")
            print(f"  - Namespaces: {list(stats.get('namespaces', {}).keys())}")
except Exception as e:
    print(f"Error checking Pinecone account: {str(e)}")

def check_pinecone_account():
    # Get Pinecone credentials from environment
    api_key = os.getenv('PINECONE_API_KEY')
    cloud = os.getenv('PINECONE_CLOUD', 'aws')
    region = os.getenv('PINECONE_REGION', 'us-east-1')
    
    if not api_key:
        print("ERROR: PINECONE_API_KEY not set in environment variables")
        return False
    
    print(f"Checking Pinecone account with API key: {api_key[:5]}...{api_key[-5:]} (length: {len(api_key)})")
    
    try:
        # Initialize Pinecone
        print("Initializing Pinecone...")
        pc = Pinecone(api_key=api_key, cloud=cloud)
        
        # List indexes with detailed error handling
        print("\nListing indexes...")
        try:
            indexes_response = pc.list_indexes()
            available_indexes = [idx['name'] for idx in indexes_response.get('indexes', [])]
            print(f"Available indexes: {available_indexes}")
            
            if not available_indexes:
                print("\nWarning: No indexes found. This could be because:")
                print("1. You haven't created any indexes yet")
                print("2. You're using a different cloud/region than where your indexes are located")
                print("3. Your API key doesn't have access to the indexes")
                
                print("\nSuggestions:")
                print("1. Create an index using the Pinecone console or the create_pinecone_index.py script")
                print("2. Verify your PINECONE_CLOUD and PINECONE_REGION environment variables")
                print("3. Check that your API key is valid and has correct permissions")
        except Exception as list_error:
            print(f"Error listing indexes: {str(list_error)}")
            return False
        
        # Get account quota information (if available)
        print("\nAccount Information:")
        for index_info in indexes_response.get('indexes', []):
            index_name = index_info.get('name')
            if index_name:
                index = pc.Index(index_name)
                stats = index.describe_index_stats()
                print(f"\nIndex '{index_name}' stats:")
                print(f"  - Vector count: {stats.get('total_vector_count', 0)}")
                print(f"  - Dimension: {stats.get('dimension', 'unknown')}")
                print(f"  - Namespaces: {list(stats.get('namespaces', {}).keys())}")
        
        print("\nPinecone account check successful!")
        return True
    except Exception as e:
        print(f"Error checking Pinecone account: {str(e)}")
        return False

if __name__ == "__main__":
    check_pinecone_account() 