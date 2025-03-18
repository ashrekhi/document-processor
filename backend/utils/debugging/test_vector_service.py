from app.services.vector_db_service import VectorDBService
import time
from openai import OpenAI

print("Testing VectorDBService with the UMP-test namespace...")

# Initialize VectorDBService
vector_service = VectorDBService()

# Add OpenAI client to VectorDBService
vector_service.openai_client = OpenAI(api_key=vector_service.openai_api_key)

# Check if initialized properly
print(f"VectorDBService initialized with index: {vector_service.index_name}")

# Get index stats to verify namespaces
try:
    print("Getting index stats...")
    stats = vector_service.pinecone_index.describe_index_stats()
    print(f"Index stats: {stats}")
    
    # List available namespaces
    namespaces = stats.get("namespaces", {})
    print(f"Available namespaces: {list(namespaces.keys())}")
    
    # Check for UMP-test namespace
    if "UMP-test" in namespaces:
        print(f"UMP-test namespace found with {namespaces['UMP-test'].get('vector_count')} vectors")
        
        # Try to search in UMP-test namespace
        print("Performing search in UMP-test namespace...")
        query = "medical record notes"
        search_start = time.time()
        results = vector_service.search_similar_chunks(
            query=query,
            top_k=3,
            namespace="UMP-test"
        )
        search_time = time.time() - search_start
        
        print(f"Search completed in {search_time:.2f} seconds")
        print(f"Found {len(results)} results")
        
        # Print results
        for i, result in enumerate(results):
            print(f"Result {i+1}:")
            print(f"  Score: {result.get('score')}")
            print(f"  Document ID: {result.get('doc_id')}")
            print(f"  Text: {result.get('text')[:150]}...")
    else:
        print("UMP-test namespace not found in index!")
except Exception as e:
    print(f"Error checking index stats: {str(e)}")
    import traceback
    traceback.print_exc()

print("Test completed.") 