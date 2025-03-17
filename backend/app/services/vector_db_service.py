import os
import json
import pinecone
from typing import List, Dict, Any, Optional
from openai import OpenAI

class VectorDBService:
    def __init__(self):
        # Initialize OpenAI client
        self.openai_api_key = os.getenv('OPENAI_API_KEY')
        if not self.openai_api_key:
            print("WARNING: OPENAI_API_KEY not set. Vector operations will fail.")
            self.openai_client = None
        else:
            self.openai_client = OpenAI(api_key=self.openai_api_key)
        
        # Initialize Pinecone
        self.pinecone_api_key = os.getenv('PINECONE_API_KEY')
        self.pinecone_environment = os.getenv('PINECONE_ENVIRONMENT', 'us-east-1')
        self.index_name = os.getenv('PINECONE_INDEX', 'radiant-documents')
        
        if not self.pinecone_api_key:
            print("WARNING: PINECONE_API_KEY not set. Vector operations will fail.")
            self.pinecone_index = None
        else:
            try:
                pinecone.init(api_key=self.pinecone_api_key, environment=self.pinecone_environment)
                
                # Check if index exists, if not create it
                if self.index_name not in pinecone.list_indexes():
                    pinecone.create_index(
                        name=self.index_name,
                        dimension=1536,  # OpenAI embedding dimension
                        metric="cosine"
                    )
                
                self.pinecone_index = pinecone.Index(self.index_name)
                print(f"Connected to Pinecone index: {self.index_name}")
            except Exception as e:
                print(f"Error initializing Pinecone: {str(e)}")
                self.pinecone_index = None
    
    def generate_embeddings(self, texts: List[str]) -> List[List[float]]:
        """Generate embeddings using OpenAI's API"""
        if not self.openai_client:
            # Return mock embeddings if OpenAI client is not available
            import random
            return [[random.uniform(-1, 1) for _ in range(1536)] for _ in texts]
        
        embeddings = []
        # Process in batches to avoid rate limits
        batch_size = 20
        for i in range(0, len(texts), batch_size):
            batch = texts[i:i+batch_size]
            try:
                response = self.openai_client.embeddings.create(
                    model="text-embedding-ada-002",
                    input=batch
                )
                batch_embeddings = [item.embedding for item in response.data]
                embeddings.extend(batch_embeddings)
            except Exception as e:
                print(f"Error generating embeddings: {str(e)}")
                # Return mock embeddings for this batch
                import random
                batch_embeddings = [[random.uniform(-1, 1) for _ in range(1536)] for _ in batch]
                embeddings.extend(batch_embeddings)
        
        return embeddings
    
    def store_document_chunks(self, doc_id: str, chunks: List[str], metadata: Dict[str, Any]) -> bool:
        """Store document chunks in the vector database"""
        if not self.pinecone_index or not self.openai_client:
            print("Cannot store chunks: Pinecone or OpenAI client not initialized")
            return False
        
        # Generate embeddings for chunks
        embeddings = self.generate_embeddings(chunks)
        
        # Prepare vectors for upsert
        vectors = []
        for i, (chunk, embedding) in enumerate(zip(chunks, embeddings)):
            chunk_id = f"{doc_id}_chunk_{i}"
            vectors.append({
                "id": chunk_id,
                "values": embedding,
                "metadata": {
                    "doc_id": doc_id,
                    "chunk_index": i,
                    "text": chunk,
                    "filename": metadata.get("filename", ""),
                    "source": metadata.get("source", ""),
                    "description": metadata.get("description", "")
                }
            })
        
        # Upsert in batches
        batch_size = 100
        for i in range(0, len(vectors), batch_size):
            batch = vectors[i:i+batch_size]
            try:
                self.pinecone_index.upsert(vectors=batch)
            except Exception as e:
                print(f"Error upserting vectors to Pinecone: {str(e)}")
                return False
        
        return True
    
    def delete_document(self, doc_id: str) -> bool:
        """Delete all chunks for a document from the vector database"""
        if not self.pinecone_index:
            print("Cannot delete document: Pinecone client not initialized")
            return False
        
        try:
            # Delete by metadata filter
            self.pinecone_index.delete(filter={"doc_id": doc_id})
            return True
        except Exception as e:
            print(f"Error deleting document from Pinecone: {str(e)}")
            return False
    
    def similarity_search(self, query: str, top_k: int = 5, filter_doc_ids: Optional[List[str]] = None) -> List[Dict[str, Any]]:
        """Search for similar chunks in the vector database"""
        if not self.pinecone_index or not self.openai_client:
            print("Cannot perform search: Pinecone or OpenAI client not initialized")
            # Return empty results
            return []
        
        try:
            # Generate embedding for the query
            query_embedding = self.generate_embeddings([query])[0]
            
            # Prepare filter if document IDs are provided
            filter_dict = None
            if filter_doc_ids:
                filter_dict = {"doc_id": {"$in": filter_doc_ids}}
            
            # Query Pinecone
            results = self.pinecone_index.query(
                vector=query_embedding,
                top_k=top_k,
                include_metadata=True,
                filter=filter_dict
            )
            
            # Format results
            formatted_results = []
            for match in results.matches:
                formatted_results.append({
                    "id": match.id,
                    "score": match.score,
                    "text": match.metadata.get("text", ""),
                    "doc_id": match.metadata.get("doc_id", ""),
                    "filename": match.metadata.get("filename", ""),
                    "source": match.metadata.get("source", ""),
                    "description": match.metadata.get("description", "")
                })
            
            return formatted_results
        except Exception as e:
            print(f"Error performing similarity search: {str(e)}")
            return [] 