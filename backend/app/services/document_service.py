import json
import os
import fitz  # PyMuPDF
from io import BytesIO
from typing import List, Dict, Any, Optional
from datetime import datetime
import uuid
import inspect

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
    
    def process_document(self, filename: str, content: bytes, folder: str = None, doc_id: str = None, source_name: str = None, description: str = None) -> str:
        """Process a document and store it in the database"""
        try:
            print(f"PROCESS_DOCUMENT: Called with args: filename={filename}, content_length={len(content)}, folder={folder}, doc_id={doc_id}, source_name={source_name}, description={description}")
            print(f"PROCESS_DOCUMENT: Function signature: {inspect.signature(self.process_document)}")
            
            # Print the call stack to see where this method is being called from
            current_frame = inspect.currentframe()
            call_stack = inspect.getouterframes(current_frame)
            print(f"PROCESS_DOCUMENT: Call stack:")
            for i, frame_info in enumerate(call_stack[1:5]):  # Skip the current frame and show the next 4
                print(f"  {i+1}. {frame_info.filename}:{frame_info.lineno} - {frame_info.function}")
            
            # Generate a unique ID for the document if not provided
            if not doc_id:
                doc_id = str(uuid.uuid4())
            print(f"PROCESS_DOCUMENT: Using document ID: {doc_id}")
            
            # Use source_name as folder if provided
            if source_name and not folder:
                folder = source_name
                print(f"PROCESS_DOCUMENT: Using source_name as folder: {folder}")
            
            # Extract text from the document
            print(f"Extracting text from document...")
            text = self._extract_text(filename, content)
            print(f"Extracted {len(text)} characters of text")
            
            # Split text into chunks
            print(f"Splitting text into chunks...")
            chunks = self._split_text(text)
            print(f"Split text into {len(chunks)} chunks")
            
            # Store the document metadata
            print(f"Storing document metadata...")
            metadata = {
                "filename": filename,
                "folder": folder or "root",
                "upload_date": datetime.now().isoformat(),
                "size": len(content),
                "source": source_name or "upload",
                "document_key": f"{doc_id}_{filename}"
            }
            
            # Store metadata in S3
            metadata_key = f"{self.metadata_folder}/{doc_id}.json"
            self.s3_service.upload_file_content(
                self.metadata_folder,
                f"{doc_id}.json",
                json.dumps(metadata).encode('utf-8')
            )
            print(f"Document metadata stored in S3 at {metadata_key}")
            
            # Also store metadata in vector DB service
            self.vector_db_service.store_document_metadata(doc_id, metadata)
            
            # Store the document content
            print(f"Storing document content...")
            self.s3_service.upload_file(folder or "root", f"{doc_id}_{filename}", content)
            print(f"Document content stored")
            
            # Store document chunks in vector database
            print(f"Storing document chunks in vector database...")
            success = self.vector_db_service.store_document_chunks(doc_id, chunks, metadata)
            
            if success:
                print(f"Document chunks stored in vector database")
                
                # Update metadata to mark document as processed
                metadata["processed"] = True
                metadata["processing"] = False
                self.s3_service.upload_file_content(
                    self.metadata_folder,
                    f"{doc_id}.json",
                    json.dumps(metadata).encode('utf-8')
                )
                print(f"Document metadata updated to mark as processed")
            else:
                print(f"Failed to store document chunks in vector database")
                
                # Update metadata to mark document as failed
                metadata["processed"] = False
                metadata["processing"] = False
                metadata["error"] = "Failed to store document chunks in vector database"
                self.s3_service.upload_file_content(
                    self.metadata_folder,
                    f"{doc_id}.json",
                    json.dumps(metadata).encode('utf-8')
                )
                print(f"Document metadata updated to mark as failed")
            
            return doc_id
        except Exception as e:
            print(f"Error processing document: {str(e)}")
            import traceback
            traceback.print_exc()
            raise
    
    def _extract_text(self, filename: str, content: bytes) -> str:
        """Extract text from a document based on file type"""
        file_extension = os.path.splitext(filename)[1].lower()
        
        if file_extension == '.pdf':
            return self._extract_text_from_pdf(BytesIO(content))
        elif file_extension in ['.txt', '.md']:
            return content.decode('utf-8')
        else:
            # For other file types, we could add more extractors
            return f"Unsupported file type: {file_extension}"
    
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
        print(f"_SPLIT_TEXT: Starting with text length: {len(text)}, chunk_size: {chunk_size}, overlap: {overlap}")
        chunks = []
        if len(text) <= chunk_size:
            print(f"_SPLIT_TEXT: Text fits in a single chunk")
            chunks.append(text)
        else:
            start = 0
            chunk_count = 0
            while start < len(text):
                end = start + chunk_size
                if end > len(text):
                    end = len(text)
                    print(f"_SPLIT_TEXT: Reached end of text, final chunk end adjusted to {end}")
                
                original_end = end
                # Try to find a good breaking point (newline or space)
                if end < len(text):
                    # Look for newline first
                    newline_pos = text.rfind('\n', start, end)
                    if newline_pos > start + chunk_size // 2:
                        end = newline_pos + 1
                        print(f"_SPLIT_TEXT: Found newline break at position {newline_pos}, adjusted end to {end}")
                    else:
                        # Look for space
                        space_pos = text.rfind(' ', start, end)
                        if space_pos > start + chunk_size // 2:
                            end = space_pos + 1
                            print(f"_SPLIT_TEXT: Found space break at position {space_pos}, adjusted end to {end}")
                        else:
                            print(f"_SPLIT_TEXT: No good breaking point found, using original end {original_end}")
                
                chunk_text = text[start:end]
                print(f"_SPLIT_TEXT: Chunk {chunk_count}: start={start}, end={end}, length={len(chunk_text)}")
                chunks.append(chunk_text)
                
                start = end - overlap
                print(f"_SPLIT_TEXT: New start position: {start} (with overlap of {overlap})")
                chunk_count += 1
        
        print(f"_SPLIT_TEXT: Created {len(chunks)} chunks")
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
                                "description": metadata.get("description", ""),
                                "folder": metadata["folder"],
                                "created_at": metadata.get("created_at", ""),
                                "s3_url": f"s3://{self.s3_service.master_bucket}/{metadata['folder']}/{metadata['document_key']}"
                            })
                        except Exception as e:
                            print(f"Error loading metadata: {str(e)}")
        except Exception as e:
            print(f"Error listing documents: {str(e)}")
        
        return documents
    
    def delete_document(self, doc_id: str) -> bool:
        """Delete a document and all its data"""
        try:
            # Get metadata to find the document location
            try:
                metadata_obj = self.s3_service.s3_client.get_object(
                    Bucket=self.s3_service.master_bucket,
                    Key=f"{self.metadata_folder}/{doc_id}.json"
                )
                metadata = json.loads(metadata_obj['Body'].read().decode('utf-8'))
                folder = metadata.get('folder')
                document_key = metadata.get('document_key')
                
                # Delete the document file
                if folder and document_key:
                    self.s3_service.s3_client.delete_object(
                        Bucket=self.s3_service.master_bucket,
                        Key=f"{folder}/{document_key}"
                    )
                
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
    
    def get_document_status(self, doc_id: str) -> str:
        """Get the processing status of a document"""
        try:
            # Check if the document metadata exists
            metadata = self.vector_db_service.get_document_metadata(doc_id)
            if not metadata:
                return "not_found"
            
            # Check if the document has been processed
            if "processed" in metadata and metadata["processed"]:
                return "processed"
            
            # Check if the document is being processed
            if "processing" in metadata and metadata["processing"]:
                return "processing"
            
            return "uploaded"
        except Exception as e:
            print(f"Error getting document status: {str(e)}")
            return "error"
    
    def ask_question(self, question: str, doc_ids: List[str] = None, folder: str = None) -> Dict[str, Any]:
        """Ask a question about documents"""
        try:
            # Search for relevant chunks
            namespace = folder if folder else None
            chunks = self.vector_db_service.search_similar_chunks(
                query=question,
                top_k=5,
                filter_doc_ids=doc_ids,
                namespace=namespace
            )
            
            # Format the context from chunks
            context = "\n\n".join([chunk["text"] for chunk in chunks])
            
            # Get answer from OpenAI
            response = self.vector_db_service.openai_client.chat.completions.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": "You are a helpful assistant that answers questions based on the provided context."},
                    {"role": "user", "content": f"Context:\n{context}\n\nQuestion: {question}"}
                ]
            )
            
            answer = response.choices[0].message.content
            
            return {
                "question": question,
                "answer": answer,
                "sources": [
                    {
                        "doc_id": chunk["doc_id"],
                        "filename": chunk["filename"],
                        "score": chunk["score"]
                    }
                    for chunk in chunks
                ]
            }
        except Exception as e:
            print(f"Error asking question: {str(e)}")
            raise
    
    def get_documents_by_namespace(self, namespace: str) -> List[Dict[str, Any]]:
        """Get all documents in a namespace"""
        try:
            documents = []
            
            # List all documents
            all_documents = self.list_documents()
            
            # Filter by folder/namespace
            for doc in all_documents:
                if doc.get("folder") == namespace:
                    documents.append(doc)
            
            return documents
        except Exception as e:
            print(f"Error getting documents by namespace: {str(e)}")
            return []
    
    def ask_question_across_namespaces(self, question: str, doc_ids: List[str] = None) -> Dict[str, Any]:
        """Ask a question across all namespaces"""
        try:
            # Search for relevant chunks across all namespaces
            chunks = self.vector_db_service.search_across_namespaces(
                query=question,
                top_k=5,
                filter_doc_ids=doc_ids
            )
            
            # Format the context from chunks
            context = "\n\n".join([chunk["text"] for chunk in chunks])
            
            # Get answer from OpenAI
            response = self.vector_db_service.openai_client.chat.completions.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": "You are a helpful assistant that answers questions based on the provided context."},
                    {"role": "user", "content": f"Context:\n{context}\n\nQuestion: {question}"}
                ]
            )
            
            answer = response.choices[0].message.content
            
            return {
                "question": question,
                "answer": answer,
                "sources": [
                    {
                        "doc_id": chunk["doc_id"],
                        "filename": chunk["filename"],
                        "score": chunk["score"],
                        "namespace": chunk.get("namespace", "")
                    }
                    for chunk in chunks
                ]
            }
        except Exception as e:
            print(f"Error asking question across namespaces: {str(e)}")
            raise 