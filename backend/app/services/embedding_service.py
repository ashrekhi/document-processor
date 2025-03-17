from typing import List, Optional
import os
import numpy as np
import random
import pinecone
import logging

class EmbeddingService:
    def __init__(self):
        # Set up logging
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(__name__)
        
        # Get environment variables
        self.api_key = os.getenv('PINECONE_API_KEY')
        self.environment = os.getenv('PINECONE_ENVIRONMENT')
        self.index_name = os.getenv('PINECONE_INDEX', 'radiant-documents')
        
        if not self.api_key or not self.environment:
            self.logger.warning("Pinecone API key or environment not set. Using mock embeddings.")
            self.pinecone_available = False
            return
            
        # Initialize Pinecone with proper error handling
        try:
            self.logger.info(f"Initializing Pinecone with environment: {self.environment}")
            pinecone.init(api_key=self.api_key, environment=self.environment)
            self.pinecone_available = True
            
            # Check if index exists
            try:
                indexes = pinecone.list_indexes()
                self.logger.info(f"Available Pinecone indexes: {indexes}")
                
                if self.index_name not in indexes:
                    self.logger.info(f"Creating new Pinecone index: {self.index_name}")
                    pinecone.create_index(
                        name=self.index_name,
                        dimension=384,  # Adjust based on your embedding model
                        metric="cosine"
                    )
                
                self.index = pinecone.Index(self.index_name)
                self.logger.info(f"Connected to Pinecone index: {self.index_name}")
                
            except Exception as e:
                self.logger.error(f"Error with Pinecone index: {str(e)}")
                self.pinecone_available = False
                # Fall back to mock embeddings
                
        except Exception as e:
            self.logger.error(f"Error initializing Pinecone: {str(e)}")
            self.pinecone_available = False
            # Fall back to mock embeddings
    
    def generate_embeddings(self, texts: List[str]) -> List[List[float]]:
        """
        Generate embeddings for a list of texts.
        Falls back to mock embeddings if Pinecone is unavailable.
        """
        if not hasattr(self, 'pinecone_available') or not self.pinecone_available:
            # Return mock embeddings for testing
            self.logger.warning("Using mock embeddings as Pinecone is unavailable")
            return [np.random.rand(384).tolist() for _ in texts]
        
        # In a real implementation, you would use a model to generate embeddings
        # For now, we'll just return random vectors
        return [np.random.rand(384).tolist() for _ in texts]
    
    def similarity_search(self, query: str, top_k: int = 3) -> List[str]:
        """
        Find the most similar documents to the query.
        Falls back to random selection if Pinecone is unavailable.
        """
        if not hasattr(self, 'pinecone_available') or not self.pinecone_available:
            self.logger.warning("Using mock similarity search as Pinecone is unavailable")
            return ["mock_doc_1", "mock_doc_2", "mock_doc_3"]
        
        # In a real implementation, you would:
        # 1. Generate an embedding for the query
        # 2. Search Pinecone for similar vectors
        # 3. Return the document IDs
        
        # For now, just return mock results
        return ["doc_1", "doc_2", "doc_3"] 