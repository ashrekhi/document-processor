from typing import List, Optional, Dict, Any
import os
import numpy as np
from openai import OpenAI
import logging
import time
import sys
import traceback

# Import Pinecone with proper handling for import errors
try:
    print("EmbeddingService: Attempting to import Pinecone...")
    
    # Import the package directly first
    import pinecone as pinecone_pkg
    print(f"EmbeddingService: Pinecone package found at {pinecone_pkg.__file__}")
    print(f"EmbeddingService: Pinecone version: {getattr(pinecone_pkg, '__version__', 'unknown')}")
    
    # Check if we have V2 API (with Pinecone class)
    if hasattr(pinecone_pkg, 'Pinecone'):
        # Import directly from the module
        from pinecone import Pinecone, ServerlessSpec
        print("EmbeddingService: Successfully imported Pinecone class (V2 API)")
        PINECONE_NEW_API = True
    # Check if we have V1 API (with init function)
    elif hasattr(pinecone_pkg, 'init'):
        print("EmbeddingService: Detected V1 API with init function")
        # Create adapter classes for compatibility
        class Pinecone:
            def __init__(self, api_key, **kwargs):
                print("EmbeddingService: Using V1 API adapter")
                self.api_key = api_key
                # Initialize the V1 client
                if 'environment' in kwargs:
                    pinecone_pkg.init(api_key=api_key, environment=kwargs['environment'])
                elif 'cloud' in kwargs:
                    print(f"EmbeddingService: Note - 'cloud' parameter {kwargs['cloud']} ignored in V1 API")
                    pinecone_pkg.init(api_key=api_key)
                else:
                    pinecone_pkg.init(api_key=api_key)
                
            def Index(self, index_name):
                print(f"EmbeddingService: Getting index '{index_name}' with V1 API")
                return pinecone_pkg.Index(name=index_name)
            
            def list_indexes(self):
                print("EmbeddingService: Listing indexes with V1 API")
                indexes = pinecone_pkg.list_indexes()
                # Convert to V2 format for compatibility
                return {"indexes": [{"name": idx} for idx in indexes]}
                
            def create_index(self, name, dimension, metric, **kwargs):
                print(f"EmbeddingService: Creating index '{name}' with V1 API")
                spec = kwargs.get('spec', None)
                if spec:
                    # Extract cloud/region info but can't use spec directly in V1
                    print(f"EmbeddingService: Note - V1 API doesn't use 'spec' parameter")
                
                # Extract environment if present
                env = kwargs.get('environment', None)
                if env:
                    return pinecone_pkg.create_index(name=name, dimension=dimension, metric=metric, environment=env)
                else:
                    return pinecone_pkg.create_index(name=name, dimension=dimension, metric=metric)
        
        class ServerlessSpec:
            def __init__(self, cloud, region):
                self.cloud = cloud
                self.region = region
                
        PINECONE_NEW_API = False
    else:
        print("EmbeddingService: WARNING - Unknown Pinecone API version")
        from pinecone import Pinecone, ServerlessSpec
        PINECONE_NEW_API = True
        
    PINECONE_IMPORT_SUCCESS = True
    print(f"EmbeddingService: Successfully imported pinecone package (New API: {PINECONE_NEW_API})")
    
except ImportError as e:
    print(f"EmbeddingService: WARNING - Pinecone import failed: {str(e)}")
    print(f"EmbeddingService: Import error details:\n{traceback.format_exc()}")
    print(f"EmbeddingService: Python version: {sys.version}")
    print(f"EmbeddingService: Python path: {sys.path}")
    PINECONE_IMPORT_SUCCESS = False
    PINECONE_NEW_API = False
    # Define stub classes for Pinecone
    class Pinecone:
        def __init__(self, api_key, **kwargs):
            print("WARNING: Using mock Pinecone class")
            
        def list_indexes(self):
            return {"indexes": []}
            
        def Index(self, index_name):
            class MockIndex:
                def describe_index_stats(self):
                    return {"namespaces": {}}
                    
                def query(self, **kwargs):
                    class MockResult:
                        def __init__(self):
                            self.matches = []
                    return MockResult()
            return MockIndex()
            
    class ServerlessSpec:
        def __init__(self, cloud, region):
            self.cloud = cloud
            self.region = region

