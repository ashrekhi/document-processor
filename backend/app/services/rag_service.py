import json
import os
from typing import List, Dict, Any
from openai import OpenAI

from app.services.vector_db_service import VectorDBService
from app.services.s3_service import S3Service

class RAGService:
    def __init__(self):
        self.s3_service = S3Service()
        self.vector_db_service = VectorDBService()
        self.metadata_folder = "metadata"
        self.api_key = os.getenv('OPENAI_API_KEY')
        if not self.api_key:
            print("WARNING: OPENAI_API_KEY not set. Using mock responses.")
            self.client = None
        else:
            self.client = OpenAI(api_key=self.api_key)
    
    def answer_question(self, question: str, doc_ids: List[str], model: str = "gpt-3.5-turbo") -> str:
        """Answer a question using RAG"""
        try:
            # Search for relevant chunks
            relevant_chunks = self.vector_db_service.search_similar(
                query=question,
                top_k=5,
                filter_doc_ids=doc_ids
            )
            
            if not relevant_chunks:
                return "I couldn't find any relevant information to answer your question. Please try a different question or upload more documents."
            
            # Build context from relevant chunks
            context = "\n\n".join([chunk["text"] for chunk in relevant_chunks])
            
            # Generate answer using OpenAI
            response = self.client.chat.completions.create(
                model=model,
                messages=[
                    {"role": "system", "content": "You are a helpful assistant that answers questions based on the provided context."},
                    {"role": "user", "content": f"Context:\n{context}\n\nQuestion: {question}\n\nAnswer:"}
                ],
                temperature=0.3,
                max_tokens=500
            )
            
            return response.choices[0].message.content
        except Exception as e:
            print(f"Error in RAG: {str(e)}")
            return f"I'm sorry, I encountered an error while trying to answer your question: {str(e)}" 