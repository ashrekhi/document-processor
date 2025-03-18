import os
import json
import hashlib
from typing import List, Dict, Any, Optional
from openai import OpenAI
import traceback
import time
from datetime import datetime
from dotenv import load_dotenv
import pathlib

# Import the Pinecone client and our EmbeddingService
try:
    from pinecone import Pinecone, ServerlessSpec
    PINECONE_IMPORT_SUCCESS = True
    print("Successfully imported pinecone package")
    # Print the imported Pinecone version to help with debugging
    import importlib.metadata
    try:
        pinecone_version = importlib.metadata.version("pinecone")
        print(f"Imported Pinecone version: {pinecone_version}")
    except Exception as ver_error:
        print(f"Could not determine Pinecone version: {str(ver_error)}")
except ImportError as e:
    print(f"WARNING: Failed to import from pinecone package due to ImportError: {str(e)}")
    print(f"This usually means the package is not installed or the wrong version is installed")
    import sys
    print(f"Python version: {sys.version}")
    print(f"Python path: {sys.path}")
    # Try to list installed packages
    try:
        import pkg_resources
        installed_packages = [d.project_name for d in pkg_resources.working_set]
        print(f"Installed packages: {installed_packages}")
    except Exception as pkg_error:
        print(f"Could not list installed packages: {str(pkg_error)}")
    PINECONE_IMPORT_SUCCESS = False
    # Define a stub Pinecone class to avoid errors
    class Pinecone:
        def __init__(self, api_key, **kwargs):
            print(f"WARNING: Using mock Pinecone class due to import failure")
            self.api_key = api_key
        
        def Index(self, index_name):
            return SimpleMockIndex()
        
        def list_indexes(self):
            return []
except Exception as e:
    print(f"WARNING: Failed to import from pinecone package due to unexpected error: {str(e)}")
    print(f"Exception type: {type(e).__name__}")
    PINECONE_IMPORT_SUCCESS = False
    # Define a stub Pinecone class to avoid errors
    class Pinecone:
        def __init__(self, api_key, **kwargs):
            print(f"WARNING: Using mock Pinecone class due to import failure")
            self.api_key = api_key
        
        def Index(self, index_name):
            return SimpleMockIndex()
        
        def list_indexes(self):
            return []

from app.services.embedding_service import EmbeddingService

# Get the absolute path to the .env file
env_path = pathlib.Path(__file__).parent.parent.parent / '.env'
print(f"Looking for .env file at: {env_path}")

# Check if .env file exists and log some diagnostic info about it
if os.path.exists(env_path):
    try:
        print(f"INFO: .env file found, size: {os.path.getsize(env_path)} bytes")
        with open(env_path, 'r') as f:
            env_content = f.readlines()
            print(f"INFO: .env file contains {len(env_content)} lines")
            # Print a sanitized version of the .env file for debugging
            print(f"DEBUG: Sanitized .env content:")
            for line in env_content:
                line = line.strip()
                if not line or line.startswith('#'):
                    # Skip empty lines and comments
                    continue
                if '=' in line:
                    key, value = line.split('=', 1)
                    # Mask sensitive values
                    if any(sensitive in key.upper() for sensitive in ['API_KEY', 'SECRET', 'PASSWORD', 'TOKEN']):
                        print(f"  {key}=****")
                    else:
                        print(f"  {key}={value}")
    except Exception as e:
        print(f"ERROR reading .env file: {str(e)}")
else:
    print(f"WARNING: .env file not found at {env_path}")
    # List environment directories to help debug
    parent_dir = env_path.parent
    print(f"Contents of parent directory ({parent_dir}):")
    try:
        for item in os.listdir(parent_dir):
            print(f"  {item}")
    except Exception as e:
        print(f"ERROR listing parent directory: {str(e)}")

# Load environment variables from the specified path
load_dotenv(dotenv_path=env_path)

# Check if environment variables are loaded
openai_api_key = os.getenv('OPENAI_API_KEY')
pinecone_api_key = os.getenv('PINECONE_API_KEY')
pinecone_index = os.getenv('PINECONE_INDEX', 'radiant-documents')
pinecone_cloud = os.getenv('PINECONE_CLOUD')
pinecone_env = os.getenv('PINECONE_ENVIRONMENT')
pinecone_region = os.getenv('PINECONE_REGION')

# Generate a hash of the Pinecone API key for comparison without revealing the full key
# This helps identify if different keys are being used between environments
if pinecone_api_key:
    key_hash = hashlib.md5(pinecone_api_key.encode()).hexdigest()
    print(f"***** ENVIRONMENT DIAGNOSTICS *****")
    print(f"PINECONE_API_KEY MD5 Hash: {key_hash}")
    print(f"PINECONE_INDEX: {pinecone_index}")
    print(f"PINECONE_CLOUD: {pinecone_cloud}")
    print(f"PINECONE_REGION: {pinecone_region}")
    print(f"PINECONE_ENVIRONMENT: {pinecone_env}")
    print(f"Current working directory: {os.getcwd()}")
    
    # Print all environment variables (masking sensitive values)
    print(f"ALL ENVIRONMENT VARIABLES:")
    for key, value in sorted(os.environ.items()):
        # Mask sensitive values
        if any(sensitive in key.upper() for sensitive in ['API_KEY', 'SECRET', 'PASSWORD', 'TOKEN']):
            print(f"  {key}=****")
        else:
            print(f"  {key}={value}")
    
    print(f"***** END DIAGNOSTICS *****")

