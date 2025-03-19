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
    print(f"Python version: {sys.version}")
    print(f"Python path: {sys.path}")
    
    # Print the module search path to help debug import issues
    for i, path in enumerate(sys.path):
        print(f"Path {i}: {path}")
    
    # Try importing the package directly
    import pinecone as pinecone_pkg
    print(f"Pinecone package located at: {pinecone_pkg.__file__}")
    print(f"Pinecone package version: {getattr(pinecone_pkg, '__version__', 'unknown')}")
    print(f"Pinecone package contents: {dir(pinecone_pkg)}")
    
    # Check if we have a V2 API key (starts with pcsk_)
    pinecone_api_key = os.getenv('PINECONE_API_KEY', '')
    is_v2_api_key = pinecone_api_key.startswith('pcsk_')
    
    if is_v2_api_key:
        print("V2 API key detected (pcsk_) - Forcing V2 API usage")
        # Ensure we have the V2 API class
        if hasattr(pinecone_pkg, 'Pinecone'):
            print("V2 API class found - Using direct Pinecone class")
            Pinecone = pinecone_pkg.Pinecone
            ServerlessSpec = pinecone_pkg.ServerlessSpec
            PINECONE_NEW_API = True
        else:
            print("ERROR: V2 API key detected but V2 API class not found")
            print("This likely means you need to upgrade the pinecone package")
            print("Try: pip install --upgrade pinecone-client")
            raise ImportError("V2 API key requires V2 API class (pinecone.Pinecone)")
    else:
        # For V1 API keys, we can use either version
        if hasattr(pinecone_pkg, 'Pinecone'):
            print("V2 API class found - Using new API format")
            Pinecone = pinecone_pkg.Pinecone
            ServerlessSpec = pinecone_pkg.ServerlessSpec
            PINECONE_NEW_API = True
        elif hasattr(pinecone_pkg, 'init'):
            print("V1 API detected - Using module as client")
            # Create class adapters for backwards compatibility
            class PineconeAdapter:
                def __init__(self, api_key, **kwargs):
                    print("Using adapter for V1 Pinecone API")
                    self.api_key = api_key
                    # Initialize the V1 client
                    if 'environment' in kwargs:
                        pinecone_pkg.init(api_key=api_key, environment=kwargs['environment'])
                    else:
                        pinecone_pkg.init(api_key=api_key)
                
                def Index(self, index_name):
                    print(f"Getting index '{index_name}' with V1 API")
                    return pinecone_pkg.Index(name=index_name)
                
                def list_indexes(self):
                    print("Listing indexes with V1 API")
                    indexes = pinecone_pkg.list_indexes()
                    # Convert to V2 format
                    return {"indexes": [{"name": idx} for idx in indexes]}
                
                def create_index(self, name, dimension, metric, **kwargs):
                    print(f"Creating index '{name}' with V1 API")
                    # Extract environment from kwargs if present
                    env = kwargs.get('environment', None)
                    if env:
                        return pinecone_pkg.create_index(name=name, dimension=dimension, metric=metric, environment=env)
                    else:
                        return pinecone_pkg.create_index(name=name, dimension=dimension, metric=metric)
            
            class ServerlessSpecAdapter:
                def __init__(self, cloud, region):
                    self.cloud = cloud
                    self.region = region
            
            # Assign the adapter classes
            Pinecone = PineconeAdapter
            ServerlessSpec = ServerlessSpecAdapter
            print("Successfully created Pinecone adapter for V1 API")
            PINECONE_NEW_API = False
        else:
            print("WARNING: Unknown Pinecone API version - neither V1 nor V2 detected")
            # Try the regular import as last resort
            from pinecone import Pinecone, ServerlessSpec
            print("Successfully imported Pinecone via from...import")
            PINECONE_NEW_API = True
        
    PINECONE_IMPORT_SUCCESS = True
    print("Successfully imported pinecone package")
    
    # Print the imported Pinecone version to help with debugging
    import importlib.metadata
    try:
        pinecone_version = importlib.metadata.version("pinecone")
        print(f"Imported Pinecone version: {pinecone_version}")
    except Exception as ver_error:
        try:
            pinecone_version = importlib.metadata.version("pinecone-client")
            print(f"Imported Pinecone-client version: {pinecone_version}")
        except Exception:
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
    PINECONE_NEW_API = False
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
    PINECONE_NEW_API = False
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
            
            # Get Pinecone cloud, region and environment if set
            self.pinecone_cloud = os.getenv('PINECONE_CLOUD')
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
            if PINECONE_NEW_API:
                # New API format returns an IndexList object
                try:
                    # Get the list of indexes using our safe helper
                    index_list = self._safe_get_value(indexes, 'indexes')
                    if not index_list:
                        print(f"DEBUG: V2 API - Could not find indexes in response")
                        print(f"DEBUG: V2 API - Response type: {type(indexes)}")
                        print(f"DEBUG: V2 API - Available attributes: {dir(indexes)}")
                        return False

                    print(f"DEBUG: V2 API - Found index_list type: {type(index_list)}")
                    print(f"DEBUG: V2 API - Index list content: {index_list}")
                    
                    # Extract names from the index objects
                    for idx in index_list:
                        name = self._safe_get_value(idx, 'name')
                        if name:
                            available_indexes.append(name)
                        else:
                            print(f"DEBUG: V2 API - Could not extract name from index: {idx}")
                            
                    print(f"DEBUG: V2 API - Extracted names: {available_indexes}")
                except Exception as e:
                    print(f"DEBUG: V2 API - Error extracting names: {str(e)}")
                    print(f"DEBUG: V2 API - Response dump: {indexes}")
                    if hasattr(indexes, '__dict__'):
                        print(f"DEBUG: V2 API - Object attributes: {indexes.__dict__}")
                else:
                    print(f"DEBUG: V2 API - Unexpected response format:")
                    print(f"  - Is dict? {isinstance(indexes, dict)}")
                    print(f"  - Has 'indexes' key? {'indexes' in indexes if isinstance(indexes, dict) else False}")
                    print(f"  - Available keys: {indexes.keys() if isinstance(indexes, dict) else 'N/A'}")
            else:
                # Old API returns a list of string names
                if isinstance(indexes, list):
                    print(f"DEBUG: V1 API - Found list type response")
                    print(f"DEBUG: V1 API - List items types: {[type(idx) for idx in indexes]}")
                    available_indexes = indexes
                # For adapter case, also check dict format
                elif isinstance(indexes, dict) and 'indexes' in indexes:
                    index_list = indexes['indexes']
                    print(f"DEBUG: V1 Adapter - Found index_list type: {type(index_list)}")
                    print(f"DEBUG: V1 Adapter - Index list content: {index_list}")
                    try:
                        available_indexes = [idx['name'] for idx in index_list if isinstance(idx, dict) and 'name' in idx]
                        print(f"DEBUG: V1 Adapter - Extracted names: {available_indexes}")
                    except Exception as e:
                        print(f"DEBUG: V1 Adapter - Error extracting names: {str(e)}")
                else:
                    print(f"DEBUG: V1 API - Unexpected response format:")
                    print(f"  - Response type: {type(indexes)}")
                    print(f"  - Content: {indexes}")
            
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
                
                # Create index based on API key format and API version
                try:
                    if self.is_new_api_key:
                        if not self.pinecone_region:
                            print(f"ERROR: PINECONE_REGION is required for creating indexes with new API keys")
                            print(f"Add PINECONE_REGION=us-east-1 to your .env file")
                            raise ValueError("PINECONE_REGION environment variable is required but not set")
                        
                        print(f"DEBUG: Creating index with {'ServerlessSpec' if PINECONE_NEW_API else 'environment'} for new API key format")
                        print(f"DEBUG: Using cloud={self.pinecone_cloud or 'aws'}, region={self.pinecone_region}")
                        
                        try:
                            if PINECONE_NEW_API:
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
                                # Old API format
                                self.pc.create_index(
                                    name=self.index_name,
                                    dimension=1536,
                                    metric="cosine"
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
                    else:
                        print(f"DEBUG: Creating index for old API key format")
                        if PINECONE_NEW_API:
                            self.pc.create_index(
                                name=self.index_name,
                                dimension=1536,
                                metric="cosine"
                            )
                        else:
                            # Old API direct call
                            self.pc.create_index(
                                name=self.index_name,
                                dimension=1536,
                                metric="cosine"
                            )
                            
                        print(f"Created new Pinecone index: {self.index_name}")
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
                
                if PINECONE_NEW_API:
                    if isinstance(indexes, dict) and 'indexes' in indexes:
                        available_indexes = [idx['name'] for idx in indexes['indexes'] if isinstance(idx, dict) and 'name' in idx]
                else:
                    if isinstance(indexes, list):
                        available_indexes = indexes
                    elif isinstance(indexes, dict) and 'indexes' in indexes:
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
                        
                        # Handle both V1 and V2 API responses
                        if isinstance(result, dict):
                            # V2 API response
                            upserted = result.get('upserted_count', 0)
                        else:
                            # V1 API response
                            upserted = getattr(result, 'upserted_count', 0)
                        
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
            
            # Check if we got a V2 API response (dictionary) or V1 API response (object with matches attribute)
            if isinstance(results, dict):
                # V2 API response
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
            else:
                # V1 API or Mock response (object with matches attribute)
                for match in getattr(results, 'matches', []):
                    formatted_match = {
                        "id": match.id,
                        "score": match.score,
                        "doc_id": match.metadata.get("doc_id", ""),
                        "text": match.metadata.get("text", ""),
                        "source": match.metadata.get("source", ""),
                        "filename": match.metadata.get("filename", ""),
                        "folder": match.metadata.get("folder", ""),
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
                
                # Handle both V1 and V2 API responses
                if isinstance(result, dict):
                    # V2 API response
                    deleted = result.get('deleted_count', 0)
                else:
                    # V1 API response
                    deleted = getattr(result, 'deleted_count', 0)
                
                print(f"Deleted {deleted} vectors from namespace {namespace}")
            else:
                # If no namespace is provided, we need to find all namespaces that contain this document
                stats = self.pinecone_index.describe_index_stats()
                
                # Handle both V1 and V2 API responses for stats
                if isinstance(stats, dict):
                    # V2 API response
                    namespaces = stats.get("namespaces", {}).keys()
                else:
                    # V1 API response
                    namespaces = getattr(stats, "namespaces", {}).keys()
                
                total_deleted = 0
                for ns in namespaces:
                    result = self.pinecone_index.delete(
                        filter={"doc_id": doc_id},
                        namespace=ns
                    )
                    
                    # Handle both V1 and V2 API responses
                    if isinstance(result, dict):
                        # V2 API response
                        deleted = result.get('deleted_count', 0)
                    else:
                        # V1 API response
                        deleted = getattr(result, 'deleted_count', 0)
                    
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