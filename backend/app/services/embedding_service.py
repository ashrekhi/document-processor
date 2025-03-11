from typing import List
import os
from sentence_transformers import SentenceTransformer

class EmbeddingService:
    def __init__(self):
        # Load the embedding model
        self.model = SentenceTransformer('all-MiniLM-L6-v2')
    
    def generate_embeddings(self, texts: List[str]) -> List[List[float]]:
        """Generate embeddings for a list of text chunks"""
        embeddings = self.model.encode(texts)
        return embeddings.tolist()
    
    def similarity_search(self, query: str, embeddings: List[List[float]], top_k: int = 5) -> List[int]:
        """Find the most similar chunks to a query"""
        query_embedding = self.model.encode([query])[0]
        
        # Calculate similarities
        similarities = []
        for i, embedding in enumerate(embeddings):
            # Cosine similarity
            dot_product = sum(a * b for a, b in zip(query_embedding, embedding))
            magnitude1 = sum(a * a for a in query_embedding) ** 0.5
            magnitude2 = sum(b * b for b in embedding) ** 0.5
            similarity = dot_product / (magnitude1 * magnitude2)
            
            similarities.append((i, similarity))
        
        # Sort by similarity (descending)
        similarities.sort(key=lambda x: x[1], reverse=True)
        
        # Return indices of top_k most similar chunks
        return [idx for idx, _ in similarities[:top_k]] 