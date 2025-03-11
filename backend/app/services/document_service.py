import json
import os
import fitz  # PyMuPDF
from io import BytesIO
from typing import List, Dict, Any, Optional

from app.services.s3_service import S3Service
from app.services.embedding_service import EmbeddingService

class DocumentService:
    def __init__(self, s3_service: S3Service):
        self.s3_service = s3_service
        self.embedding_service = EmbeddingService()
        self.metadata_bucket = os.getenv('METADATA_BUCKET', 'doc-processor-metadata')
        
        # Ensure metadata bucket exists
        try:
            self.s3_service.create_bucket(self.metadata_bucket)
        except Exception as e:
            print(f"Error creating metadata bucket: {str(e)}")
    
    def process_document(
        self, 
        doc_id: str, 
        filename: str, 
        bucket_name: str, 
        s3_key: str,
        source_name: str,
        description: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Process a document for RAG:
        1. Extract text
        2. Split into chunks
        3. Generate embeddings
        4. Store metadata
        """
        # Download the file from S3
        file_buffer = self.s3_service.download_file(bucket_name, s3_key)
        
        # Extract text based on file type
        file_extension = os.path.splitext(filename)[1].lower()
        
        if file_extension == '.pdf':
            text = self._extract_text_from_pdf(file_buffer)
        elif file_extension in ['.txt', '.md']:
            text = file_buffer.read().decode('utf-8')
        else:
            # For other file types, we could add more extractors
            text = f"Unsupported file type: {file_extension}"
        
        # Split text into chunks
        chunks = self._split_text(text)
        
        # Generate embeddings for each chunk
        embeddings = self.embedding_service.generate_embeddings(chunks)
        
        # Store document metadata
        metadata = {
            "id": doc_id,
            "filename": filename,
            "source": source_name,
            "description": description,
            "bucket_name": bucket_name,
            "s3_key": s3_key,
            "chunk_count": len(chunks)
        }
        
        # Store chunks and embeddings
        for i, (chunk, embedding) in enumerate(zip(chunks, embeddings)):
            chunk_metadata = {
                "doc_id": doc_id,
                "chunk_id": i,
                "text": chunk,
                "embedding": embedding
            }
            
            # Save chunk metadata to S3
            self.s3_service.s3_client.put_object(
                Bucket=self.metadata_bucket,
                Key=f"{doc_id}/chunk_{i}.json",
                Body=json.dumps(chunk_metadata)
            )
        
        # Save document metadata
        self.s3_service.s3_client.put_object(
            Bucket=self.metadata_bucket,
            Key=f"{doc_id}/metadata.json",
            Body=json.dumps(metadata)
        )
        
        return metadata
    
    def list_documents(self) -> List[Dict[str, Any]]:
        """List all documents"""
        documents = []
        
        # List all folders in metadata bucket
        response = self.s3_service.s3_client.list_objects_v2(
            Bucket=self.metadata_bucket,
            Delimiter='/'
        )
        
        if 'CommonPrefixes' in response:
            for prefix in response['CommonPrefixes']:
                doc_id = prefix['Prefix'].rstrip('/')
                
                # Get metadata for this document
                try:
                    metadata_obj = self.s3_service.s3_client.get_object(
                        Bucket=self.metadata_bucket,
                        Key=f"{doc_id}/metadata.json"
                    )
                    metadata = json.loads(metadata_obj['Body'].read().decode('utf-8'))
                    
                    documents.append({
                        "id": metadata["id"],
                        "filename": metadata["filename"],
                        "source": metadata["source"],
                        "description": metadata.get("description"),
                        "s3_url": f"s3://{metadata['bucket_name']}/{metadata['s3_key']}"
                    })
                except Exception as e:
                    print(f"Error loading metadata for {doc_id}: {str(e)}")
        
        return documents
    
    def delete_document(self, doc_id: str) -> None:
        """Delete a document and its associated data"""
        try:
            # Get document metadata
            metadata_obj = self.s3_service.s3_client.get_object(
                Bucket=self.metadata_bucket,
                Key=f"{doc_id}/metadata.json"
            )
            metadata = json.loads(metadata_obj['Body'].read().decode('utf-8'))
            
            # Delete the document bucket
            self.s3_service.delete_bucket(metadata["bucket_name"])
            
            # Delete metadata
            objects = self.s3_service.s3_client.list_objects_v2(
                Bucket=self.metadata_bucket,
                Prefix=f"{doc_id}/"
            )
            
            if 'Contents' in objects:
                for obj in objects['Contents']:
                    self.s3_service.s3_client.delete_object(
                        Bucket=self.metadata_bucket,
                        Key=obj['Key']
                    )
        
        except Exception as e:
            raise Exception(f"Error deleting document {doc_id}: {str(e)}")
    
    def _extract_text_from_pdf(self, file_buffer: BytesIO) -> str:
        """Extract text from a PDF file"""
        pdf_document = fitz.open(stream=file_buffer.read(), filetype="pdf")
        text = ""
        
        for page_num in range(len(pdf_document)):
            page = pdf_document.load_page(page_num)
            text += page.get_text()
        
        return text
    
    def _split_text(self, text: str, chunk_size: int = 1000, overlap: int = 100) -> List[str]:
        """Split text into overlapping chunks"""
        chunks = []
        
        if len(text) <= chunk_size:
            chunks.append(text)
        else:
            start = 0
            while start < len(text):
                end = min(start + chunk_size, len(text))
                
                # Try to find a good breaking point (period, newline, etc.)
                if end < len(text):
                    # Look for a period or newline within the last 100 chars
                    for i in range(end, max(start, end - 100), -1):
                        if text[i] in ['.', '\n']:
                            end = i + 1
                            break
                
                chunks.append(text[start:end])
                start = end - overlap
        
        return chunks 