import os
from dotenv import load_dotenv
from pinecone import Pinecone, ServerlessSpec
import time

# Load environment variables
load_dotenv()

def create_pinecone_index():
    # Get Pinecone credentials
    api_key = os.getenv('PINECONE_API_KEY')
    index_name = os.getenv('PINECONE_INDEX', 'radiant-documents')
    cloud = os.getenv('PINECONE_CLOUD', 'aws')
    region = os.getenv('PINECONE_REGION', 'us-east-1')
    
    if not api_key:
        print("ERROR: PINECONE_API_KEY not set in environment variables")
        return False
    
    try:
        # Initialize Pinecone
        print(f"Initializing Pinecone with cloud: {cloud} and region: {region}")
        pc = Pinecone(api_key=api_key, cloud=cloud)
        
        # List existing indexes
        indexes = pc.list_indexes()
        print(f"Existing indexes: {indexes}")
        
        # Check if index already exists
        if index_name in indexes:
            print(f"Index '{index_name}' already exists")
            return True
        
        # Create the index
        print(f"Creating index '{index_name}'...")
        pc.create_index(
            name=index_name,
            dimension=1536,  # OpenAI ada-002 embedding dimension
            metric="cosine",
            spec=ServerlessSpec(
                cloud=cloud,
                region=region
            )
        )
        
        # Wait for the index to be ready
        print("Waiting for index to be ready...")
        time.sleep(10)  # Give it some time to initialize
        
        # Verify the index was created
        indexes = pc.list_indexes()
        if index_name in indexes:
            print(f"Index '{index_name}' created successfully!")
            
            # Connect to the index
            index = pc.Index(index_name)
            
            # Get index stats
            stats = index.describe_index_stats()
            print(f"Index stats: {stats}")
            
            return True
        else:
            print(f"Failed to create index '{index_name}'")
            return False
    except Exception as e:
        print(f"Error creating Pinecone index: {str(e)}")
        return False

if __name__ == "__main__":
    create_pinecone_index() 