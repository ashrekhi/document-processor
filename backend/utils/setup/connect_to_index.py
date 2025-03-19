import os
from dotenv import load_dotenv
from pinecone import Pinecone

# Load environment variables
load_dotenv()

# Get Pinecone credentials
api_key = os.getenv('PINECONE_API_KEY')
index_name = os.getenv('PINECONE_INDEX', 'radiant-documents')
cloud = os.getenv('PINECONE_CLOUD', 'aws')
region = os.getenv('PINECONE_REGION', 'us-east-1')

try:
    # Initialize Pinecone
    print(f"Initializing Pinecone with cloud: {cloud}, region: {region}")
    pc = Pinecone(api_key=api_key, cloud=cloud)
    
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
    index_name = os.getenv('PINECONE_INDEX', 'radiant-documents')
    cloud = os.getenv('PINECONE_CLOUD', 'aws')
    region = os.getenv('PINECONE_REGION', 'us-east-1')
    
    if not api_key:
        print("ERROR: PINECONE_API_KEY not set in environment variables")
        return False
    
    print(f"Connecting to Pinecone with:")
    print(f"  API Key: {api_key[:5]}...{api_key[-5:]} (length: {len(api_key)})")
    print(f"  Cloud: {cloud}")
    print(f"  Region: {region}")
    print(f"  Index Name: {index_name}")
    
    try:
        # Initialize Pinecone
        print("Initializing Pinecone...")
        pc = Pinecone(api_key=api_key, cloud=cloud)
        
        # List indexes
        print("Listing indexes...")
        indexes_response = pc.list_indexes()
        available_indexes = [idx['name'] for idx in indexes_response.get('indexes', [])]
        print(f"Available indexes: {available_indexes}")
        
        # Check if our index exists
        if index_name in available_indexes:
            print(f"Index '{index_name}' exists")
            
            # Connect to the index
            print(f"Connecting to index '{index_name}'...")
            index = pc.Index(index_name)
            
            # Get index stats
            print("Getting index stats...")
            stats = index.describe_index_stats()
            print(f"Index stats: {stats}")
            
            print("Pinecone connection test successful!")
            return True
        else:
            print(f"Index '{index_name}' does not exist")
            print("Please create the index in the Pinecone console or use the create_pinecone_index.py script.")
            return False
    except Exception as e:
        print(f"Error connecting to Pinecone: {str(e)}")
        return False

if __name__ == "__main__":
    connect_to_index() 