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
        """Answer a question using RAG approach with the specified documents and model"""
        # Search for relevant chunks in the vector database
        search_results = self.vector_db_service.similarity_search(
            query=question,
            top_k=5,
            filter_doc_ids=doc_ids
        )
        
        if not search_results:
            return "No document content found to answer the question."
        
        # Build context from search results
        context_chunks = [result["text"] for result in search_results]
        context = "\n\n".join(context_chunks)
        
        # Use OpenAI to generate an answer
        if not self.client:
            return f"This is a mock answer to the question: '{question}' based on the provided context. In a real implementation, this would use OpenAI's API with model {model} to generate a response based on the retrieved document chunks."
        
        try:
            response = self.client.chat.completions.create(
                model=model,
                messages=[
                    {"role": "system", "content": "You are a helpful assistant that answers questions based on the provided context. If the answer cannot be found in the context, say so."},
                    {"role": "user", "content": f"Context:\n{context}\n\nQuestion: {question}"}
                ],
                max_tokens=500,
                temperature=0.3
            )
            
            return response.choices[0].message.content
        except Exception as e:
            print(f"Error generating answer with OpenAI: {str(e)}")
            return f"Error generating answer: {str(e)}" 