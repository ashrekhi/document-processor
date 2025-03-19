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

print("Testing Pinecone connection...")
print(f"Using index: {index_name}")
print(f"Cloud: {cloud}")
print(f"Region: {region}")

try:
    # Initialize Pinecone
    pc = Pinecone(api_key=api_key, cloud=cloud)
    
    # List available indexes
    indexes = pc.list_indexes()
    print(f"Available indexes: {indexes}")
    
    # Connect to the index
    index = pc.Index(index_name)
    print(f"Successfully connected to index: {index_name}")
    
    # Get index stats
    stats = index.describe_index_stats()
    print(f"Index stats: {stats}")
except Exception as e:
    print(f"Error testing Pinecone: {str(e)}")

if __name__ == "__main__":
    test_pinecone_connection() 