class EmbeddingService:
    def __init__(self):
        # Set up logging
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(__name__)
        
        # Get configuration from environment variables
        self.openai_api_key = os.getenv('OPENAI_API_KEY')
        self.pinecone_api_key = os.getenv('PINECONE_API_KEY')  # Correct API key for Pinecone
        self.model = os.getenv('EMBEDDING_MODEL', 'text-embedding-ada-002')
        self.max_retries = int(os.getenv('EMBEDDING_MAX_RETRIES', '3'))
        self.retry_delay = float(os.getenv('EMBEDDING_RETRY_DELAY', '1.0'))
        self.cloud = os.getenv('PINECONE_CLOUD', 'aws')
        self.region = os.getenv('PINECONE_REGION', 'us-east-1')
        self.environment = os.getenv('PINECONE_ENVIRONMENT')  # For backwards compatibility
        self.index_name = os.getenv('PINECONE_INDEX', 'radiant-documents')
        
        # Initialize OpenAI client for embeddings
        if not self.openai_api_key:
            self.logger.warning("OpenAI API key not set. Embeddings will fail.")
            self.openai_client = None
            self.openai_available = False
        else:
            self.openai_client = OpenAI(api_key=self.openai_api_key)
            self.openai_available = True
        
        if not self.pinecone_api_key:
            self.logger.warning("Pinecone API key not set. Using mock embeddings.")
            self.pinecone_available = False
            return
            
        # Initialize Pinecone with proper error handling
        try:
            self.logger.info(f"Initializing Pinecone with cloud: {self.cloud}, region: {self.region}")
            
            # Initialize Pinecone based on API version
            if PINECONE_NEW_API:
                # New API format
                self.logger.info("Using V2 Pinecone API format")
                if self.environment:
                    self.logger.info(f"Using environment parameter: {self.environment}")
                    pc = Pinecone(api_key=self.pinecone_api_key, environment=self.environment)
                else:
                    self.logger.info(f"Using cloud parameter: {self.cloud}")
                    pc = Pinecone(api_key=self.pinecone_api_key, cloud=self.cloud)
            else:
                # Old API format (V1)
                self.logger.info("Using V1 Pinecone API format")
                if self.environment:
                    pc = Pinecone(api_key=self.pinecone_api_key, environment=self.environment)
                else:
                    pc = Pinecone(api_key=self.pinecone_api_key)
                    
            self.pinecone_available = True
            
            # Check if index exists and connect to it
            try:
                # Get list of indexes
                self.logger.info("Checking available Pinecone indexes...")
                
                # List indexes based on API version
                if PINECONE_NEW_API:
                    # New API format
                    try:
                        indexes_response = pc.list_indexes()
                        self.logger.info(f"Raw Pinecone index list response: {indexes_response}")
                        available_indexes = [idx['name'] for idx in indexes_response.get('indexes', [])]
                    except Exception as list_err:
                        self.logger.error(f"Error listing indexes with V2 API: {str(list_err)}")
                        # Try again with a short delay
                        time.sleep(1)
                        try:
                            indexes_response = pc.list_indexes()
                            self.logger.info(f"Retry - Raw Pinecone index list response: {indexes_response}")
                            available_indexes = [idx['name'] for idx in indexes_response.get('indexes', [])]
                        except Exception as retry_err:
                            self.logger.error(f"Retry failed - Error listing indexes: {str(retry_err)}")
                            available_indexes = []
                else:
                    # Old API might return list or dict
                    try:
                        indexes_resp = pc.list_indexes()
                        self.logger.info(f"Raw Pinecone index list response (V1): {indexes_resp}")
                        if isinstance(indexes_resp, dict) and 'indexes' in indexes_resp:
                            available_indexes = [idx['name'] for idx in indexes_resp.get('indexes', [])]
                        elif isinstance(indexes_resp, list):
                            available_indexes = indexes_resp
                        else:
                            available_indexes = []
                    except Exception as list_err:
                        self.logger.error(f"Error listing indexes with V1 API: {str(list_err)}")
                        # Try again with a short delay
                        time.sleep(1)
                        try:
                            indexes_resp = pc.list_indexes()
                            self.logger.info(f"Retry - Raw Pinecone index list response (V1): {indexes_resp}")
                            if isinstance(indexes_resp, dict) and 'indexes' in indexes_resp:
                                available_indexes = [idx['name'] for idx in indexes_resp.get('indexes', [])]
                            elif isinstance(indexes_resp, list):
                                available_indexes = indexes_resp
                            else:
                                available_indexes = []
                        except Exception as retry_err:
                            self.logger.error(f"Retry failed - Error listing indexes: {str(retry_err)}")
                            available_indexes = []
                        
                self.logger.info(f"Available Pinecone indexes: {available_indexes}")
                self.logger.info(f"Checking for index name: '{self.index_name}'")
                self.logger.info(f"Case-sensitive match found: {self.index_name in available_indexes}")
                
                # Check also for case-insensitive matches which might be causing confusion
                for idx in available_indexes:
                    if idx.lower() == self.index_name.lower() and idx != self.index_name:
                        self.logger.warning(f"Found case-insensitive match: '{idx}' vs target '{self.index_name}'")
                        self.logger.warning(f"This might be causing confusion - consider using the exact case")
                
                if self.index_name not in available_indexes:
                    self.logger.info(f"Creating new Pinecone index: {self.index_name}")
                    # Create index with the appropriate dimension for text-embedding-ada-002 (1536)
                    try:
                        if PINECONE_NEW_API:
                            pc.create_index(
                                name=self.index_name,
                                dimension=1536,  # dimension for text-embedding-ada-002
                                metric="cosine",
                                spec=ServerlessSpec(
                                    cloud=self.cloud,
                                    region=self.region
                                )
                            )
                        else:
                            # Old API doesn't use spec
                            if self.environment:
                                pc.create_index(
                                    name=self.index_name,
                                    dimension=1536,
                                    metric="cosine",
                                    environment=self.environment
                                )
                            else:
                                pc.create_index(
                                    name=self.index_name,
                                    dimension=1536,
                                    metric="cosine"
                                )
                        self.logger.info(f"Successfully created index: {self.index_name}")
                    except Exception as create_err:
                        self.logger.error(f"Error creating index: {str(create_err)}")
                        
                        # Check if it's a quota error
                        err_str = str(create_err).lower()
                        if "quota" in err_str or "limit" in err_str or "max pods" in err_str:
                            self.logger.error("Detected quota limit error from Pinecone")
                            self.logger.error("This might be due to account limitations - if you have existing indexes, try using one of those instead")
                            
                            # Try to use an existing index if any are available
                            if available_indexes:
                                alternative_index = available_indexes[0]
                                self.logger.warning(f"Will try to use existing index '{alternative_index}' instead")
                                self.index_name = alternative_index
                            else:
                                self.logger.error("No existing indexes found to use as an alternative")
                                raise
                        else:
                            # Re-raise for other errors
                            raise
                
                # Connect to the index based on API version
                if PINECONE_NEW_API:
                    self.index = pc.Index(self.index_name)
                else:
                    self.index = pc.Index(name=self.index_name)
                
                self.logger.info(f"Connected to Pinecone index: {self.index_name}")
                
                # Test the connection
                stats = self.index.describe_index_stats()
                self.logger.info(f"Index stats: {stats}")
                
            except Exception as e:
                self.logger.error(f"Error with Pinecone index: {str(e)}")
                self.logger.error(f"Details: {traceback.format_exc()}")
                self.pinecone_available = False
                
        except Exception as e:
            self.logger.error(f"Error initializing Pinecone: {str(e)}")
            self.pinecone_available = False
    
    def generate_embeddings(self, texts: List[str]) -> List[List[float]]:
        """
        Generate embeddings for a list of texts using OpenAI's text-embedding-ada-002 model.
        Falls back to mock embeddings if OpenAI is unavailable.
        """
        if not self.openai_available:
            self.logger.warning("OpenAI client unavailable. Using mock embeddings.")
            return [np.random.rand(1536).tolist() for _ in texts]
        
        embeddings = []
        
        # Process texts in batches to avoid rate limits
        batch_size = 10
        for i in range(0, len(texts), batch_size):
            batch = texts[i:i+batch_size]
            self.logger.info(f"Generating embeddings for batch of {len(batch)} texts")
            
            try:
                # Add a small delay to avoid rate limits
                time.sleep(0.5)
                
                # Generate embeddings with OpenAI
                response = self.openai_client.embeddings.create(
                    model="text-embedding-ada-002",
                    input=batch
                )
                
                # Extract embeddings from response
                batch_embeddings = [item.embedding for item in response.data]
                embeddings.extend(batch_embeddings)
                
                self.logger.info(f"Successfully generated {len(batch_embeddings)} embeddings")
            except Exception as e:
                self.logger.error(f"Error generating embeddings: {str(e)}")
                # Add mock embeddings for this batch as fallback
                mock_embeddings = [np.random.rand(1536).tolist() for _ in batch]
                embeddings.extend(mock_embeddings)
        
        return embeddings
    
    def similarity_search(self, query: str, top_k: int = 3, namespace: str = None) -> List[Dict[str, Any]]:
        """
        Find the most similar documents to the query using Pinecone.
        Returns document IDs and metadata.
        """
        if not self.pinecone_available or not self.openai_available:
            self.logger.warning("Pinecone or OpenAI unavailable. Using mock similarity search.")
            return [
                {"id": f"mock_doc_{i}", "score": 0.9 - (i * 0.1), "metadata": {"text": f"Mock document {i}"}} 
                for i in range(1, top_k + 1)
            ]
        
        try:
            # Generate embedding for the query
            self.logger.info(f"Generating embedding for query: '{query[:50]}...'")
            embedding = self.generate_single_embedding(query)
            
            if not embedding:
                self.logger.error("Failed to generate embedding for query")
                return []
            
            # Search Pinecone with the query embedding
            self.logger.info(f"Searching Pinecone index with the query embedding")
            results = self.index.query(
                vector=embedding,
                top_k=top_k,
                include_metadata=True,
                namespace=namespace
            )
            
            # Format results
            formatted_results = []
            for match in results.matches:
                formatted_match = {
                    "id": match.id,
                    "score": match.score,
                    "metadata": match.metadata or {}
                }
                formatted_results.append(formatted_match)
            
            self.logger.info(f"Found {len(formatted_results)} matches for the query")
            return formatted_results
            
        except Exception as e:
            self.logger.error(f"Error during similarity search: {str(e)}")
            return []
    
    def generate_single_embedding(self, text: str) -> Optional[List[float]]:
        """Generate embedding for a single text using OpenAI."""
        if not self.openai_available:
            self.logger.warning("OpenAI client unavailable. Using mock embedding.")
            return np.random.rand(1536).tolist()
        
        try:
            # Generate embedding with OpenAI
            response = self.openai_client.embeddings.create(
                model="text-embedding-ada-002",
                input=text
            )
            
            # Extract embedding from response
            embedding = response.data[0].embedding
            return embedding
        except Exception as e:
            self.logger.error(f"Error generating single embedding: {str(e)}")
            return None 