# Add Pinecone cloud/environment/region debug info
pinecone_cloud = os.getenv('PINECONE_CLOUD')
pinecone_env = os.getenv('PINECONE_ENVIRONMENT')
pinecone_region = os.getenv('PINECONE_REGION')
print(f"PINECONE_CLOUD loaded: {'Yes' if pinecone_cloud else 'No'}")
print(f"PINECONE_ENVIRONMENT loaded: {'Yes' if pinecone_env else 'No'}")
print(f"PINECONE_REGION loaded: {'Yes' if pinecone_region else 'No'}")
if pinecone_cloud:
    print(f"PINECONE_CLOUD value: {pinecone_cloud}")
if pinecone_env:
    print(f"PINECONE_ENVIRONMENT value: {pinecone_env}")
if pinecone_region:
    print(f"PINECONE_REGION value: {pinecone_region}")

# Define a simple mock index to use as fallback if needed
class SimpleMockIndex:
    def __init__(self):
        print("WARNING: Using simplified mock Pinecone index for DEVELOPMENT purposes only")
        self.data = {}
    
    def upsert(self, vectors, namespace="default"):
        if namespace not in self.data:
            self.data[namespace] = {}
        
        for vec in vectors:
            self.data[namespace][vec["id"]] = (vec["values"], vec["metadata"])
        
        return {"upserted_count": len(vectors)}
    
    def query(self, vector, top_k=5, include_metadata=True, filter=None, namespace="default"):
        print(f"WARNING: Using mock query - real vector search is unavailable")
        
        # Simple mock response
        class MockMatch:
            def __init__(self, id):
                self.id = id
                self.score = 0.85
                self.metadata = {"text": "This is development mode only. Vector search is unavailable.", 
                               "doc_id": "dev-mode-doc", 
                               "filename": "dev-mode.txt"}
        
        class MockResponse:
            def __init__(self):
                self.matches = [MockMatch(f"mock_{i}") for i in range(3)]
        
        return MockResponse()
    
    def delete(self, filter=None, namespace="default"):
        return {"deleted_count": 0}
        
    def describe_index_stats(self):
        return {"namespaces": {"default": {"vector_count": 0}}}

