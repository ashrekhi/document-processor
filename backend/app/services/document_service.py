import json
import os
import fitz  # PyMuPDF
from io import BytesIO
from typing import List, Dict, Any, Optional
from datetime import datetime
import uuid
import inspect
import time

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
    
    def process_document(self, filename: str, content: bytes, folder: str = None, doc_id: str = None, source_name: str = None, description: str = None, custom_prompt: str = None,
                        prompt_model: str = "gpt-3.5-turbo") -> str:
        """Process a document and store it in the database"""
        try:
            print(f"Processing document: {filename} (size: {len(content)} bytes)")
            
            # Generate a unique ID for the document if not provided
            if not doc_id:
                doc_id = str(uuid.uuid4())
            
            # Use source_name as folder if provided
            if source_name and not folder:
                folder = source_name
            
            # Extract text from the document
            print(f"Extracting text from document...")
            text = self._extract_text(filename, content)
            print(f"Extracted {len(text)} characters of text")
            
            # Split text into chunks
            print(f"Splitting text into chunks...")
            chunks = self._split_text(text)
            print(f"Split text into {len(chunks)} chunks")
            
            # Store the document metadata
            metadata = {
                "filename": filename,
                "folder": folder or "root",
                "upload_date": datetime.now().isoformat(),
                "size": len(content),
                "source": source_name or "upload",
                "document_key": f"{doc_id}_{filename}",
                "custom_prompt": custom_prompt,
                "prompt_model": prompt_model
            }
            
            # Store metadata in S3
            metadata_key = f"{self.metadata_folder}/{doc_id}.json"
            self.s3_service.upload_file_content(
                self.metadata_folder,
                f"{doc_id}.json",
                json.dumps(metadata).encode('utf-8')
            )
            
            # Also store metadata in vector DB service
            self.vector_db_service.store_document_metadata(doc_id, metadata)
            
            # Store the document content
            self.s3_service.upload_file(folder or "root", f"{doc_id}_{filename}", content)
            
            # Store document chunks in vector database
            print(f"Storing document chunks in vector database...")
            success = self.vector_db_service.store_document_chunks(doc_id, chunks, metadata)
            
            if success:
                # Update metadata to mark document as processed
                metadata["processed"] = True
                metadata["processing"] = False
                self.s3_service.upload_file_content(
                    self.metadata_folder,
                    f"{doc_id}.json",
                    json.dumps(metadata).encode('utf-8')
                )
                print(f"Document processing completed successfully: {filename}")
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
    
    def _split_text(self, text: str, chunk_size: int = 1500, overlap: int = 300) -> List[str]:
        """Split text into overlapping chunks safely, avoiding infinite loops."""
        print(f"Starting text splitting: length={len(text)}, chunk_size={chunk_size}, overlap={overlap}")
        
        # Print a sample of the text to ensure it looks correct
        text_sample = text[:300] + "..." if len(text) > 300 else text
        print(f"Sample of text to split: '{text_sample}'")
        
        chunks = []
        
        # Safety check for invalid inputs
        if chunk_size <= 0:
            print(f"WARNING: Invalid chunk_size ({chunk_size}). Resetting to default 1500.")
            chunk_size = 1500
        if overlap >= chunk_size:
            print(f"WARNING: Overlap ({overlap}) >= chunk_size ({chunk_size}). Adjusting to {chunk_size // 3}.")
            overlap = chunk_size // 3  # Set overlap to 1/3 of chunk size if invalid
        
        # If text is smaller than chunk size, return it as a single chunk
        if len(text) <= chunk_size:
            print(f"Text is smaller than chunk_size. Using as single chunk.")
            chunks.append(text)
            print(f"Text splitting complete: created 1 chunk")
            return chunks
        
        # Track positions to detect lack of progress
        start = 0
        prev_start = -1
        chunk_count = 0
        max_chunks = max(100, (len(text) // (chunk_size - overlap)) * 2)  # Conservative upper bound, minimum 100
        print(f"Maximum allowed chunks: {max_chunks} (based on text length and chunk parameters)")
        
        while start < len(text) and chunk_count < max_chunks:
            # Check if we're making progress
            if start == prev_start:
                print(f"WARNING: No progress in chunking (stuck at position {start}/{len(text)}). Breaking loop.")
                # Add the remaining text as the final chunk and break
                final_chunk = text[start:].strip()
                if final_chunk:
                    print(f"Adding final chunk of length {len(final_chunk)} characters")
                    chunks.append(final_chunk)
                break
            
            prev_start = start
            end = start + chunk_size
            print(f"\nProcessing chunk {chunk_count+1}: start={start}, initial end={end}")
            
            # If we've reached the end of the text
            if end >= len(text):
                print(f"End position {end} exceeds text length {len(text)}. This is the final chunk.")
                # Add the final chunk and break
                final_chunk = text[start:].strip()
                print(f"Adding final chunk of length {len(final_chunk)} characters")
                chunks.append(final_chunk)
                chunk_count += 1
                break
                
            # Try to find a good break point
            original_end = end
            
            # Look for paragraph break
            next_break = text.find('\n\n', end - min(chunk_size//2, 500), end)
            if next_break != -1:
                print(f"Found paragraph break at position {next_break} (looking in range {end - min(chunk_size//2, 500)} to {end})")
                end = next_break + 2  # Include the newlines
            else:
                print(f"No paragraph break found in range {end - min(chunk_size//2, 500)} to {end}")
                
                # Look for sentence break
                next_break = text.find('. ', end - min(chunk_size//2, 500), end)
                if next_break != -1:
                    print(f"Found sentence break at position {next_break}")
                    end = next_break + 2  # Include the period and space
                else:
                    print(f"No sentence break found")
                    
                    # Look for any whitespace as last resort
                    space_pos = text.rfind(' ', end - min(chunk_size//2, 500), end)
                    if space_pos > start + chunk_size // 3:  # Ensure we're not making too small chunks
                        print(f"Found space at position {space_pos}")
                        end = space_pos + 1
                    else:
                        print(f"No suitable space found (best candidate was at {space_pos})")
            
            # Absolute failsafe: if we couldn't find a good break point, force a break at chunk_size
            if end <= start:
                print(f"WARNING: No valid break point found. Forcing break at position {start + chunk_size}.")
                end = start + chunk_size
            
            print(f"Final chunk end position: {end} (adjusted from {original_end})")
                
            # Add the chunk
            chunk = text[start:end].strip()
            if chunk:  # Only add non-empty chunks
                print(f"Adding chunk of length {len(chunk)} characters")
                if len(chunk) < 50:  # If very small, print the whole chunk for debugging
                    print(f"Short chunk content: '{chunk}'")
                chunks.append(chunk)
            else:
                print(f"WARNING: Empty chunk detected. Skipping.")
                
            # CRITICAL: Make sure we advance by at least one character
            new_start = end - overlap
            if new_start <= start:
                print(f"WARNING: New start position {new_start} would not advance past current start {start}. Forcing advancement.")
                new_start = start + 1  # Ensure progress by at least one character
            
            print(f"Advancing to new start position: {new_start} (moved {new_start - start} characters, overlap={overlap})")
            start = new_start
                
            chunk_count += 1
            
            # Print progress only occasionally to reduce log volume
            if chunk_count % 20 == 0 or chunk_count < 5:
                print(f"Text splitting progress: processed {chunk_count} chunks")
                
            # Safety check for unexpected chunk counts
            if chunk_count >= 50 and chunk_count % 50 == 0:
                print(f"WARNING: High chunk count ({chunk_count}) detected. Text length: {len(text)}, chunk_size: {chunk_size}")
                print(f"Current position: {start}/{len(text)} ({(start / len(text) * 100):.1f}% through text)")
                
            # If we've been working for a while and aren't making much progress, abort with a partial result
            if chunk_count >= 100 and start < len(text) * 0.5:
                print(f"WARNING: Processed {chunk_count} chunks but only at {(start / len(text) * 100):.1f}% of text. Stopping early.")
                # Add the rest as a final chunk
                final_chunk = text[start:].strip()
                if final_chunk:
                    print(f"Adding final chunk of length {len(final_chunk)} characters")
                    chunks.append(final_chunk)
                break
        
        # Final safety check - if we hit max_chunks, something is wrong
        if chunk_count >= max_chunks:
            print(f"WARNING: Hit maximum chunk count limit ({max_chunks}). Possible infinite loop detected.")
            print(f"Current position: {start}/{len(text)} ({(start / len(text) * 100):.1f}% through text)")
            
        print(f"Text splitting complete: created {len(chunks)} chunks")
        
        # Additional validation of chunks
        if chunks:
            min_size = min(len(chunk) for chunk in chunks)
            max_size = max(len(chunk) for chunk in chunks)
            print(f"Chunk size statistics: min={min_size}, max={max_size}, avg={sum(len(c) for c in chunks)/len(chunks):.1f}")
        
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
    
    def ask_question_in_folder(self, question: str, folder: str, model: str = "gpt-3.5-turbo") -> str:
        """Ask a question about all documents in a folder"""
        print(f"DOCUMENT SERVICE: Model: '{model}'")
        print(f"DOCUMENT SERVICE: Checking for documents in folder '{folder}'")
        
        try:
            # Get documents in the folder
            documents = self.get_documents_in_folder(folder)
            print(f"DOCUMENT SERVICE: Found {len(documents)} documents in folder '{folder}'")
            
            if not documents:
                return f"No documents found in folder '{folder}'. Please upload documents to this folder first."
            
            print(f"DOCUMENT SERVICE: Searching directly in namespace '{folder}'")
            
            try:
                stats = self.vector_db_service.pinecone_index.describe_index_stats()
                print(f"DOCUMENT SERVICE: Index stats: {stats}")
                
                # Check if the namespace exists and has vectors
                namespaces = stats.get("namespaces", {})
                if folder not in namespaces:
                    print(f"DOCUMENT SERVICE WARNING: Namespace '{folder}' not found in index")
                    return f"No document vectors found for folder '{folder}'. Please ensure documents have been properly processed."
                
                vector_count = namespaces[folder].get("vector_count", 0)
                print(f"DOCUMENT SERVICE: Namespace '{folder}' has {vector_count} vectors")
                
                if vector_count == 0:
                    print(f"DOCUMENT SERVICE WARNING: Namespace '{folder}' exists but has no vectors")
                    return f"The folder '{folder}' exists but doesn't contain any document vectors. Please process documents in this folder first."
            except Exception as stats_error:
                print(f"DOCUMENT SERVICE WARNING: Error getting index stats: {str(stats_error)}")
            
            # Search for relevant chunks directly in the namespace matching the folder
            start_time = time.time()
            chunks = self.vector_db_service.search_similar_chunks(
                query=question,
                top_k=5,
                namespace=folder  # Explicitly use the folder name as namespace
            )
            
            search_time = time.time() - start_time
            print(f"DOCUMENT SERVICE: Found {len(chunks)} relevant chunks in {search_time:.2f} seconds")
            
            # If no chunks found, return a clear message
            if not chunks or len(chunks) == 0:
                print(f"DOCUMENT SERVICE WARNING: No relevant chunks found for query in namespace '{folder}'")
                return f"I couldn't find any relevant information in the documents in folder '{folder}' to answer your question. Please try rephrasing or asking about a different topic."
            
            # Log information about the chunks found
            print(f"DOCUMENT SERVICE: Details of {len(chunks)} chunks:")
            for i, chunk in enumerate(chunks):
                chunk_id = chunk.get('id', 'unknown')
                doc_id = chunk.get('doc_id', 'unknown')
                score = chunk.get('score', 'unknown')
                text_length = len(chunk.get('text', ''))
                print(f"  Chunk {i+1}: ID={chunk_id}, Doc ID={doc_id}, Score={score}, Text length={text_length}")
            
            # Construct context from chunks
            context = ""
            for chunk in chunks:
                chunk_text = chunk.get("text", "")
                if chunk_text:
                    context += f"{chunk_text}\n\n"
            
            print(f"DOCUMENT SERVICE: Total context length: {len(context)} characters")
            
            # Create the prompt for OpenAI
            prompt = f"""
            You are an AI assistant that helps answer questions based on the provided document context.
            Answer the following question based ONLY on the information provided in the context below.
            If you can't find the answer in the context, say "I don't see specific information about that in the provided documents. The documents in folder '{folder}' appear to contain information about [brief summary of what IS in the documents based on the context]."
            Don't use prior knowledge. Be concise and to the point.
            
            Context:
            {context}
            
            Question: {question}
            
            Answer:
            """
            
            # Call OpenAI API
            print(f"DOCUMENT SERVICE: Calling OpenAI at {time.strftime('%H:%M:%S')} with model {model}")
            openai_start_time = time.time()
            
            if not hasattr(self.vector_db_service, 'openai_client') or self.vector_db_service.openai_client is None:
                print(f"DOCUMENT SERVICE ERROR: OpenAI client not initialized")
                return "Error: OpenAI API client not initialized. Please check your API key configuration."
            
            response = self.vector_db_service.openai_client.chat.completions.create(
                model=model,
                messages=[
                    {"role": "system", "content": "You are a helpful assistant that answers questions based on document context."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0,
                timeout=30  # 30 second timeout
            )
            
            openai_time = time.time() - openai_start_time
            print(f"DOCUMENT SERVICE: OpenAI API call completed in {openai_time:.2f} seconds")
            
            # Process the response
            answer = response.choices[0].message.content
            answer_length = len(answer) if answer else 0
            print(f"DOCUMENT SERVICE: Received answer of length {answer_length} chars")
            answer_preview = answer[:150].replace('\n', ' ') + '...' if len(answer) > 150 else answer
            print(f"DOCUMENT SERVICE: Answer preview: '{answer_preview}'")
            
            return answer
            
        except Exception as e:
            print(f"DOCUMENT SERVICE ERROR: {str(e)}")
            import traceback
            traceback.print_exc()
            return f"Error processing your question: {str(e)}"
    
    def get_documents_in_folder(self, folder: str) -> List[Dict[str, Any]]:
        """Get all documents in a folder - alias for get_documents_by_namespace"""
        print(f"Getting documents in folder: {folder}")
        return self.get_documents_by_namespace(folder) 