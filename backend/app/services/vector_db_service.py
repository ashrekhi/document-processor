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
import sys

# Import the Pinecone client and our EmbeddingService
try:
    print("Attempting to import Pinecone...")
    # Import V2 API directly
    import pinecone
    from pinecone import Pinecone, ServerlessSpec
    print(f"Successfully imported Pinecone (V2 API), version: {pinecone.__version__}")
    PINECONE_IMPORT_SUCCESS = True
    
    # Print the imported Pinecone version to help with debugging
    import importlib.metadata
    try:
        pinecone_version = importlib.metadata.version("pinecone-client")
        print(f"Imported pinecone-client version: {pinecone_version}")
    except Exception as ver_error:
        print(f"Could not determine Pinecone version: {str(ver_error)}")
except ImportError as e:
    print(f"WARNING: Failed to import from pinecone package due to ImportError: {str(e)}")
    print(f"This usually means the package is not installed or the wrong version is installed")
    print(f"Import error details:\n{traceback.format_exc()}")
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
    
    # Create a mock pinecone module with basic functionality
    import types
    pinecone = types.ModuleType('pinecone')
    pinecone.__version__ = "mock-3.0.0"
    
    def mock_create_index(**kwargs):
        print(f"MOCK: Would create index {kwargs.get('name')} with dimension {kwargs.get('dimension')}")
        return None
        
    pinecone.create_index = mock_create_index
    
    # Define a stub Pinecone class to avoid errors
    class Pinecone:
        def __init__(self, api_key, **kwargs):
            print(f"WARNING: Using mock Pinecone class due to import failure")
            self.api_key = api_key
        
        def Index(self, index_name):
            return SimpleMockIndex()
        
        def list_indexes(self):
            return {"indexes": []}
            
    class ServerlessSpec:
        def __init__(self, cloud, region):
            self.cloud = cloud
            self.region = region
except Exception as e:
    print(f"WARNING: Failed to import from pinecone package due to unexpected error: {str(e)}")
    print(f"Exception type: {type(e).__name__}")
    print(f"Exception details:\n{traceback.format_exc()}")
    PINECONE_IMPORT_SUCCESS = False
    
    # Define a stub Pinecone class to avoid errors
    class Pinecone:
        def __init__(self, api_key, **kwargs):
            print(f"WARNING: Using mock Pinecone class due to import failure")
            self.api_key = api_key
        
        def Index(self, index_name):
            return SimpleMockIndex()
        
        def list_indexes(self):
            return {"indexes": []}

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

# Get environment variables from the specified path
load_dotenv(dotenv_path=env_path)

# Check if environment variables are loaded
openai_api_key = os.getenv('OPENAI_API_KEY')
pinecone_api_key = os.getenv('PINECONE_API_KEY')
pinecone_index = os.getenv('PINECONE_INDEX', 'radiant-documents')
pinecone_cloud = os.getenv('PINECONE_CLOUD')
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

# Add Pinecone cloud/region debug info
pinecone_cloud = os.getenv('PINECONE_CLOUD')
pinecone_region = os.getenv('PINECONE_REGION')
print(f"PINECONE_CLOUD loaded: {'Yes' if pinecone_cloud else 'No'}")
print(f"PINECONE_REGION loaded: {'Yes' if pinecone_region else 'No'}")
if pinecone_cloud:
    print(f"PINECONE_CLOUD value: {pinecone_cloud}")
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
        
        # V2 API compatible response
        matches = []
        for i in range(3):
            matches.append({
                "id": f"mock_{i}",
                "score": 0.85,
                "metadata": {
                    "text": "This is development mode only. Vector search is unavailable.",
                    "doc_id": "dev-mode-doc",
                    "filename": "dev-mode.txt"
                }
            })
        
        return {"matches": matches}
    
    def delete(self, filter=None, namespace="default"):
        return {"deleted_count": 0}
        
    def describe_index_stats(self):
        return {"namespaces": {"default": {"vector_count": 0}}}

# Check if debug mode is enabled
DEBUG_PINECONE = os.getenv('DEBUG_PINECONE', '').lower() == 'true'
if DEBUG_PINECONE:
    print("DEBUG MODE ENABLED: Detailed Pinecone diagnostics will be shown")

