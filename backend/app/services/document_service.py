import json
import os
import fitz  # PyMuPDF
from io import BytesIO
from typing import List, Dict, Any, Optional

from app.services.s3_service import S3Service
from app.services.vector_db_service import VectorDBService

class DocumentService:
    def __init__(self, s3_service: S3Service):
        self.s3_service = s3_service
        self.vector_db_service = VectorDBService()
        self.metadata_folder = "metadata"
        
        # Ensure metadata folder exists
        try:
            self.s3_service.create_folder(self.metadata_folder)
        except Exception as e:
            print(f"Error creating metadata folder: {str(e)}")
    
    def process_document(
        self, 
        doc_id: str, 
        filename: str, 
        content: bytes,
        source_name: str,
        description: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Process a document for RAG:
        1. Extract text
        2. Split into chunks
        3. Generate embeddings
        4. Store in vector database
        5. Store metadata
        """
        # Create a folder for this document
        document_folder = f"documents/{doc_id}"
        self.s3_service.create_folder(document_folder)
        
        # Upload the original file
        file_extension = os.path.splitext(filename)[1].lower()
        file_key = f"original{file_extension}"
        s3_url = self.s3_service.upload_file(document_folder, file_key, content)
        
        # Extract text based on file type
        if file_extension == '.pdf':
            text = self._extract_text_from_pdf(BytesIO(content))
        elif file_extension in ['.txt', '.md']:
            text = content.decode('utf-8')
        else:
            # For other file types, we could add more extractors
            text = f"Unsupported file type: {file_extension}"
        
        # Split text into chunks
        chunks = self._split_text(text)
        
        # Store metadata
        metadata = {
            "id": doc_id,
            "filename": filename,
            "source": source_name,
            "description": description,
            "chunk_count": len(chunks),
            "folder": document_folder,
            "file_key": file_key
        }
        
        # Store chunks in vector database
        self.vector_db_service.store_document_chunks(doc_id, chunks, metadata)
        
        # Store metadata in S3
        self.s3_service.upload_file(
            self.metadata_folder,
            f"{doc_id}.json",
            json.dumps(metadata).encode('utf-8')
        )
        
        return {
            "id": doc_id,
            "filename": filename,
            "source": source_name,
            "description": description,
            "s3_url": s3_url
        }
    
    def _extract_text_from_pdf(self, file_stream: BytesIO) -> str:
        """Extract text from a PDF file"""
        text = ""
        try:
            pdf_document = fitz.open(stream=file_stream, filetype="pdf")
            for page_num in range(len(pdf_document)):
                page = pdf_document.load_page(page_num)
                text += page.get_text()
            pdf_document.close()
        except Exception as e:
            print(f"Error extracting text from PDF: {str(e)}")
            text = f"Error extracting text: {str(e)}"
        
        return text
    
    def _split_text(self, text: str, chunk_size: int = 1000, overlap: int = 200) -> List[str]:
        """Split text into overlapping chunks"""
        chunks = []
        if len(text) <= chunk_size:
            chunks.append(text)
        else:
            start = 0
            while start < len(text):
                end = start + chunk_size
                if end > len(text):
                    end = len(text)
                
                # Try to find a good breaking point (newline or space)
                if end < len(text):
                    # Look for newline first
                    newline_pos = text.rfind('\n', start, end)
                    if newline_pos > start + chunk_size // 2:
                        end = newline_pos + 1
                    else:
                        # Look for space
                        space_pos = text.rfind(' ', start, end)
                        if space_pos > start + chunk_size // 2:
                            end = space_pos + 1
                
                chunks.append(text[start:end])
                start = end - overlap
        
        return chunks
    
    def list_documents(self) -> List[Dict[str, Any]]:
        """List all available documents"""
        documents = []
        
        try:
            # List all metadata files
            response = self.s3_service.s3_client.list_objects_v2(
                Bucket=self.s3_service.master_bucket,
                Prefix=f"{self.metadata_folder}/"
            )
            
            if 'Contents' in response:
                for obj in response['Contents']:
                    if obj['Key'].endswith('.json'):
                        try:
                            # Get metadata
                            metadata_obj = self.s3_service.s3_client.get_object(
                                Bucket=self.s3_service.master_bucket,
                                Key=obj['Key']
                            )
                            metadata = json.loads(metadata_obj['Body'].read().decode('utf-8'))
                            
                            documents.append({
                                "id": metadata["id"],
                                "filename": metadata["filename"],
                                "source": metadata["source"],
                                "description": metadata.get("description"),
                                "s3_url": f"s3://{self.s3_service.master_bucket}/{metadata['folder']}/{metadata['file_key']}"
                            })
                        except Exception as e:
                            print(f"Error loading metadata: {str(e)}")
        except Exception as e:
            print(f"Error listing documents: {str(e)}")
        
        return documents
    
    def delete_document(self, doc_id: str) -> bool:
        """Delete a document and all its data"""
        try:
            # Get metadata to find the document folder
            try:
                metadata_obj = self.s3_service.s3_client.get_object(
                    Bucket=self.s3_service.master_bucket,
                    Key=f"{self.metadata_folder}/{doc_id}.json"
                )
                metadata = json.loads(metadata_obj['Body'].read().decode('utf-8'))
                document_folder = metadata.get('folder')
                
                # Delete the document folder
                if document_folder:
                    self.s3_service.delete_folder(document_folder)
                
                # Delete the metadata file
                self.s3_service.s3_client.delete_object(
                    Bucket=self.s3_service.master_bucket,
                    Key=f"{self.metadata_folder}/{doc_id}.json"
                )
                
                # Delete from vector database
                self.vector_db_service.delete_document(doc_id)
                
                return True
            except Exception as e:
                print(f"Error deleting document {doc_id}: {str(e)}")
                return False
        except Exception as e:
            print(f"Error deleting document {doc_id}: {str(e)}")
            return False
    
    def get_folder_info(self) -> Dict[str, Any]:
        """Get information about available folders"""
        try:
            folders = self.s3_service.list_folders()
            return {
                "master_bucket": self.s3_service.master_bucket,
                "folders": folders
            }
        except Exception as e:
            raise Exception(f"Error getting folder info: {str(e)}") 