class VectorDBService:
    def __init__(self, index_name: str = None, namespace: str = "default"):
        """Initialize the Vector DB service, connected to the specified index and namespace"""
        try:
            print(f"Initializing VectorDBService with index_name='{index_name}', namespace='{namespace}'")
            
            # First, check if we're using a mock implementation
            if not PINECONE_IMPORT_SUCCESS:
                print(f"***********************************************************************")
                print(f"* WARNING: USING MOCK PINECONE IMPLEMENTATION - VECTOR SEARCH IS LIMITED *")
                print(f"* Documents uploaded in this environment won't be properly vectorized   *")
                print(f"* Please fix the Pinecone import issue to enable full functionality     *")
                print(f"***********************************************************************")
            
            # Get the OpenAI API key from environment variables
            self.openai_api_key = os.getenv('OPENAI_API_KEY')
            if not self.openai_api_key:
                print("Error: OPENAI_API_KEY not set in environment variables")
                print(f".env file exists: {os.path.exists(env_path)}")
                raise ValueError("OPENAI_API_KEY not set in environment variables. Vector operations cannot proceed.")
            
            # Initialize an OpenAI API client for embeddings
            print(f"Creating embedding service...")
            self.embedding_service = EmbeddingService()
            print(f"Successfully created embedding service")
            
            # Initialize OpenAI client
            self.openai_client = OpenAI(api_key=self.openai_api_key)
            print(f"Successfully initialized OpenAI client")
            
            # Set the index_name to use
            default_index = "document-processor"
            self.index_name = index_name if index_name else os.getenv('PINECONE_INDEX', default_index)
            print(f"Using index name: {self.index_name}")
            
            # Get the namespace to use
            self.namespace = namespace
            print(f"Using namespace: {self.namespace}")
            
            # Get the Pinecone API key from environment variables
            self.pinecone_api_key = os.getenv('PINECONE_API_KEY')
            if not self.pinecone_api_key:
                print("Error: PINECONE_API_KEY not set in environment variables")
                print(f".env file exists: {os.path.exists(env_path)}")
                if os.getenv('ALLOW_DEV_FALLBACK', '').lower() == 'true':
                    print(f"WARNING: Using development fallback mode for Pinecone. Vector search features will be limited.")
                    self.pinecone_index = SimpleMockIndex()
                    return
                else:
                    raise ValueError("PINECONE_API_KEY not set in environment variables. Vector operations cannot proceed.")
            
            # Get Pinecone cloud, region and environment if set
            self.pinecone_cloud = os.getenv('PINECONE_CLOUD')
            self.pinecone_env = os.getenv('PINECONE_ENVIRONMENT')
            self.pinecone_region = os.getenv('PINECONE_REGION')
            
            # Check if we have a new or old format API key
            self.is_new_api_key = self.pinecone_api_key.startswith('pcsk_')
            
            if self.is_new_api_key:
                print(f"DEBUG: Using new Pinecone API key format (pcsk_)")
                if self.pinecone_cloud:
                    print(f"DEBUG: Using Pinecone cloud: {self.pinecone_cloud}")
                else:
                    print(f"WARNING: New Pinecone API keys require PINECONE_CLOUD parameter (typically 'aws' or 'gcp')")
                    print(f"Add PINECONE_CLOUD=aws to your .env file")
                    
                if self.pinecone_region:
                    print(f"DEBUG: Using Pinecone region: {self.pinecone_region}")
                else:
                    print(f"WARNING: New Pinecone API keys require PINECONE_REGION parameter (e.g., 'us-east-1', 'us-west-2')")
                    print(f"Add PINECONE_REGION=us-east-1 to your .env file")
            else:
                print(f"DEBUG: Using older Pinecone API key format")
                if self.pinecone_env:
                    print(f"DEBUG: Using Pinecone environment: {self.pinecone_env}")
                else:
                    print(f"WARNING: Older Pinecone API keys require PINECONE_ENVIRONMENT parameter")
                    print(f"Add PINECONE_ENVIRONMENT=gcp-starter to your .env file")
            
            # If Pinecone import failed, use the fallback
            if not PINECONE_IMPORT_SUCCESS:
                print(f"WARNING: Pinecone import failed. Using fallback mock implementation.")
                if os.getenv('ALLOW_DEV_FALLBACK', '').lower() == 'true':
                    self.pinecone_index = SimpleMockIndex()
                    return
                else:
                    raise ValueError("Failed to import Pinecone library and ALLOW_DEV_FALLBACK is not enabled.")
            
            try:
                # Initialize Pinecone client
                print(f"Initializing Pinecone with new client...")
                print(f"DEBUG: About to initialize Pinecone with API key starting with: {self.pinecone_api_key[:5]}...")
                
                # Initialize Pinecone based on API key format
                if self.is_new_api_key:
                    if self.pinecone_cloud:
                        print(f"DEBUG: Using cloud parameter in Pinecone initialization: {self.pinecone_cloud}")
                        self.pc = Pinecone(api_key=self.pinecone_api_key, cloud=self.pinecone_cloud)
                    else:
                        print(f"DEBUG: No cloud parameter provided, trying without it")
                        self.pc = Pinecone(api_key=self.pinecone_api_key)
                else:
                    if self.pinecone_env:
                        print(f"DEBUG: Using environment parameter in Pinecone initialization: {self.pinecone_env}")
                        self.pc = Pinecone(api_key=self.pinecone_api_key, environment=self.pinecone_env)
                    else:
                        print(f"DEBUG: No environment parameter provided, trying without it")
                        self.pc = Pinecone(api_key=self.pinecone_api_key)
                    
                print(f"DEBUG: Pinecone client initialized successfully")
                
                try:
                    # Check if index exists and create if needed
                    print(f"DEBUG: Ensuring index '{self.index_name}' exists")
                    
                    # First, list all available indexes to debug
                    print(f"DEBUG: Listing all available Pinecone indexes in account...")
                    all_indexes = self.pc.list_indexes()
                    print(f"DEBUG: ALL AVAILABLE INDEXES: {all_indexes}")
                    
                    # Proceed with index creation check/process
                    self._ensure_index_exists()
                    
                    # Connect to the index
                    print(f"Connecting to Pinecone index: {self.index_name}")
                    self.pinecone_index = self.pc.Index(self.index_name)
                    print(f"DEBUG: Got Pinecone index reference")
                    
                    # Test the connection and dump DETAILED stats
                    print(f"DEBUG: About to describe index stats")
                    stats = self.pinecone_index.describe_index_stats()
                    print(f"Index stats: {stats}")
                    
                    # Detailed analysis of the index stats to debug namespace issues
                    print(f"DEBUG: DETAILED INDEX ANALYSIS")
                    if 'namespaces' in stats:
                        ns_count = len(stats['namespaces'])
                        print(f"Found {ns_count} namespaces in index '{self.index_name}'")
                        for ns_name, ns_data in stats['namespaces'].items():
                            vector_count = ns_data.get('vector_count', 0)
                            print(f"  Namespace '{ns_name}': {vector_count} vectors")
                    else:
                        print(f"No namespaces found in index '{self.index_name}'")
                    
                    print(f"DEBUG: Successfully connected to Pinecone index '{self.index_name}'")
                    
                except Exception as index_error:
                    print(f"ERROR: Failed to connect to Pinecone index: {str(index_error)}")
                    print(f"DEBUG: Full error details:")
                    traceback.print_exc()
                    
                    print(f"\nTROUBLESHOOTING GUIDE:")
                    if self.is_new_api_key:
                        print(f"1. Check that your Pinecone API key is valid and not expired")
                        print(f"2. Verify that PINECONE_CLOUD in your .env file is set correctly (usually 'aws' or 'gcp')")
                        print(f"3. Verify that PINECONE_REGION in your .env file is set correctly (e.g., 'us-east-1')")
                        print(f"4. Ensure you're using the correct value for PINECONE_INDEX")
                        print(f"5. Check if your Pinecone account has an active subscription and sufficient quota")
                    else:
                        print(f"1. Check that your Pinecone API key is valid and not expired")
                        print(f"2. Verify that PINECONE_ENVIRONMENT in your .env file matches your Pinecone account")
                        print(f"3. Ensure the index '{self.index_name}' exists or can be created in your Pinecone project")
                        print(f"4. Check if your Pinecone account has an active subscription and sufficient quota")
                    
                    if os.getenv('ALLOW_DEV_FALLBACK', '').lower() == 'true':
                        print(f"WARNING: Using development fallback mode for Pinecone. Vector search features will be limited.")
                        self.pinecone_index = SimpleMockIndex()
                    else:
                        raise ValueError(f"Failed to connect to Pinecone index: {str(index_error)}")
                
            except Exception as e:
                print(f"ERROR: Failed to initialize Pinecone client: {str(e)}")
                print(f"DEBUG: Full error details:")
                traceback.print_exc()
                
                if os.getenv('ALLOW_DEV_FALLBACK', '').lower() == 'true':
                    print(f"WARNING: Using development fallback mode for Pinecone. Vector search features will be limited.")
                    self.pinecone_index = SimpleMockIndex()
                else:
                    raise ValueError(f"Failed to initialize Pinecone client: {str(e)}")
        except Exception as e:
            print(f"ERROR: Failed to initialize VectorDBService: {str(e)}")
            raise ValueError(f"Failed to initialize VectorDBService: {str(e)}")
    
    def _ensure_index_exists(self):
        """Check if the index exists and create it if it doesn't"""
        try:
            # List all indexes
            print(f"DEBUG: Listing all Pinecone indexes...")
            indexes = self.pc.list_indexes()
            print(f"DEBUG: Found indexes: {indexes}")
            
            # Check if the index already exists by looking at the 'indexes' list
            # In the newer Pinecone API, the format has changed
            index_exists = False
            
            # New format returns a dict with 'indexes' key containing a list of objects with 'name' field
            if isinstance(indexes, dict) and 'indexes' in indexes:
                index_list = indexes['indexes']
                for idx in index_list:
                    if isinstance(idx, dict) and 'name' in idx and idx['name'] == self.index_name:
                        index_exists = True
                        print(f"DEBUG: Found existing index '{self.index_name}' in indexes list")
                        break
            # Old format returns a list of string names
            elif isinstance(indexes, list):
                index_exists = self.index_name in indexes
                if index_exists:
                    print(f"DEBUG: Found existing index '{self.index_name}' in indexes list (old format)")
            
            # Fix the index existence check - the log shows we're incorrectly reporting False even when index exists
            if not index_exists:
                # Double check by looking at the raw response for the index name
                if isinstance(indexes, dict) and 'indexes' in indexes:
                    raw_response = str(indexes)
                    if f"'name': '{self.index_name}'" in raw_response or f'"name": "{self.index_name}"' in raw_response:
                        index_exists = True
                        print(f"DEBUG: Found existing index '{self.index_name}' in raw response")
            
            print(f"DEBUG: Index '{self.index_name}' exists: {index_exists}")
            
            if not index_exists:
                print(f"Index '{self.index_name}' not found. Creating...")
                
                # Create index based on API key format
                if self.is_new_api_key:
                    if not self.pinecone_region:
                        print(f"ERROR: PINECONE_REGION is required for creating indexes with new API keys")
                        print(f"Add PINECONE_REGION=us-east-1 to your .env file")
                        raise ValueError("PINECONE_REGION environment variable is required but not set")
                        
                    print(f"DEBUG: Creating index with ServerlessSpec for new API key format")
                    print(f"DEBUG: Using cloud={self.pinecone_cloud or 'aws'}, region={self.pinecone_region}")
                    
                    self.pc.create_index(
                        name=self.index_name,
                        dimension=1536,
                        metric="cosine",
                        spec=ServerlessSpec(
                            cloud=self.pinecone_cloud or "aws",
                            region=self.pinecone_region
                        )
                    )
                else:
                    print(f"DEBUG: Creating index for old API key format")
                    self.pc.create_index(
                        name=self.index_name,
                        dimension=1536,
                        metric="cosine",
                        environment=self.pinecone_env
                    )
                    
                print(f"Created new Pinecone index: {self.index_name}")
            else:
                print(f"Pinecone index '{self.index_name}' already exists.")
        except Exception as e:
            # Check if the error is a 409 Conflict (index already exists)
            if "409" in str(e) and "ALREADY_EXISTS" in str(e):
                print(f"Index '{self.index_name}' already exists (verified from error response).")
                # This is actually not an error, the index exists which is what we want
                return
            
            print(f"Error ensuring index exists: {str(e)}")
            import traceback
            print(f"DEBUG: Full index creation error details:\n{traceback.format_exc()}")
            raise ValueError(f"Failed to ensure Pinecone index exists: {str(e)}")
    
    def _generate_embedding(self, text: str) -> List[float]:
        """Generate an embedding for a text using our embedding service"""
        print(f"Generating embedding for text of length {len(text)} characters using embedding service")
        
        try:
            # Use our embedding service to generate the embedding
            embedding = self.embedding_service.generate_single_embedding(text)
            if embedding:
                print(f"Successfully generated embedding of dimension {len(embedding)}")
                return embedding
            else:
                print(f"Failed to generate embedding via embedding service")
                raise ValueError("Failed to generate embedding: embedding service returned None")
        except Exception as e:
            print(f"Error generating embedding: {str(e)}")
            raise ValueError(f"Error generating embedding: {str(e)}")
    
    def store_document_chunks(self, doc_id: str, chunks: List[str], metadata: Dict[str, Any]) -> bool:
        """Store document chunks in the vector database"""
        if not self.pinecone_index or not self.openai_client:
            error_msg = f"Vector database not initialized for document {doc_id}. Cannot store chunks."
            print(f"ERROR: {error_msg}")
            raise ValueError(error_msg)
        
        try:
            # Check if there are an unusual number of chunks (potential infinite loop in text splitting)
            if len(chunks) > 1000:
                print(f"WARNING: Unusually high number of chunks ({len(chunks)}) detected. Something may be wrong with text splitting.")
                print(f"Processing only the first 1000 chunks to prevent memory issues.")
                chunks = chunks[:1000]  # Limit to a reasonable number
            
            print(f"Storing document chunks: {len(chunks)} chunks for document {doc_id}")
            
            # Get namespace from folder or use default
            namespace = metadata.get("folder", "default")
            
            # Process chunks in batches to avoid rate limits and memory issues
            batch_size = 10
            total_vectors = 0
            total_batches = (len(chunks) - 1) // batch_size + 1
            
            for i in range(0, len(chunks), batch_size):
                batch = chunks[i:i+batch_size]
                current_batch = i // batch_size + 1
                
                # Only log every 5 batches for large documents
                if current_batch % 5 == 0 or current_batch <= 2 or current_batch == total_batches:
                    print(f"Processing batch {current_batch}/{total_batches} ({len(batch)} chunks)")
                
                vectors = []
                
                for j, chunk in enumerate(batch):
                    # Skip empty chunks
                    if not chunk.strip():
                        continue
                        
                    chunk_id = f"{doc_id}_{i+j}"
                    embedding = self._generate_embedding(chunk)
                    
                    if embedding:
                        # Keep metadata small to reduce memory usage
                        chunk_metadata = {
                            "doc_id": doc_id,
                            "chunk_index": i+j,
                            "text": chunk[:500],  # Reduce metadata size even more
                            "filename": metadata.get("filename", "")
                        }
                        
                        # Format for the new client
                        vectors.append({
                            "id": chunk_id,
                            "values": embedding,
                            "metadata": chunk_metadata
                        })
                
                if vectors:
                    # Upsert vectors to Pinecone with namespace
                    try:
                        result = self.pinecone_index.upsert(
                            vectors=vectors,
                            namespace=namespace
                        )
                        total_vectors += len(vectors)
                        # Clear vectors list to free memory
                        vectors = []
                    except Exception as upsert_error:
                        print(f"Error upserting batch {current_batch}: {str(upsert_error)}")
                        # Continue with next batch rather than failing entire process
            
            print(f"Completed storing {total_vectors} vectors for document {doc_id}")
            return total_vectors > 0  # Success if at least some vectors were stored
        except Exception as e:
            print(f"Error storing document chunks: {str(e)}")
            traceback.print_exc()
            raise ValueError(f"Failed to store document chunks: {str(e)}")
    
    def search_similar_chunks(self, query: str, top_k: int = 5, namespace: str = None) -> List[Dict[str, Any]]:
        """Search for similar chunks to a query in a specific namespace"""
        if not self.pinecone_index or not self.openai_client:
            error_msg = "Vector database not initialized. Cannot perform search."
            print(f"ERROR: {error_msg}")
            raise ValueError(error_msg)
        
        try:
            print(f"{'='*80}")
            print(f"VECTOR SEARCH: Starting search operation at {time.strftime('%H:%M:%S')}")
            print(f"VECTOR SEARCH: Searching for chunks similar to: '{query[:50]}...' (query length: {len(query)})")
            print(f"VECTOR SEARCH: Parameters: top_k={top_k}, namespace={namespace}")
            print(f"VECTOR SEARCH: Current class implementation: {self.pinecone_index.__class__.__name__}")
            
            # Get index stats to understand what namespaces exist and vector counts
            try:
                stats = self.pinecone_index.describe_index_stats()
                print(f"VECTOR SEARCH: Current index stats: {stats}")
                
                # Log available namespaces
                namespaces = stats.get("namespaces", {})
                print(f"VECTOR SEARCH: Available namespaces: {list(namespaces.keys())}")
                
                # Check if the requested namespace exists
                if namespace and namespace not in namespaces:
                    print(f"VECTOR SEARCH WARNING: Requested namespace '{namespace}' doesn't exist in index")
                    print(f"VECTOR SEARCH: Will try to search anyway, but expect empty results")
                
                # Check if root namespace exists and has vectors
                if "root" in namespaces:
                    root_vectors = namespaces["root"].get("vector_count", 0)
                    print(f"VECTOR SEARCH: Root namespace has {root_vectors} vectors")
                    
                    # If user specified None for namespace but there are vectors in root, suggest trying with root
                    if namespace is None and root_vectors > 0:
                        print(f"VECTOR SEARCH SUGGESTION: There are {root_vectors} vectors in 'root' namespace")
                        print(f"VECTOR SEARCH SUGGESTION: Consider searching with namespace='root' explicitly")
            except Exception as stats_error:
                print(f"VECTOR SEARCH WARNING: Error getting index stats: {str(stats_error)}")
                print(f"VECTOR SEARCH: Will proceed with search anyway")
            
            # Check if query is too short
            if len(query) < 5:
                print(f"VECTOR SEARCH WARNING: Query is very short ({len(query)} chars). This may produce poor search results.")
            
            # Generate embedding for the query
            print(f"VECTOR SEARCH: Generating embedding for query...")
            query_start_time = time.time()
            query_embedding = self._generate_embedding(query)
            embedding_time = time.time() - query_start_time
            print(f"VECTOR SEARCH: Generated query embedding in {embedding_time:.2f} seconds")
            print(f"VECTOR SEARCH: Embedding dimension: {len(query_embedding)}")
            
            # Check if we should try the root namespace as fallback
            try_namespaces = [namespace]
            if namespace is None:
                # If no namespace specified, let's also try 'root' as a fallback if it exists
                # but only if initial search returns no results
                try:
                    if stats and "namespaces" in stats and "root" in stats["namespaces"]:
                        if stats["namespaces"]["root"].get("vector_count", 0) > 0:
                            print(f"VECTOR SEARCH: Will try 'root' namespace if default search returns no results")
                except:
                    pass
            
            # Search Pinecone with namespace
            print(f"VECTOR SEARCH: Executing search in Pinecone at {time.strftime('%H:%M:%S')}...")
            print(f"VECTOR SEARCH: Pinecone index type: {type(self.pinecone_index)}")
            print(f"VECTOR SEARCH: Using namespace: '{namespace}'")
            
            search_start_time = time.time()
            
            # Execute Pinecone query
            results = self.pinecone_index.query(
                vector=query_embedding,
                top_k=top_k,
                include_metadata=True,
                namespace=namespace
            )
            search_time = time.time() - search_start_time
            print(f"VECTOR SEARCH: Executed search in {search_time:.2f} seconds")
            
            # Log raw results
            print(f"VECTOR SEARCH: Results type: {type(results)}")
            print(f"VECTOR SEARCH: Results has matches: {hasattr(results, 'matches')}")
            if hasattr(results, 'matches'):
                print(f"VECTOR SEARCH: Found {len(results.matches)} matches")
                
                # Try root namespace as fallback if default namespace returned no results
                if len(results.matches) == 0 and namespace is None:
                    try:
                        print(f"VECTOR SEARCH: No results in default namespace, trying 'root' namespace as fallback...")
                        root_search_start_time = time.time()
                        root_results = self.pinecone_index.query(
                            vector=query_embedding,
                            top_k=top_k,
                            include_metadata=True,
                            namespace="root"
                        )
                        root_search_time = time.time() - root_search_start_time
                        
                        if hasattr(root_results, 'matches') and len(root_results.matches) > 0:
                            print(f"VECTOR SEARCH: Found {len(root_results.matches)} matches in 'root' namespace")
                            results = root_results
                            print(f"VECTOR SEARCH: Using results from 'root' namespace instead")
                        else:
                            print(f"VECTOR SEARCH: No results in 'root' namespace either")
                    except Exception as root_error:
                        print(f"VECTOR SEARCH: Error searching 'root' namespace: {str(root_error)}")
            else:
                print(f"VECTOR SEARCH: Unexpected response structure from Pinecone")
                print(f"VECTOR SEARCH: Raw results: {results}")
                raise ValueError("Unexpected response structure from Pinecone")
            
            # Format results for the new client response format
            print(f"VECTOR SEARCH: Processing search results...")
            formatted_results = []
            
            for match in results.matches:
                # Debug individual match structure
                print(f"VECTOR SEARCH: Processing match with ID: {match.id}, score: {match.score}")
                print(f"VECTOR SEARCH: Match metadata present: {hasattr(match, 'metadata')}")
                
                if not hasattr(match, 'metadata') or not match.metadata:
                    print(f"VECTOR SEARCH WARNING: Match has no metadata: {match}")
                    continue
                
                # Log detailed metadata
                print(f"VECTOR SEARCH: Match metadata keys: {match.metadata.keys() if hasattr(match, 'metadata') else 'None'}")
                
                formatted_match = {
                    "id": match.id,
                    "score": match.score,
                    "doc_id": match.metadata.get("doc_id", ""),
                    "text": match.metadata.get("text", ""),
                    "source": match.metadata.get("source", ""),
                    "filename": match.metadata.get("filename", ""),
                    "folder": match.metadata.get("folder", "")
                }
                
                # Log metadata for debugging
                if len(match.metadata.get("text", "")) > 0:
                    text_sample = match.metadata.get("text", "")[:50].replace('\n', ' ') + "..."
                    print(f"VECTOR SEARCH: Match text sample: '{text_sample}'")
                else:
                    print(f"VECTOR SEARCH WARNING: Match has empty text: {match.metadata}")
                
                formatted_results.append(formatted_match)
            
            print(f"VECTOR SEARCH: Found {len(formatted_results)} matches after formatting")
            if formatted_results:
                top_score = formatted_results[0]["score"] if formatted_results else 0
                print(f"VECTOR SEARCH: Top match score: {top_score:.4f}")
                
                # Log the scores distribution
                if len(formatted_results) > 1:
                    scores = [result["score"] for result in formatted_results]
                    avg_score = sum(scores) / len(scores)
                    min_score = min(scores)
                    print(f"VECTOR SEARCH: Score distribution - min: {min_score:.4f}, avg: {avg_score:.4f}, max: {top_score:.4f}")
            else:
                print(f"VECTOR SEARCH WARNING: No formatted results after processing.")
                print(f"VECTOR SEARCH SUGGESTIONS:")
                print(f"  1. Check if documents have been processed and embeddings stored")
                print(f"  2. Verify document IDs are correct")
                print(f"  3. Try searching with namespace='root' explicitly") 
                print(f"  4. Try searching without document ID filtering")
                print(f"  5. Check if the namespace contains vectors with describe_index_stats()")
            
            print(f"VECTOR SEARCH: Returning {len(formatted_results)} results")
            print(f"{'='*80}")
            return formatted_results
        except Exception as e:
            error_type = type(e).__name__
            print(f"VECTOR SEARCH ERROR ({error_type}): {str(e)}")
            import traceback
            print(f"VECTOR SEARCH ERROR: Full error details:\n{traceback.format_exc()}")
            raise ValueError(f"Vector search failed: {str(e)}")
    
    def delete_document(self, doc_id: str, namespace: str = None) -> bool:
        """Delete all chunks for a document"""
        if not self.pinecone_index:
            error_msg = "Vector database not initialized. Cannot delete document."
            print(f"ERROR: {error_msg}")
            raise ValueError(error_msg)
        
        try:
            # If namespace is provided, delete only from that namespace
            if namespace:
                print(f"Deleting document {doc_id} from namespace '{namespace}'")
                self.pinecone_index.delete(
                    filter={"doc_id": doc_id},
                    namespace=namespace
                )
            else:
                # If no namespace is provided, we need to find all namespaces that contain this document
                print(f"Deleting document {doc_id} from all namespaces")
                
                # Get index stats to find all namespaces
                stats = self.pinecone_index.describe_index_stats()
                namespaces = stats.get("namespaces", {}).keys()
                
                for ns in namespaces:
                    print(f"Checking namespace '{ns}' for document {doc_id}")
                    # Delete from each namespace
                    self.pinecone_index.delete(
                        filter={"doc_id": doc_id},
                        namespace=ns
                    )
            
            return True
        except Exception as e:
            print(f"Error deleting document from vector database: {str(e)}")
            traceback.print_exc()
            raise ValueError(f"Failed to delete document: {str(e)}")
    
    def store_document_metadata(self, doc_id: str, metadata: Dict[str, Any]) -> bool:
        """Store document metadata in S3"""
        try:
            # We'll store the metadata in S3 since Pinecone is just for vectors
            # This method is called by DocumentService
            print(f"Storing metadata for document {doc_id}")
            
            # Add processing status to metadata if not already present
            if "id" not in metadata:
                metadata["id"] = doc_id
            if "document_key" not in metadata:
                metadata["document_key"] = f"{doc_id}_{metadata.get('filename', 'unknown')}"
            if "created_at" not in metadata:
                metadata["created_at"] = datetime.now().isoformat()
            if "processed" not in metadata:
                metadata["processed"] = False
            if "processing" not in metadata:
                metadata["processing"] = True
            
            # Convert metadata to JSON
            metadata_json = json.dumps(metadata)
            
            # Store in S3 (this would typically be done by S3Service)
            # For now, we'll just return True
            print(f"Metadata for document {doc_id} prepared for storage")
            return True
        except Exception as e:
            print(f"Error storing document metadata: {str(e)}")
            raise ValueError(f"Failed to store document metadata: {str(e)}")
    
    def get_document_metadata(self, doc_id: str) -> Dict[str, Any]:
        """Get document metadata from S3"""
        # Note: In a real implementation, you would fetch this from S3
        return {
            "id": doc_id,
            "processed": True,
            "processing": False
        }
    
    def list_namespaces(self) -> List[str]:
        """List all available namespaces"""
        if not self.pinecone_index:
            error_msg = "Vector database not initialized. Cannot list namespaces."
            print(f"ERROR: {error_msg}")
            raise ValueError(error_msg)
        
        try:
            # Get index stats to find all namespaces
            stats = self.pinecone_index.describe_index_stats()
            namespaces = list(stats.get("namespaces", {}).keys())
            
            return namespaces
        except Exception as e:
            print(f"Error listing namespaces: {str(e)}")
            raise ValueError(f"Failed to list namespaces: {str(e)}")
    
    def delete_namespace(self, namespace: str) -> bool:
        """Delete an entire namespace and all vectors within it"""
        if not self.pinecone_index:
            error_msg = f"Vector database not initialized. Cannot delete namespace '{namespace}'."
            print(f"ERROR: {error_msg}")
            raise ValueError(error_msg)
        
        try:
            print(f"VECTOR DB: Deleting namespace '{namespace}'")
            
            # Check if namespace exists
            stats = self.pinecone_index.describe_index_stats()
            if namespace not in stats.get("namespaces", {}):
                print(f"VECTOR DB: Namespace '{namespace}' does not exist or is already empty.")
                return True  # Success since it doesn't exist anyway
            
            # Deleting all vectors in the namespace
            # Get vector count to log before deletion
            vector_count = stats.get("namespaces", {}).get(namespace, {}).get("vector_count", 0)
            print(f"VECTOR DB: Found {vector_count} vectors in namespace '{namespace}'")
            
            # Delete all vectors in the namespace (Pinecone doesn't have a direct "delete namespace" operation)
            # We use an empty filter which deletes everything in the namespace
            result = self.pinecone_index.delete(
                filter={},  # Empty filter deletes all vectors
                namespace=namespace
            )
            
            print(f"VECTOR DB: Successfully deleted namespace '{namespace}'")
            return True
        except Exception as e:
            print(f"VECTOR DB ERROR: Error deleting namespace '{namespace}': {str(e)}")
            import traceback
            traceback.print_exc()
            raise ValueError(f"Failed to delete namespace: {str(e)}")
    
    def search_across_namespaces(self, query: str, top_k: int = 5) -> List[Dict[str, Any]]:
        """Search for similar chunks across all namespaces"""
        if not self.pinecone_index or not self.openai_client:
            error_msg = "Vector database not initialized. Cannot search across namespaces."
            print(f"ERROR: {error_msg}")
            raise ValueError(error_msg)
        
        try:
            print(f"VECTOR CROSS-NAMESPACE SEARCH: Searching for chunks similar to: '{query[:50]}...' (query length: {len(query)})")
            print(f"VECTOR CROSS-NAMESPACE SEARCH: Parameters: top_k={top_k}")
            
            # Get all namespaces
            namespaces = self.list_namespaces()
            print(f"VECTOR CROSS-NAMESPACE SEARCH: Found {len(namespaces)} namespaces: {namespaces}")
            
            if not namespaces:
                print(f"VECTOR CROSS-NAMESPACE SEARCH: No namespaces found. Returning empty results.")
                return []
            
            # Generate embedding for the query (do this once)
            print(f"VECTOR CROSS-NAMESPACE SEARCH: Generating embedding for query...")
            query_start_time = time.time()
            query_embedding = self._generate_embedding(query)
            embedding_time = time.time() - query_start_time
            print(f"VECTOR CROSS-NAMESPACE SEARCH: Generated query embedding in {embedding_time:.2f} seconds")
            
            # Search in each namespace
            all_results = []
            all_start_time = time.time()
            
            for namespace in namespaces:
                print(f"VECTOR CROSS-NAMESPACE SEARCH: Searching in namespace: {namespace}")
                namespace_start_time = time.time()
                
                # Search Pinecone with namespace
                try:
                    results = self.pinecone_index.query(
                        vector=query_embedding,
                        top_k=top_k,
                        include_metadata=True,
                        namespace=namespace
                    )
                    
                    # Format results for the new client response format and add namespace
                    for match in results.matches:
                        all_results.append({
                            "id": match.id,
                            "score": match.score,
                            "doc_id": match.metadata.get("doc_id", ""),
                            "text": match.metadata.get("text", ""),
                            "source": match.metadata.get("source", ""),
                            "filename": match.metadata.get("filename", ""),
                            "folder": match.metadata.get("folder", ""),
                            "namespace": namespace
                        })
                    
                    namespace_time = time.time() - namespace_start_time
                    print(f"VECTOR CROSS-NAMESPACE SEARCH: Found {len(results.matches)} matches in namespace '{namespace}' in {namespace_time:.2f} seconds")
                    
                except Exception as namespace_error:
                    error_type = type(namespace_error).__name__
                    print(f"VECTOR CROSS-NAMESPACE SEARCH ERROR ({error_type}): Error searching namespace '{namespace}': {str(namespace_error)}")
            
            total_search_time = time.time() - all_start_time
            print(f"VECTOR CROSS-NAMESPACE SEARCH: Completed searches across all namespaces in {total_search_time:.2f} seconds")
            print(f"VECTOR CROSS-NAMESPACE SEARCH: Found {len(all_results)} total matches across all namespaces")
            
            # Sort by score (highest first)
            all_results.sort(key=lambda x: x["score"], reverse=True)
            
            # Trim to top_k results
            top_results = all_results[:top_k]
            print(f"VECTOR CROSS-NAMESPACE SEARCH: Returning top {len(top_results)} results")
            
            # Log namespace distribution in final results
            if top_results:
                namespace_counts = {}
                for result in top_results:
                    ns = result["namespace"]
                    namespace_counts[ns] = namespace_counts.get(ns, 0) + 1
                
                print(f"VECTOR CROSS-NAMESPACE SEARCH: Final results namespace distribution: {namespace_counts}")
                
                # Log score range
                top_score = top_results[0]["score"] if top_results else 0
                min_score = top_results[-1]["score"] if top_results else 0
                print(f"VECTOR CROSS-NAMESPACE SEARCH: Score range in final results - min: {min_score:.4f}, max: {top_score:.4f}")
            
            return top_results
        except Exception as e:
            error_type = type(e).__name__
            print(f"VECTOR CROSS-NAMESPACE SEARCH ERROR ({error_type}): {str(e)}")
            import traceback
            print(f"VECTOR CROSS-NAMESPACE SEARCH ERROR: Full error details:\n{traceback.format_exc()}")
            raise ValueError(f"Cross-namespace search failed: {str(e)}")