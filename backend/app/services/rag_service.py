import json
import os
from typing import List, Dict, Any
from openai import OpenAI

from app.services.embedding_service import EmbeddingService
from app.services.s3_service import S3Service

class RAGService:
    def __init__(self):
        self.s3_service = S3Service()
        self.embedding_service = EmbeddingService()
        self.metadata_folder = "metadata"
        self.api_key = os.getenv('OPENAI_API_KEY')
        if not self.api_key:
            print("WARNING: OPENAI_API_KEY not set. Using mock responses.")
            self.client = None
        else:
            self.client = OpenAI(api_key=self.api_key)
    
    def answer_question(self, question: str, doc_ids: List[str], model: str = "gpt-3.5-turbo") -> str:
        """Answer a question using RAG approach with the specified documents and model"""
        # Get all chunks from the specified documents
        all_chunks = []
        all_embeddings = []
        
        for doc_id in doc_ids:
            try:
                # Get document metadata
                metadata_obj = self.s3_service.s3_client.get_object(
                    Bucket=self.s3_service.master_bucket,
                    Key=f"{self.metadata_folder}/{doc_id}.json"
                )
                metadata = json.loads(metadata_obj['Body'].read().decode('utf-8'))
                document_folder = metadata.get('folder')
                
                if document_folder:
                    # List all chunk files for this document
                    response = self.s3_service.s3_client.list_objects_v2(
                        Bucket=self.s3_service.master_bucket,
                        Prefix=f"{document_folder}/chunk_"
                    )
                    
                    if 'Contents' in response:
                        for obj in response['Contents']:
                            # Get chunk data
                            chunk_obj = self.s3_service.s3_client.get_object(
                                Bucket=self.s3_service.master_bucket,
                                Key=obj['Key']
                            )
                            chunk_data = json.loads(chunk_obj['Body'].read().decode('utf-8'))
                            
                            all_chunks.append(chunk_data['text'])
                            all_embeddings.append(chunk_data['embedding'])
            except Exception as e:
                print(f"Error loading chunks for {doc_id}: {str(e)}")
        
        if not all_chunks:
            return "No document content found to answer the question."
        
        # Find most relevant chunks
        top_indices = self.embedding_service.similarity_search(question, all_embeddings)
        
        # Build context from top chunks
        context = "\n\n".join([all_chunks[i] for i in top_indices])
        
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