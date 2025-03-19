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
    
    # First try with v2 format (direct attribute)
    if hasattr(pinecone_pkg, 'Pinecone'):
        print("V2 API detected - Importing Pinecone class from module directly")
        Pinecone = pinecone_pkg.Pinecone
        ServerlessSpec = pinecone_pkg.ServerlessSpec
        print("Successfully imported Pinecone class from module attributes")
        PINECONE_NEW_API = True
    # Then try with v1 format (using the module as the client)
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

# Check if debug mode is enabled
DEBUG_PINECONE = os.getenv('DEBUG_PINECONE', '').lower() == 'true'
if DEBUG_PINECONE:
    print("DEBUG MODE ENABLED: Detailed Pinecone diagnostics will be shown")

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
                
                # Initialize Pinecone based on which API version we're using
                if self.is_new_api_key:
                    print(f"DEBUG: Using new API key format with {'new' if PINECONE_NEW_API else 'old'} API client")
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
                    
                    # List all indexes with retry mechanism
                    print(f"DEBUG: Listing all Pinecone indexes...")
                    print(f"DEBUG: Using API key beginning with: {self.pinecone_api_key[:5]}...")
                    print(f"DEBUG: Current environment settings:")
                    print(f"  - PINECONE_INDEX: {self.index_name}")
                    print(f"  - PINECONE_CLOUD: {self.pinecone_cloud}")
                    print(f"  - PINECONE_REGION: {self.pinecone_region}")
                    print(f"  - PINECONE_ENVIRONMENT: {self.pinecone_env}")
                    print(f"  - API Key Type: {'New format (pcsk_)' if self.is_new_api_key else 'Classic format'}")
                    print(f"  - API Version: {'V2 (Pinecone class)' if PINECONE_NEW_API else 'V1 (init function)'}")
                    
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
                                        metric="cosine",
                                        environment=self.pinecone_env
                                    )
                                else:
                                    # Old API direct call
                                    self.pc.create_index(
                                        name=self.index_name,
                                        dimension=1536,
                                        metric="cosine",
                                        environment=self.pinecone_env
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
            print(f"  - PINECONE_ENVIRONMENT: {self.pinecone_env}")
            print(f"  - API Key Type: {'New format (pcsk_)' if self.is_new_api_key else 'Classic format'}")
            print(f"  - API Version: {'V2 (Pinecone class)' if PINECONE_NEW_API else 'V1 (init function)'}")
            
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
                                metric="cosine",
                                environment=self.pinecone_env
                            )
                        else:
                            # Old API direct call
                            self.pc.create_index(
                                name=self.index_name,
                                dimension=1536,
                                metric="cosine",
                                environment=self.pinecone_env
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
                    
                    # Try to find case-insensitive match
                    namespace_lower = namespace.lower()
                    case_match = None
                    for ns in namespaces.keys():
                        if ns.lower() == namespace_lower:
                            case_match = ns
                            print(f"VECTOR SEARCH: Found case-insensitive match for namespace: '{ns}' vs requested '{namespace}'")
                            break
                    
                    if case_match:
                        print(f"VECTOR SEARCH: Using case-insensitive match '{case_match}' instead of '{namespace}'")
                        namespace = case_match
                    else:
                        # Check if we should try alternate namespaces
                        if len(namespaces) > 0:
                            available_ns = list(namespaces.keys())
                            alternative_ns = available_ns[0]
                            vector_count = namespaces[alternative_ns].get("vector_count", 0)
                            if vector_count > 0:
                                print(f"VECTOR SEARCH: Requested namespace not found, will try alternative '{alternative_ns}' with {vector_count} vectors")
                                namespace = alternative_ns
                
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
            
            # List of namespaces to try, in order
            namespaces_to_try = []
            if namespace is not None:
                namespaces_to_try.append(namespace)
            
            # If no explicit namespace, or if the specified namespace doesn't exist, 
            # add potential fallbacks
            if namespace is None or (stats and "namespaces" in stats and namespace not in stats["namespaces"]):
                # Add default namespace first
                if "default" in stats.get("namespaces", {}):
                    if "default" not in namespaces_to_try:
                        namespaces_to_try.append("default")
                
                # Then try root if it exists and has vectors
                if "root" in stats.get("namespaces", {}) and stats["namespaces"]["root"].get("vector_count", 0) > 0:
                    if "root" not in namespaces_to_try:
                        namespaces_to_try.append("root")
                
                # Last resort, try any namespace with vectors
                for ns, ns_data in stats.get("namespaces", {}).items():
                    if ns not in namespaces_to_try and ns_data.get("vector_count", 0) > 0:
                        namespaces_to_try.append(ns)
                        break  # Just add one alternative
            
            print(f"VECTOR SEARCH: Will try these namespaces in order: {namespaces_to_try}")
            
            # Initialize results
            results = None
            used_namespace = None
            
            # Try each namespace until we get results
            for ns in namespaces_to_try:
                try:
                    print(f"VECTOR SEARCH: Trying search in namespace '{ns}'...")
                    search_start_time = time.time()
                    
                    # Execute Pinecone query with retry
                    max_retries = 2
                    retry_count = 0
                    search_error = None
                    
                    while retry_count <= max_retries:
                        try:
                            # Execute Pinecone query
                            results = self.pinecone_index.query(
                                vector=query_embedding,
                                top_k=top_k,
                                include_metadata=True,
                                namespace=ns
                            )
                            search_error = None
                            break  # Success, exit retry loop
                        except Exception as query_error:
                            search_error = query_error
                            retry_count += 1
                            print(f"VECTOR SEARCH WARNING: Query attempt {retry_count} failed: {str(query_error)}")
                            if retry_count <= max_retries:
                                retry_delay = 1.0 * retry_count  # Exponential backoff
                                print(f"VECTOR SEARCH: Retrying in {retry_delay:.1f} seconds...")
                                time.sleep(retry_delay)
                            else:
                                print(f"VECTOR SEARCH ERROR: All retry attempts failed")
                    
                    # Check if we got a successful result
                    if search_error:
                        # All retries failed
                        print(f"VECTOR SEARCH ERROR: Failed to search namespace '{ns}' after {max_retries + 1} attempts")
                        continue  # Try next namespace
                    
                    search_time = time.time() - search_start_time
                    print(f"VECTOR SEARCH: Executed search in {search_time:.2f} seconds")
                    
                    # Check if we got results
                    if hasattr(results, 'matches') and len(results.matches) > 0:
                        print(f"VECTOR SEARCH: Found {len(results.matches)} matches in namespace '{ns}'")
                        used_namespace = ns
                        break  # Success, exit namespace loop
                    else:
                        print(f"VECTOR SEARCH: No matches found in namespace '{ns}', will try next namespace if available")
                
                except Exception as ns_error:
                    print(f"VECTOR SEARCH ERROR: Failed to search namespace '{ns}': {str(ns_error)}")
                    continue  # Try next namespace
            
            # Check if we got any results
            if not results or not hasattr(results, 'matches') or len(results.matches) == 0:
                print(f"VECTOR SEARCH WARNING: No results found in any namespace")
                return []
            
            print(f"VECTOR SEARCH: Using results from namespace '{used_namespace}'")
            
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
                    "folder": match.metadata.get("folder", ""),
                    "namespace": used_namespace  # Include which namespace was actually used
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