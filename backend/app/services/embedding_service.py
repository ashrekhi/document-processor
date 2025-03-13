from typing import List
import os
import numpy as np
import random

class EmbeddingService:
    def __init__(self):
        # Mock embedding service for testing
        pass
    
    def generate_embeddings(self, texts: List[str]) -> List[List[float]]:
        """Generate mock embeddings for testing"""
        # Generate random embeddings of dimension 1536 (same as OpenAI's ada-002)
        return [
            [random.uniform(-1, 1) for _ in range(1536)]
            for _ in texts
        ]
    
    def similarity_search(self, query: str, embeddings: List[List[float]], top_k: int = 5) -> List[int]:
        """Mock similarity search that returns random indices"""
        indices = list(range(len(embeddings)))
        random.shuffle(indices)
        return indices[:min(top_k, len(indices))] 