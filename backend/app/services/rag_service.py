import json
import os
from typing import List, Dict, Any
import openai

from app.services.embedding_service import EmbeddingService

class RAGService:
    def __init__(self):
        self.embedding_service = EmbeddingService()
        self.metadata_bucket = os.getenv('METADATA_BUCKET', 'doc-processor-metadata')
        self.s3_client = self.embedding_service.s3_client
        
        # Initialize OpenAI client
        openai.api_key = os.getenv('OPENAI_API_KEY')
    
    def answer_question(self, question: str, doc_ids: List[str]) -> str:
        """
        Answer a question using RAG:
        1. Retrieve relevant chunks from the specified documents
        2. Generate an answer using the retrieved context
        """
        # Get relevant chunks from each document
        all_chunks = []
        all_embeddings = []
        
        for doc_id in doc_ids:
            # List all chunk files for this document
            response = self.s3_client.list_objects_v2(
                Bucket=self.metadata_bucket,
                Prefix=f"{doc_id}/chunk_"
            )
            
            if 'Contents' in response:
                for obj in response['Contents']:
                    # Load chunk metadata
                    chunk_obj = self.s3_client.get_object(
                        Bucket=self.metadata_bucket,
                        Key=obj['Key']
                    )
                    chunk_data = json.loads(chunk_obj['Body'].read().decode('utf-8'))
                    
                    all_chunks.append(chunk_data['text'])
                    all_embeddings.append(chunk_data['embedding'])
        
        if not all_chunks:
            return "No document content found to answer the question."
        
        # Find the most relevant chunks
        top_indices = self.embedding_service.similarity_search(
            query=question,
            embeddings=all_embeddings,
            top_k=5
        )
        
        # Build context from top chunks
        context = "\n\n".join([all_chunks[i] for i in top_indices])
        
        # Generate answer using OpenAI
        response = openai.ChatCompletion.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "You are a helpful assistant that answers questions based on the provided context. If the answer cannot be found in the context, say so."},
                {"role": "user", "content": f"Context:\n{context}\n\nQuestion: {question}"}
            ],
            max_tokens=500,
            temperature=0.3
        )
        
        return response.choices[0].message.content 