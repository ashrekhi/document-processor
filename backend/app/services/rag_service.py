import json
import os
from typing import List, Dict, Any

from app.services.embedding_service import EmbeddingService
from app.services.s3_service import S3Service

class RAGService:
    def __init__(self):
        self.s3_service = S3Service()
        self.embedding_service = EmbeddingService()
        self.metadata_folder = "metadata"
    
    def answer_question(self, question: str, doc_ids: List[str]) -> str:
        """Answer a question using RAG approach with the specified documents"""
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
        
        # Mock answer generation
        return f"This is a mock answer to the question: '{question}' based on the provided context. In a real implementation, this would use OpenAI's API to generate a response based on the retrieved document chunks." 