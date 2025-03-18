from typing import List, Optional, Dict, Any
import os
import numpy as np
from openai import OpenAI
import logging
import time

# Import Pinecone with proper handling for import errors
try:
    from pinecone import Pinecone, ServerlessSpec
    PINECONE_IMPORT_SUCCESS = True
    print(f"EmbeddingService: Pinecone import succeeded")
except ImportError as e:
    print(f"EmbeddingService: WARNING - Pinecone import failed: {str(e)}")
    PINECONE_IMPORT_SUCCESS = False
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
        
        # Get environment variables
        self.api_key = os.getenv('PINECONE_API_KEY')
        self.cloud = os.getenv('PINECONE_CLOUD', 'aws')
        self.region = os.getenv('PINECONE_REGION', 'us-east-1')
        self.environment = os.getenv('PINECONE_ENVIRONMENT')  # For backwards compatibility
        self.index_name = os.getenv('PINECONE_INDEX', 'radiant-documents')
        self.openai_api_key = os.getenv('OPENAI_API_KEY')
        
        # Initialize OpenAI client for embeddings
        if not self.openai_api_key:
            self.logger.warning("OpenAI API key not set. Embeddings will fail.")
            self.openai_client = None
            self.openai_available = False
        else:
            self.openai_client = OpenAI(api_key=self.openai_api_key)
            self.openai_available = True
        
        if not self.api_key:
            self.logger.warning("Pinecone API key not set. Using mock embeddings.")
            self.pinecone_available = False
            return
            
        # Initialize Pinecone with proper error handling
        try:
            self.logger.info(f"Initializing Pinecone with cloud: {self.cloud}, region: {self.region}")
            
            # Initialize Pinecone with the new API
            pc = Pinecone(api_key=self.api_key, cloud=self.cloud)
            self.pinecone_available = True
            
            # Check if index exists and connect to it
            try:
                # Get list of indexes
                self.logger.info("Checking available Pinecone indexes...")
                
                # List indexes with the new API format
                available_indexes = [idx['name'] for idx in pc.list_indexes().get('indexes', [])]
                self.logger.info(f"Available Pinecone indexes: {available_indexes}")
                
                if self.index_name not in available_indexes:
                    self.logger.info(f"Creating new Pinecone index: {self.index_name}")
                    # Create index with the appropriate dimension for text-embedding-ada-002 (1536)
                    pc.create_index(
                        name=self.index_name,
                        dimension=1536,  # dimension for text-embedding-ada-002
                        metric="cosine",
                        spec=ServerlessSpec(
                            cloud=self.cloud,
                            region=self.region
                        )
                    )
                
                # Connect to the index with the new API
                self.index = pc.Index(self.index_name)
                
                self.logger.info(f"Connected to Pinecone index: {self.index_name}")
                
                # Test the connection
                stats = self.index.describe_index_stats()
                self.logger.info(f"Index stats: {stats}")
                
            except Exception as e:
                self.logger.error(f"Error with Pinecone index: {str(e)}")
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