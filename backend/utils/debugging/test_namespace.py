import os
from dotenv import load_dotenv
from pinecone import Pinecone

# Load environment variables from .env file
load_dotenv()

print(f"Starting namespace test with updated config...")

# Get Pinecone credentials
api_key = os.getenv('PINECONE_API_KEY')
cloud = os.getenv('PINECONE_CLOUD')
region = os.getenv('PINECONE_REGION')
index_name = os.getenv('PINECONE_INDEX')

print(f"Pinecone API Key: {api_key[:8]}...{api_key[-5:]}")
print(f"Pinecone Cloud: {cloud}")
print(f"Pinecone Region: {region}")
print(f"Pinecone Index: {index_name}")

# Initialize Pinecone
pc = Pinecone(api_key=api_key, cloud=cloud)

# List indexes
print(f"Listing all indexes...")
indexes = pc.list_indexes()
print(f"Available indexes: {indexes}")

# Get the specific index
print(f"Connecting to index: {index_name}")
index = pc.Index(index_name)

# Get index stats
print(f"Getting index stats...")
stats = index.describe_index_stats()
print(f"Index stats: {stats}")

# Check for UMP-test namespace
namespaces = stats.get("namespaces", {})
print(f"Available namespaces: {list(namespaces.keys())}")

if "UMP-test" in namespaces:
    print(f"Found UMP-test namespace with {namespaces['UMP-test'].get('vector_count')} vectors")
    
    # Query the UMP-test namespace
    print(f"Querying the UMP-test namespace...")
    # Create a dummy vector of the right dimension
    dummy_vector = [0.1] * 1536
    
    results = index.query(
        vector=dummy_vector,
        top_k=2,
        include_metadata=True,
        namespace="UMP-test"
    )
    
    print(f"Query results: {results}")
    if hasattr(results, 'matches'):
        print(f"Found {len(results.matches)} matches")
        for match in results.matches:
            print(f"Match ID: {match.id}, Score: {match.score}")
            if hasattr(match, 'metadata') and match.metadata:
                print(f"Metadata: {match.metadata}")
else:
    print(f"UMP-test namespace not found in index")

print("Test completed.") 