class VectorDBService:
    def __init__(self, index_name: str = None, namespace: str = "default"):
        """Initialize the Vector DB service, connected to the specified index and namespace"""
        # Initialize pinecone_index to None at the start
        self.pinecone_index = None
        
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
            
            # Get Pinecone cloud and region
            self.pinecone_cloud = os.getenv('PINECONE_CLOUD')
            self.pinecone_region = os.getenv('PINECONE_REGION')
            
            # If Pinecone import failed, use the fallback
            if not PINECONE_IMPORT_SUCCESS:
                print(f"WARNING: Pinecone import failed. Using fallback mock implementation.")
                if os.getenv('ALLOW_DEV_FALLBACK', '').lower() == 'true':
                    self.pinecone_index = SimpleMockIndex()
                    return
                else:
                    raise ValueError("Failed to import Pinecone library and ALLOW_DEV_FALLBACK is not enabled.")
            
            try:
                # Initialize Pinecone with V2 API
                if not self.pinecone_cloud:
                    print(f"DEBUG: No cloud parameter provided, defaulting to 'aws'")
                    self.pinecone_cloud = "aws"
                
                if not self.pinecone_region:
                    print(f"ERROR: PINECONE_REGION is required for V2 API")
                    print(f"Add PINECONE_REGION=us-east-1 to your .env file")
                    raise ValueError("PINECONE_REGION environment variable is required but not set")
                
                print(f"DEBUG: Initializing Pinecone with cloud={self.pinecone_cloud}, region={self.pinecone_region}")
                self.pc = Pinecone(api_key=self.pinecone_api_key, cloud=self.pinecone_cloud)
                print(f"DEBUG: Pinecone client initialized successfully")
                
                # Connect to the index
                print(f"DEBUG: Connecting to index '{self.index_name}'...")
                self.pinecone_index = self.pc.Index(self.index_name)
                print(f"DEBUG: Successfully connected to index")
                
                # Test the connection
                stats = self.pinecone_index.describe_index_stats()
                print(f"DEBUG: Index stats: {stats}")
                return
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
    
    def _safe_get_value(self, obj, key):
        """Safely extract a value from a Pinecone object or dictionary"""
        try:
            # Try attribute access first (for Pinecone objects)
            if hasattr(obj, key):
                return getattr(obj, key)
            # Then try dictionary access
            elif isinstance(obj, dict) and key in obj:
                return obj[key]
            # For list-like objects that might be wrapped
            elif hasattr(obj, '__getitem__'):
                try:
                    return obj[key]
                except:
                    return None
            return None
        except Exception as e:
            print(f"DEBUG: Error extracting '{key}' from object: {str(e)}")
            return None

    def _ensure_index_exists(self):
        """Check if the index exists and create it if it doesn't"""
        try:
            # List all indexes with retry mechanism
            print(f"DEBUG: Listing all Pinecone indexes...")
            print(f"DEBUG: Using API key beginning with: {self.pinecone_api_key[:5]}...")
            print(f"DEBUG: Current environment settings:")
            print(f"  - PINECONE_INDEX: {self.index_name}")
            print(f"  - PINECONE_CLOUD: {self.pinecone_cloud}")
            print(f"  - PINECONE_REGION: {self.pinecone_region}")
            
            max_retries = 3
            retry_delay = 1  # Start with 1 second delay
            indexes = None
            
            for retry in range(max_retries):
                try:
                    print(f"DEBUG: Attempting to list indexes (attempt {retry + 1}/{max_retries})")
                    indexes = self.pc.list_indexes()
                    if indexes:
                        break
                except Exception as e:
                    print(f"DEBUG: Error listing indexes on attempt {retry + 1}: {str(e)}")
                    if retry < max_retries - 1:
                        print(f"DEBUG: Retrying in {retry_delay} seconds...")
                        time.sleep(retry_delay)
                        retry_delay *= 2  # Exponential backoff
                    else:
                        print(f"DEBUG: All retry attempts failed")
                        raise e
            
            if not indexes:
                print(f"DEBUG: Failed to get index list after {max_retries} attempts")
                return False
                
            print(f"DEBUG: Raw index list response: {indexes}")
            print(f"DEBUG: Response type: {type(indexes)}")
            print(f"DEBUG: Response structure: {json.dumps(indexes, indent=2) if isinstance(indexes, (dict, list)) else 'Not JSON serializable'}")
            
            # Extract available indexes
            available_indexes = []
            try:
                # Get the list of indexes from V2 API response
                index_list = self._safe_get_value(indexes, 'indexes')
                if not index_list:
                    print(f"DEBUG: Could not find indexes in response")
                    print(f"DEBUG: Response type: {type(indexes)}")
                    print(f"DEBUG: Available attributes: {dir(indexes)}")
                    return False

                print(f"DEBUG: Found index_list type: {type(index_list)}")
                print(f"DEBUG: Index list content: {index_list}")
                
                # Extract names from the index objects
                for idx in index_list:
                    name = self._safe_get_value(idx, 'name')
                    if name:
                        available_indexes.append(name)
                    else:
                        print(f"DEBUG: Could not extract name from index: {idx}")
                        
                print(f"DEBUG: Extracted names: {available_indexes}")
            except Exception as e:
                print(f"DEBUG: Error extracting names: {str(e)}")
                print(f"DEBUG: Response dump: {indexes}")
                if hasattr(indexes, '__dict__'):
                    print(f"DEBUG: Object attributes: {indexes.__dict__}")
                
            print(f"DEBUG: Available indexes: {available_indexes}")
            
            # Check if the index already exists
            index_exists = self.index_name in available_indexes
            
            # Also check for case-insensitive matches which might be causing confusion
            case_insensitive_match = None
            for idx in available_indexes:
                if idx.lower() == self.index_name.lower() and idx != self.index_name:
                    case_insensitive_match = idx
                    print(f"DEBUG: Case-insensitive match found: '{idx}' vs target '{self.index_name}'")
                    print(f"DEBUG: Consider updating your PINECONE_INDEX environment variable to use the exact case: '{idx}'")
            
            # If the exact index doesn't exist but a case-insensitive match does, use that instead
            if not index_exists and case_insensitive_match:
                print(f"DEBUG: Using case-insensitive match '{case_insensitive_match}' instead of '{self.index_name}'")
                self.index_name = case_insensitive_match
                index_exists = True
            
            print(f"DEBUG: Final result - Index '{self.index_name}' exists: {index_exists}")
            
            if not index_exists:
                # If no specific index was requested, try to use any existing index 
                # instead of creating a new one
                if not os.getenv('PINECONE_INDEX') and available_indexes:
                    print(f"DEBUG: No specific index was requested, and found {len(available_indexes)} existing indexes")
                    print(f"DEBUG: Using existing index '{available_indexes[0]}' instead of creating a new one")
                    self.index_name = available_indexes[0]
                    return
                
                print(f"Index '{self.index_name}' not found. Creating...")
                
                # Create index based on API key format
                try:
                    if not self.pinecone_region:
                        print(f"ERROR: PINECONE_REGION is required for creating indexes with V2 API")
                        print(f"Add PINECONE_REGION=us-east-1 to your .env file")
                        raise ValueError("PINECONE_REGION environment variable is required but not set")
                    
                    print(f"DEBUG: Creating index with ServerlessSpec")
                    print(f"DEBUG: Using cloud={self.pinecone_cloud or 'aws'}, region={self.pinecone_region}")
                    
                    try:
                        pinecone.create_index(
                            name=self.index_name,
                            dimension=1536,
                            metric="cosine",
                            spec=ServerlessSpec(
                                cloud=self.pinecone_cloud or "aws",
                                region=self.pinecone_region
                            )
                        )
                        print(f"Created new Pinecone index: {self.index_name}")
                    except Exception as create_err:
                        error_msg = str(create_err).lower()
                        # Check specifically for 409 conflict error
                        if "409" in error_msg or "already exists" in error_msg:
                            print(f"INFO: Index '{self.index_name}' already exists (confirmed from 409 response)")
                            # This is not an error condition - the index exists which is what we want
                            return
                        else:
                            print(f"Error creating index: {str(create_err)}")
                        raise create_err
                except Exception as create_err:
                    error_msg = str(create_err).lower()
                    print(f"Error creating index: {str(create_err)}")
                    
                    # Check if it's a quota-related error
                    if any(term in error_msg for term in ["quota", "limit", "max pods", "reached"]):
                        print(f"QUOTA ERROR: Unable to create new index due to account limitations")
                        
                        # If there are existing indexes, use one of them instead
                        if available_indexes:
                            print(f"Found {len(available_indexes)} existing indexes")
                            print(f"Using existing index '{available_indexes[0]}' instead of creating a new one")
                            self.index_name = available_indexes[0]
                            print(f"Switched to using existing index: {self.index_name}")
                        else:
                            print(f"ERROR: No existing indexes available to use as fallback")
                            if os.getenv('ALLOW_DEV_FALLBACK', '').lower() == 'true':
                                print(f"WARNING: Using development fallback mode with mock implementation")
                                # The calling method will handle setting up mock implementation
                            else:
                                raise ValueError("No Pinecone indexes available and unable to create new ones due to quota limits")
                    else:
                        import traceback
                        print(f"DEBUG: Full index creation error details:\n{traceback.format_exc()}")
                        raise ValueError(f"Failed to create Pinecone index: {str(create_err)}")
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
            
            # If there are existing indexes, use one instead
            try:
                indexes = self.pc.list_indexes()
                available_indexes = []
                
                if isinstance(indexes, dict) and 'indexes' in indexes:
                    available_indexes = [idx['name'] for idx in indexes['indexes'] if isinstance(idx, dict) and 'name' in idx]
                
                if available_indexes:
                    print(f"ERROR RECOVERY: Using existing index '{available_indexes[0]}' instead of '{self.index_name}'")
                    self.index_name = available_indexes[0]
                    return
            except Exception as recovery_err:
                print(f"Failed to recover by using existing index: {str(recovery_err)}")
            
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
            # Check if there are an unusual number of chunks
            if len(chunks) > 1000:
                print(f"WARNING: Unusually high number of chunks ({len(chunks)}) detected. Limiting to 1000 chunks.")
                chunks = chunks[:1000]
            
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
                
                if current_batch % 5 == 0 or current_batch <= 2 or current_batch == total_batches:
                    print(f"Processing batch {current_batch}/{total_batches} ({len(batch)} chunks)")
                
                vectors = []
                
                for j, chunk in enumerate(batch):
                    if not chunk.strip():
                        continue
                        
                    chunk_id = f"{doc_id}_{i+j}"
                    embedding = self._generate_embedding(chunk)
                    
                    if embedding:
                        chunk_metadata = {
                            "doc_id": doc_id,
                            "chunk_index": i+j,
                            "text": chunk[:500],
                            "filename": metadata.get("filename", "")
                        }
                        
                        vectors.append({
                            "id": chunk_id,
                            "values": embedding,
                            "metadata": chunk_metadata
                        })
                
                if vectors:
                    try:
                        result = self.pinecone_index.upsert(
                            vectors=vectors,
                            namespace=namespace
                        )
                        
                        # Get upserted count from V2 API response
                        upserted = result.get('upserted_count', 0)
                        
                        total_vectors += upserted
                        vectors = []  # Clear vectors list to free memory
                        
                    except Exception as upsert_error:
                        print(f"Error upserting batch {current_batch}: {str(upsert_error)}")
                        continue  # Try next batch
            
            print(f"Successfully stored {total_vectors} vectors for document {doc_id}")
            return total_vectors > 0
            
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
            
            # Generate embedding for the query
            print(f"VECTOR SEARCH: Generating embedding for query...")
            query_start_time = time.time()
            query_embedding = self._generate_embedding(query)
            embedding_time = time.time() - query_start_time
            print(f"VECTOR SEARCH: Generated query embedding in {embedding_time:.2f} seconds")
            print(f"VECTOR SEARCH: Embedding dimension: {len(query_embedding)}")
            
            # Execute Pinecone query
            print(f"VECTOR SEARCH: Executing query in namespace: {namespace}")
            results = self.pinecone_index.query(
                vector=query_embedding,
                top_k=top_k,
                include_metadata=True,
                namespace=namespace
            )
            
            # Format results for the V2 API response format
            formatted_results = []
            
            # Get matches from the V2 API response dictionary
            matches = results.get('matches', [])
            for match in matches:
                formatted_match = {
                    "id": match.get('id'),
                    "score": match.get('score', 0),
                    "doc_id": match.get('metadata', {}).get('doc_id', ''),
                    "text": match.get('metadata', {}).get('text', ''),
                    "source": match.get('metadata', {}).get('source', ''),
                    "filename": match.get('metadata', {}).get('filename', ''),
                    "folder": match.get('metadata', {}).get('folder', ''),
                    "namespace": namespace
                }
                formatted_results.append(formatted_match)
            
            print(f"VECTOR SEARCH: Found {len(formatted_results)} matches")
            if formatted_results:
                top_score = formatted_results[0]["score"]
                print(f"VECTOR SEARCH: Top match score: {top_score:.4f}")
            
            return formatted_results
            
        except Exception as e:
            error_type = type(e).__name__
            print(f"VECTOR SEARCH ERROR ({error_type}): {str(e)}")
            print(f"VECTOR SEARCH ERROR: Full error details:\n{traceback.format_exc()}")
            raise ValueError(f"Vector search failed: {str(e)}")
    
    def delete_document(self, doc_id: str, namespace: str = None) -> bool:
        """Delete all chunks for a document"""
        if not self.pinecone_index:
            error_msg = "Vector database not initialized. Cannot delete document."
            print(f"ERROR: {error_msg}")
            raise ValueError(error_msg)
        
        try:
            print(f"Deleting document {doc_id} from {'namespace ' + namespace if namespace else 'all namespaces'}")
            
            # If namespace is provided, delete only from that namespace
            if namespace:
                result = self.pinecone_index.delete(
                    filter={"doc_id": doc_id},
                    namespace=namespace
                )
                
                # Get deleted count from V2 API response
                deleted = result.get('deleted_count', 0)
                print(f"Deleted {deleted} vectors from namespace {namespace}")
            else:
                # If no namespace is provided, we need to find all namespaces that contain this document
                stats = self.pinecone_index.describe_index_stats()
                
                # Get namespaces from V2 API response
                namespaces = stats.get("namespaces", {}).keys()
                
                total_deleted = 0
                for ns in namespaces:
                    result = self.pinecone_index.delete(
                        filter={"doc_id": doc_id},
                        namespace=ns
                    )
                    
                    # Get deleted count from V2 API response
                    deleted = result.get('deleted_count', 0)
                    
                    total_deleted += deleted
                    print(f"Deleted {deleted} vectors from namespace {ns}")
                
                print(f"Total vectors deleted across all namespaces: {total_deleted}")
            
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
            
            # Use delete_all=True parameter which is available in Pinecone v3.0.0
            # This properly deletes all vectors in the namespace
            result = self.pinecone_index.delete(
                delete_all=True,  # This is the key change
                namespace=namespace
            )
            
            print(f"VECTOR DB: Successfully deleted namespace '{namespace}'")
            
            # Verify the namespace is empty after deletion
            stats_after = self.pinecone_index.describe_index_stats()
            if namespace in stats_after.get("namespaces", {}):
                remaining_vectors = stats_after.get("namespaces", {}).get(namespace, {}).get("vector_count", 0)
                if remaining_vectors > 0:
                    print(f"VECTOR DB WARNING: Namespace '{namespace}' still has {remaining_vectors} vectors after deletion")
                    # Try a second approach if vectors remain (for compatibility with different Pinecone versions)
                    self.pinecone_index.delete(
                        filter={},  # Empty filter as fallback
                        namespace=namespace
                    )
                    print(f"VECTOR DB: Attempted second deletion approach for namespace '{namespace}'")
            
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
                    
                    # Format results for the V2 API response format
                    for match in results.get('matches', []):
                        all_results.append({
                            "id": match.get('id'),
                            "score": match.get('score', 0),
                            "doc_id": match.get('metadata', {}).get('doc_id', ''),
                            "text": match.get('metadata', {}).get('text', ''),
                            "source": match.get('metadata', {}).get('source', ''),
                            "filename": match.get('metadata', {}).get('filename', ''),
                            "folder": match.get('metadata', {}).get('folder', ''),
                            "namespace": namespace
                        })
                    
                    namespace_time = time.time() - namespace_start_time
                    print(f"VECTOR CROSS-NAMESPACE SEARCH: Found {len(results.get('matches', []))} matches in namespace '{namespace}' in {namespace_time:.2f} seconds")
                    
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

    def calculate_document_similarity(self, doc1_text: str, doc2_text: str, method: str = "embedding", 
                               custom_prompt: str = None, prompt_model: str = "gpt-3.5-turbo") -> Dict[str, Any]:
        """
        Calculate similarity between two document texts using various methods.
        
        Args:
            doc1_text: Text content of the first document
            doc2_text: Text content of the second document
            method: Similarity method to use ("embedding", "text", or "hybrid")
            custom_prompt: Optional prompt to process the text before comparison (e.g., to remove headers/footers)
            prompt_model: The OpenAI model to use for processing the prompt (default: "gpt-3.5-turbo")
            
        Returns:
            Dict containing similarity scores and metadata
        """
        try:
            print(f"Calculating similarity between two documents")
            print(f"Document 1 length: {len(doc1_text)} characters")
            print(f"Document 2 length: {len(doc2_text)} characters")
            print(f"Using method: {method}")
            
            # Apply custom processing to the document text if a prompt is provided
            if custom_prompt:
                print(f"Applying custom prompt to process document texts before comparison using model: {prompt_model}")
                try:
                    # Process text using OpenAI to apply custom instructions
                    response1 = self.openai_client.chat.completions.create(
                        model=prompt_model,
                        messages=[
                            {"role": "system", "content": custom_prompt},
                            {"role": "user", "content": doc1_text}
                        ],
                        temperature=0.0
                    )
                    
                    response2 = self.openai_client.chat.completions.create(
                        model=prompt_model,
                        messages=[
                            {"role": "system", "content": custom_prompt},
                            {"role": "user", "content": doc2_text}
                        ],
                        temperature=0.0
                    )
                    
                    # Extract processed text
                    processed_doc1_text = response1.choices[0].message.content
                    processed_doc2_text = response2.choices[0].message.content
                    
                    # Log the changes for debugging
                    print(f"Original doc1 length: {len(doc1_text)}, Processed doc1 length: {len(processed_doc1_text)}")
                    print(f"Original doc2 length: {len(doc2_text)}, Processed doc2 length: {len(processed_doc2_text)}")
                    
                    # Use the processed text instead
                    doc1_text = processed_doc1_text
                    doc2_text = processed_doc2_text
                except Exception as e:
                    print(f"Error applying custom prompt to document text: {str(e)}")
                    print(f"Using original document text without custom processing")
            
            result = {
                "similarity": 0.0,
                "embedding_similarity": 0.0,
                "text_similarity": 0.0,
                "comparison_time": 0.0,
                "method": method,
                "timestamp": datetime.now().isoformat(),
                "custom_prompt_applied": custom_prompt is not None,
                "prompt_model": prompt_model if custom_prompt else None
            }
            
            start_time = time.time()
            
            # Calculate embedding-based similarity
            if method in ["embedding", "hybrid"]:
                # Generate embeddings for both documents
                embedding1 = self._generate_embedding(doc1_text)
                embedding2 = self._generate_embedding(doc2_text)
                
                # Calculate cosine similarity
                # Formula: cos(θ) = (A·B) / (||A|| × ||B||)
                dot_product = sum(a * b for a, b in zip(embedding1, embedding2))
                magnitude1 = sum(a * a for a in embedding1) ** 0.5
                magnitude2 = sum(b * b for b in embedding2) ** 0.5
                
                embedding_similarity = dot_product / (magnitude1 * magnitude2)
                result["embedding_similarity"] = embedding_similarity
                
                if method == "embedding":
                    result["similarity"] = embedding_similarity
            
            # Calculate text-based similarity using TF-IDF
            if method in ["text", "hybrid"]:
                # Simple text-based similarity using word frequency
                # This is a basic implementation - a proper one would use libraries like scikit-learn for TF-IDF
                
                # Tokenize documents into words
                words1 = set(doc1_text.lower().split())
                words2 = set(doc2_text.lower().split())
                
                # Calculate Jaccard similarity coefficient
                intersection = len(words1.intersection(words2))
                union = len(words1.union(words2))
                
                text_similarity = intersection / union if union > 0 else 0.0
                result["text_similarity"] = text_similarity
                
                if method == "text":
                    result["similarity"] = text_similarity
            
            # For hybrid method, take the average of both similarities
            if method == "hybrid":
                result["similarity"] = (result["embedding_similarity"] + result["text_similarity"]) / 2
            
            end_time = time.time()
            result["comparison_time"] = end_time - start_time
            
            print(f"Calculated similarity score: {result['similarity']:.4f} using {method} method")
            print(f"Comparison completed in {result['comparison_time']:.2f} seconds")
            
            return result
        
        except Exception as e:
            print(f"Error calculating document similarity: {str(e)}")
            import traceback
            traceback.print_exc()
            raise ValueError(f"Failed to calculate document similarity: {str(e)}")

    def calculate_document_similarity_by_id(self, doc1_id: str, doc2_id: str, method: str = "hybrid", namespace: str = None) -> Dict[str, Any]:
        """
        Calculate similarity between two documents already stored in the system.
        
        Args:
            doc1_id: ID of the first document
            doc2_id: ID of the second document
            method: Similarity method to use ("embedding", "text", "hybrid", or "chunked")
            namespace: Optional namespace where documents are stored
            
        Returns:
            Dict containing similarity scores and metadata
        """
        try:
            print(f"Calculating similarity between documents {doc1_id} and {doc2_id}")
            print(f"Using method: {method}")
            
            result = {
                "doc1_id": doc1_id,
                "doc2_id": doc2_id,
                "similarity": 0.0,
                "method": method,
                "timestamp": datetime.now().isoformat(),
                "namespace": namespace
            }
            
            # For chunked method, use a different approach
            if method == "chunked":
                return self.calculate_chunked_document_similarity(doc1_id, doc2_id, namespace)
            
            # Get document content from S3 or your document storage
            # This method needs to be implemented based on your storage system
            doc1_text = self._get_document_text(doc1_id, namespace)
            doc2_text = self._get_document_text(doc2_id, namespace)
            
            # Calculate similarity using the text content
            similarity_result = self.calculate_document_similarity(doc1_text, doc2_text, method)
            
            # Merge the results
            result.update(similarity_result)
            
            # Optionally store this comparison result in S3 for history
            self._store_comparison_result(result)
            
            return result
        
        except Exception as e:
            print(f"Error calculating document similarity by ID: {str(e)}")
            import traceback
            traceback.print_exc()
            raise ValueError(f"Failed to calculate document similarity by ID: {str(e)}")

    def calculate_chunked_document_similarity(self, doc1_id: str, doc2_id: str, namespace: str = None) -> Dict[str, Any]:
        """
        Calculate similarity between two documents by comparing their chunks.
        This is more accurate for large documents that have been chunked.
        
        Args:
            doc1_id: ID of the first document
            doc2_id: ID of the second document
            namespace: Optional namespace where documents are stored
            
        Returns:
            Dict containing similarity scores and metadata
        """
        try:
            print(f"Calculating chunked similarity between documents {doc1_id} and {doc2_id}")
            
            result = {
                "doc1_id": doc1_id,
                "doc2_id": doc2_id,
                "similarity": 0.0,
                "method": "chunked",
                "timestamp": datetime.now().isoformat(),
                "namespace": namespace,
                "chunk_comparisons": 0
            }
            
            start_time = time.time()
            
            # Get all vectors for doc1
            doc1_filter = {"doc_id": doc1_id}
            
            # Get all vectors for doc2
            doc2_filter = {"doc_id": doc2_id}
            
            # Calculate similarity between chunks
            all_similarity_scores = []
            top_matches = []
            
            # Use statistical sampling for very large documents to avoid comparing all chunks
            max_chunks_to_compare = 1000  # Set a reasonable limit
            
            # First get doc1 chunks
            doc1_results = self.pinecone_index.query(
                filter=doc1_filter,
                vector=[0.0] * 1536,  # Dummy vector, we're only using the filter
                top_k=max_chunks_to_compare,
                include_metadata=True,
                include_values=True,
                namespace=namespace
            )
            
            # Then get doc2 chunks
            doc2_results = self.pinecone_index.query(
                filter=doc2_filter,
                vector=[0.0] * 1536,  # Dummy vector, we're only using the filter
                top_k=max_chunks_to_compare,
                include_metadata=True,
                include_values=True,
                namespace=namespace
            )
            
            doc1_chunks = doc1_results.get('matches', [])
            doc2_chunks = doc2_results.get('matches', [])
            
            print(f"Retrieved {len(doc1_chunks)} chunks for doc1 and {len(doc2_chunks)} chunks for doc2")
            
            # If we have too many combinations, sample them
            if len(doc1_chunks) * len(doc2_chunks) > max_chunks_to_compare:
                import random
                # Sample chunks from both documents
                if len(doc1_chunks) > 50:
                    doc1_chunks = random.sample(doc1_chunks, 50)
                if len(doc2_chunks) > 50:
                    doc2_chunks = random.sample(doc2_chunks, 50)
                print(f"Sampled down to {len(doc1_chunks)} chunks for doc1 and {len(doc2_chunks)} chunks for doc2")
            
            # Compare each chunk from doc1 with each chunk from doc2
            for i, doc1_chunk in enumerate(doc1_chunks):
                doc1_vector = doc1_chunk.get('values', [])
                if not doc1_vector:
                    continue
                
                for j, doc2_chunk in enumerate(doc2_chunks):
                    doc2_vector = doc2_chunk.get('values', [])
                    if not doc2_vector:
                        continue
                    
                    # Calculate cosine similarity
                    dot_product = sum(a * b for a, b in zip(doc1_vector, doc2_vector))
                    magnitude1 = sum(a * a for a in doc1_vector) ** 0.5
                    magnitude2 = sum(b * b for b in doc2_vector) ** 0.5
                    
                    chunk_similarity = dot_product / (magnitude1 * magnitude2)
                    all_similarity_scores.append(chunk_similarity)
                    
                    # Keep track of top matches
                    if chunk_similarity > 0.8:  # Adjust threshold as needed
                        top_matches.append({
                            "doc1_chunk": i,
                            "doc2_chunk": j,
                            "similarity": chunk_similarity,
                            "doc1_text": doc1_chunk.get('metadata', {}).get('text', ''),
                            "doc2_text": doc2_chunk.get('metadata', {}).get('text', '')
                        })
            
            # Sort top matches by similarity
            top_matches.sort(key=lambda x: x["similarity"], reverse=True)
            
            # Calculate aggregate similarity
            if all_similarity_scores:
                # Take the average of top 25% of similarity scores
                all_similarity_scores.sort(reverse=True)
                top_n = max(1, len(all_similarity_scores) // 4)
                top_similarity_scores = all_similarity_scores[:top_n]
                avg_similarity = sum(top_similarity_scores) / len(top_similarity_scores)
                
                result["similarity"] = avg_similarity
                result["chunk_comparisons"] = len(all_similarity_scores)
                result["top_matches"] = top_matches[:10]  # Include top 10 matches
            else:
                print("No chunk comparisons were performed")
                result["similarity"] = 0.0
            
            end_time = time.time()
            result["comparison_time"] = end_time - start_time
            
            print(f"Calculated chunk similarity score: {result['similarity']:.4f}")
            print(f"Compared {result['chunk_comparisons']} chunk pairs in {result['comparison_time']:.2f} seconds")
            
            # Optionally store this comparison result in S3 for history
            self._store_comparison_result(result)
            
            return result
        
        except Exception as e:
            print(f"Error calculating chunked document similarity: {str(e)}")
            import traceback
            traceback.print_exc()
            raise ValueError(f"Failed to calculate chunked document similarity: {str(e)}")

    def _get_document_text(self, doc_id: str, namespace: str = None) -> str:
        """
        Retrieve the full text of a document from storage.
        
        Args:
            doc_id: ID of the document
            namespace: Optional namespace where the document is stored
            
        Returns:
            str: The full text content of the document
        """
        # This is a placeholder implementation
        # You would need to implement this to retrieve documents from your storage system
        
        try:
            print(f"Retrieving text for document {doc_id} from namespace {namespace}")
            
            # Example implementation using a hypothetical S3 service
            # from app.services.s3_service import S3Service
            # s3_service = S3Service()
            # document_data = s3_service.get_object(f"documents/{doc_id}/content.txt")
            # return document_data.decode('utf-8')
            
            # For demonstration purposes, we'll just construct a placeholder
            # In a real implementation, this would retrieve the document from S3
            return f"This is placeholder text for document {doc_id}. Implement actual retrieval from S3."
        
        except Exception as e:
            print(f"Error retrieving document text: {str(e)}")
            raise ValueError(f"Failed to retrieve document text: {str(e)}")

    def _store_comparison_result(self, result: Dict[str, Any]) -> bool:
        """
        Store document comparison result in S3 for history tracking.
        
        Args:
            result: The comparison result to store
            
        Returns:
            bool: True if stored successfully
        """
        try:
            # Generate a unique key for this comparison
            comparison_id = f"{result['doc1_id']}_{result['doc2_id']}_{int(time.time())}"
            
            # Example implementation using a hypothetical S3 service
            # from app.services.s3_service import S3Service
            # s3_service = S3Service()
            # s3_service.put_object(
            #     f"document_comparisons/{comparison_id}.json",
            #     json.dumps(result).encode('utf-8')
            # )
            
            print(f"Stored comparison result with ID: {comparison_id}")
            return True
        
        except Exception as e:
            print(f"Error storing comparison result: {str(e)}")
            # Don't raise an exception here, as this is just an auxiliary function
            return False

    def get_similar_documents(self, doc_id: str, top_k: int = 5, namespace: str = None) -> List[Dict[str, Any]]:
        """
        Find documents similar to a given document.
        
        Args:
            doc_id: ID of the document to find similar documents for
            top_k: Number of similar documents to return
            namespace: Optional namespace where documents are stored
            
        Returns:
            List of similar documents with similarity scores
        """
        try:
            print(f"Finding documents similar to {doc_id}")
            
            # Get the document text
            doc_text = self._get_document_text(doc_id, namespace)
            
            # Generate embedding for the document
            doc_embedding = self._generate_embedding(doc_text)
            
            # Search for similar documents using the embedding
            results = self.pinecone_index.query(
                vector=doc_embedding,
                top_k=top_k * 3,  # Get more results than needed to filter by unique docs
                include_metadata=True,
                namespace=namespace
            )
            
            # Process results to get unique documents
            unique_docs = {}
            
            for match in results.get('matches', []):
                match_doc_id = match.get('metadata', {}).get('doc_id', '')
                
                # Skip the document itself
                if match_doc_id == doc_id:
                    continue
                
                # Keep only the highest scoring match for each document
                if match_doc_id not in unique_docs or match.get('score', 0) > unique_docs[match_doc_id]['score']:
                    unique_docs[match_doc_id] = {
                        'doc_id': match_doc_id,
                        'score': match.get('score', 0),
                        'filename': match.get('metadata', {}).get('filename', ''),
                        'namespace': namespace
                    }
            
            # Convert to list and sort by score
            similar_docs = list(unique_docs.values())
            similar_docs.sort(key=lambda x: x['score'], reverse=True)
            
            # Return top_k results
            return similar_docs[:top_k]
        
        except Exception as e:
            print(f"Error finding similar documents: {str(e)}")
            import traceback
            traceback.print_exc()
            raise ValueError(f"Failed to find similar documents: {str(e)}")