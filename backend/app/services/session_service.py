import json
import os
import uuid
import re
from typing import List, Dict, Any, Optional
from datetime import datetime

from app.services.s3_service import S3Service
from app.services.vector_db_service import VectorDBService
from app.services.document_service import DocumentService

class SessionService:
    """Service for managing document processing sessions and folder organization"""
    
    def __init__(self, s3_service: S3Service):
        self.s3_service = s3_service
        self.vector_db_service = VectorDBService()
        self.document_service = DocumentService(s3_service)
        self.sessions_folder = "sessions"
        self.session_metadata_folder = "session_metadata"
        
        # Ensure required folders exist
        try:
            self.s3_service.create_folder(self.sessions_folder)
            self.s3_service.create_folder(self.session_metadata_folder)
        except Exception as e:
            print(f"Error ensuring session folders: {str(e)}")
    
    def create_session(self, name: str, description: str = None, similarity_threshold: float = 0.7) -> Dict[str, Any]:
        """Create a new document processing session"""
        try:
            # Generate a unique ID for the session
            session_id = str(uuid.uuid4())
            
            # Create session folder structure
            session_folder = f"{self.sessions_folder}/{session_id}"
            self.s3_service.create_folder(session_folder)
            
            # Create session metadata
            now = datetime.now().isoformat()
            session_metadata = {
                "id": session_id,
                "name": name,
                "description": description,
                "similarity_threshold": similarity_threshold,
                "created_at": now,
                "updated_at": now,
                "active": True,
                "folder_path": session_folder,
                "document_count": 0,
                "folder_count": 0
            }
            
            # Store metadata
            metadata_key = f"{self.session_metadata_folder}/{session_id}.json"
            self.s3_service.upload_file_content(
                self.session_metadata_folder,
                f"{session_id}.json",
                json.dumps(session_metadata).encode('utf-8')
            )
            
            return session_metadata
        except Exception as e:
            print(f"Error creating session: {str(e)}")
            import traceback
            traceback.print_exc()
            raise
    
    def get_session(self, session_id: str) -> Dict[str, Any]:
        """Get session details by ID"""
        try:
            # Get metadata from S3
            metadata_key = f"{self.session_metadata_folder}/{session_id}.json"
            try:
                metadata_obj = self.s3_service.s3_client.get_object(
                    Bucket=self.s3_service.master_bucket,
                    Key=metadata_key
                )
                metadata = json.loads(metadata_obj['Body'].read().decode('utf-8'))
                return metadata
            except Exception as e:
                print(f"Error getting session metadata: {str(e)}")
                raise ValueError(f"Session not found: {session_id}")
        except Exception as e:
            print(f"Error getting session: {str(e)}")
            raise
    
    def update_session(self, session_id: str, name: str = None, description: str = None, 
                       similarity_threshold: float = None, active: bool = None) -> Dict[str, Any]:
        """Update session metadata"""
        try:
            # Get current metadata
            session = self.get_session(session_id)
            
            # Update fields if provided
            if name:
                session["name"] = name
            if description is not None:
                session["description"] = description
            if similarity_threshold is not None:
                session["similarity_threshold"] = similarity_threshold
            if active is not None:
                session["active"] = active
            
            session["updated_at"] = datetime.now().isoformat()
            
            # Store updated metadata
            self.s3_service.upload_file_content(
                self.session_metadata_folder,
                f"{session_id}.json",
                json.dumps(session).encode('utf-8')
            )
            
            return session
        except Exception as e:
            print(f"Error updating session: {str(e)}")
            raise
    
    def list_sessions(self) -> List[Dict[str, Any]]:
        """List all sessions"""
        try:
            # List session metadata files
            response = self.s3_service.s3_client.list_objects_v2(
                Bucket=self.s3_service.master_bucket,
                Prefix=f"{self.session_metadata_folder}/"
            )
            
            sessions = []
            
            if 'Contents' in response:
                for obj in response['Contents']:
                    if obj['Key'].endswith('.json'):
                        try:
                            metadata_obj = self.s3_service.s3_client.get_object(
                                Bucket=self.s3_service.master_bucket,
                                Key=obj['Key']
                            )
                            metadata = json.loads(metadata_obj['Body'].read().decode('utf-8'))
                            sessions.append(metadata)
                        except Exception as e:
                            print(f"Error reading session metadata: {str(e)}")
            
            # Sort by creation date (newest first)
            sessions.sort(key=lambda x: x.get("created_at", ""), reverse=True)
            return sessions
        except Exception as e:
            print(f"Error listing sessions: {str(e)}")
            raise
    
    def delete_session(self, session_id: str) -> bool:
        """Delete a similarity session and all its contents"""
        try:
            # Get session details
            session = self.get_session(session_id)
            session_folder = session["folder_path"]
            
            # Get all documents in this session
            documents = self.get_session_documents(session_id)
            
            # Get all session folders (these are similarity buckets)
            similarity_buckets = self._get_session_folders(session_id)
            
            # First, list all namespaces in the vector database
            all_namespaces = []
            try:
                all_namespaces = self.vector_db_service.list_namespaces()
                print(f"Found {len(all_namespaces)} total namespaces in vector database")
                print(f"Available namespaces: {', '.join(all_namespaces)}")
            except Exception as e:
                print(f"Error listing all namespaces: {str(e)}")
            
            # Step 1: Delete individual document vectors from vector database
            # Using standardized namespace format (full folder path)
            for doc in documents:
                try:
                    doc_id = doc["id"]
                    bucket = doc.get("folder", "")
                    # Use the standardized namespace format
                    full_folder_path = f"{session_folder}/{bucket}"
                    
                    print(f"Deleting document {doc_id} from namespace '{full_folder_path}'")
                    self.vector_db_service.delete_document(doc_id, namespace=full_folder_path)
                    
                    # For backward compatibility, also try the bucket name format
                    try:
                        self.vector_db_service.delete_document(doc_id, namespace=bucket)
                    except Exception:
                        # Ignore failures on the legacy format
                        pass
                except Exception as e:
                    print(f"Error deleting document {doc_id}: {str(e)}")
            
            # Step 2: Identify namespaces to delete - prioritize the standardized format
            namespaces_to_delete = set()
            
            # Primary format: full folder paths for each bucket
            for bucket in similarity_buckets:
                full_bucket_path = f"{session_folder}/{bucket}"
                namespaces_to_delete.add(full_bucket_path)
                print(f"Added standard namespace format: '{full_bucket_path}'")
                
                # For backward compatibility, also add the bucket name
                namespaces_to_delete.add(bucket)
            
            # Also check for session folder as namespace
            namespaces_to_delete.add(session_folder)
            
            # Step 3: Delete each identified namespace
            print(f"Deleting these namespaces: {', '.join(namespaces_to_delete)}")
            for namespace in namespaces_to_delete:
                if namespace in all_namespaces:
                    try:
                        print(f"Deleting namespace '{namespace}' from vector database")
                        self.vector_db_service.delete_namespace(namespace=namespace)
                    except Exception as e:
                        print(f"Error deleting namespace '{namespace}' from vector DB: {str(e)}")
            
            # Step 4: Check for any namespace containing the session ID
            # This catches any potential edge cases or historical namespace formats
            for namespace in all_namespaces:
                if session_id in namespace and namespace not in namespaces_to_delete:
                    try:
                        print(f"Deleting session-related namespace '{namespace}' from vector database")
                        self.vector_db_service.delete_namespace(namespace=namespace)
                    except Exception as e:
                        print(f"Error deleting session-related namespace: {str(e)}")
            
            # Step 5: Delete session folder and contents using S3 service
            self.s3_service.delete_folder(session_folder)
            
            # Step 6: Delete session metadata
            self.s3_service.s3_client.delete_object(
                Bucket=self.s3_service.master_bucket,
                Key=f"{self.session_metadata_folder}/{session_id}.json"
            )
            
            print(f"Successfully deleted similarity session {session_id} and all associated resources")
            return True
        except Exception as e:
            print(f"Error deleting similarity session: {str(e)}")
            raise
    
    def process_document_in_session(self, session_id: str, filename: str, content: bytes) -> Dict[str, Any]:
        """Process a document within a session, automatically organizing it into a folder"""
        try:
            # Get session details
            session = self.get_session(session_id)
            session_folder = session["folder_path"]
            similarity_threshold = session.get("similarity_threshold", 0.7)
            
            # Generate a unique ID for the document
            doc_id = str(uuid.uuid4())
            
            # First, check for similar documents and determine folder
            # Now returns both folder and similarity logs
            result = self._determine_document_folder(session_id, content, filename, similarity_threshold)
            
            if isinstance(result, tuple) and len(result) == 2:
                bucket, similarity_logs = result
            else:
                # For backward compatibility
                bucket = result
                similarity_logs = {"comparisons": [], "folders_checked": [], "final_folder": bucket}
                
            print(f"Determined folder for document: {bucket}")
            
            # Now process the document with the determined folder
            full_folder_path = f"{session_folder}/{bucket}"
            
            # Create the folder if it doesn't exist
            self.s3_service.create_folder(full_folder_path)
            
            # Diagnostic: Log namespace information
            try:
                all_namespaces = self.vector_db_service.list_namespaces()
                print(f"DEBUG - Current namespaces before document processing: {', '.join(all_namespaces)}")
            except Exception as e:
                print(f"DEBUG - Error listing namespaces for diagnostics: {str(e)}")
            
            # IMPORTANT: Always use the full folder path as the namespace for consistency
            print(f"DEBUG - Using full folder path as namespace: {full_folder_path}")
            
            # Process the document - Pass the full folder path to ensure consistent namespace naming
            doc_id = self.document_service.process_document(
                filename=filename,
                content=content,
                folder=full_folder_path,
                doc_id=doc_id
            )
            
            # Diagnostic: Check namespaces after processing
            try:
                all_namespaces_after = self.vector_db_service.list_namespaces()
                new_namespaces = set(all_namespaces_after) - set(all_namespaces) if 'all_namespaces' in locals() else set()
                if new_namespaces:
                    print(f"DEBUG - New namespaces created: {', '.join(new_namespaces)}")
                print(f"DEBUG - Document namespace used for {doc_id} is standardized to: {full_folder_path}")
            except Exception as e:
                print(f"DEBUG - Error during namespace diagnostics: {str(e)}")
            
            # Update session metadata
            self._update_session_document_count(session_id)
            
            # Return document details
            document = {
                "id": doc_id,
                "filename": filename,
                "folder": bucket,  # Keep using bucket name for UI display
                "full_folder_path": full_folder_path,
                "session_id": session_id,
                "upload_date": datetime.now().isoformat(),
                "size": len(content),
                "similarity_logs": similarity_logs
            }
            
            return document
        except Exception as e:
            print(f"Error processing document in session: {str(e)}")
            import traceback
            traceback.print_exc()
            raise
    
    def _determine_document_folder(self, session_id: str, content: bytes, filename: str, 
                                  similarity_threshold: float) -> tuple:
        """Determine the best similarity bucket for a document based on similarity to existing docs
        
        Returns:
            tuple: (bucket_name, similarity_logs)
            
        Note: The bucket_name returned is just the bucket identifier (e.g., "bucket1").
        The full namespace path used in vector storage will be "{session_folder}/{bucket_name}"
        """
        try:
            # Create a log structure to capture similarity information
            similarity_logs = {
                "comparisons": [],
                "folders_checked": [],
                "final_folder": None,
                "is_new_folder": False,
                "placement_reason": None,
                "threshold": similarity_threshold
            }
            
            # Get session details
            session = self.get_session(session_id)
            session_folder = session["folder_path"]
            
            # Extract text from the document
            text = self.document_service._extract_text(filename, content)
            
            # If this is the first document, put it in 'bucket1' 
            # Get existing similarity buckets in the session
            similarity_buckets = self._get_session_folders(session_id)
            similarity_logs["folders_checked"] = similarity_buckets.copy()
            
            if not similarity_buckets or len(similarity_buckets) == 0:
                first_bucket = "bucket1"
                similarity_logs["final_folder"] = first_bucket
                similarity_logs["is_new_folder"] = True
                similarity_logs["placement_reason"] = "First document in session"
                print(f"Creating first bucket '{first_bucket}' for session {session_id}")
                return first_bucket, similarity_logs
            
            # Check similarity with documents in each bucket
            best_bucket = None
            best_similarity = 0.0
            best_doc_id = None
            best_doc_filename = None
            
            # For each existing bucket, get a sample document and compare similarity
            for bucket in similarity_buckets:
                folder_docs = self._get_folder_documents(session_id, bucket)
                
                if not folder_docs:
                    continue
                
                # Try to find the best match in this bucket
                for doc in folder_docs:
                    try:
                        # Get document text from S3
                        doc_id = doc["id"]
                        doc_filename = doc.get("filename", "unknown")
                        full_folder_path = f"{session_folder}/{bucket}"
                        
                        # Calculate similarity
                        similarity_result = self.vector_db_service.calculate_document_similarity(
                            doc1_text=text, 
                            doc2_text=self._get_document_text(doc_id, full_folder_path), 
                            method="hybrid"
                        )
                        
                        similarity = similarity_result.get("similarity", 0.0)
                        
                        # Log this comparison
                        comparison_log = {
                            "doc1_id": "new_document",
                            "doc1_name": filename,
                            "doc2_id": doc_id,
                            "doc2_name": doc_filename,
                            "similarity": similarity,
                            "folder": bucket,
                            "method": similarity_result.get("method", "hybrid"),
                            "decision": "Not a match" if similarity < similarity_threshold else "Match found"
                        }
                        similarity_logs["comparisons"].append(comparison_log)
                        
                        # Update best match if this is better
                        if similarity > best_similarity:
                            best_similarity = similarity
                            best_bucket = bucket
                            best_doc_id = doc_id
                            best_doc_filename = doc_filename
                            
                        # If we found a very good match, stop searching
                        if similarity > 0.9:
                            break
                    except Exception as e:
                        print(f"Error comparing with document {doc.get('id')}: {str(e)}")
                        continue
            
            # If we found a good enough match, use that bucket
            if best_bucket and best_similarity >= similarity_threshold:
                print(f"Found similar document with score {best_similarity:.2f} in bucket '{best_bucket}'")
                similarity_logs["final_folder"] = best_bucket
                similarity_logs["is_new_folder"] = False
                similarity_logs["placement_reason"] = f"Similar to document '{best_doc_filename}' with score {best_similarity:.2f}"
                return best_bucket, similarity_logs
            
            # Otherwise, create a new bucket with standard "bucketX" naming
            # Find the highest bucket number and increment
            highest_bucket_num = 0
            bucket_pattern = r'bucket(\d+)'
            
            for bucket in similarity_buckets:
                match = re.search(bucket_pattern, bucket)
                if match:
                    try:
                        bucket_num = int(match.group(1))
                        highest_bucket_num = max(highest_bucket_num, bucket_num)
                    except ValueError:
                        continue
            
            # Create the next bucket in sequence
            next_bucket_num = highest_bucket_num + 1
            new_bucket = f"bucket{next_bucket_num}"
            
            print(f"Creating new similarity bucket '{new_bucket}' for document (best similarity was {best_similarity:.2f})")
            similarity_logs["final_folder"] = new_bucket
            similarity_logs["is_new_folder"] = True
            
            if best_similarity > 0:
                similarity_logs["placement_reason"] = f"Best match was {best_similarity:.2f} with document in '{best_bucket}' bucket, below threshold of {similarity_threshold}"
            else:
                similarity_logs["placement_reason"] = "No similar documents found"
                
            return new_bucket, similarity_logs
        except Exception as e:
            print(f"Error determining similarity bucket: {str(e)}")
            import traceback
            traceback.print_exc()
            # Default to a numbered bucket
            similarity_buckets = self._get_session_folders(session_id)
            highest_bucket_num = 0
            bucket_pattern = r'bucket(\d+)'
            
            for bucket in similarity_buckets:
                match = re.search(bucket_pattern, bucket)
                if match:
                    try:
                        bucket_num = int(match.group(1))
                        highest_bucket_num = max(highest_bucket_num, bucket_num)
                    except ValueError:
                        continue
            
            next_bucket_num = highest_bucket_num + 1
            folder_name = f"bucket{next_bucket_num}"
            
            return folder_name, {
                "comparisons": [],
                "folders_checked": [],
                "final_folder": folder_name,
                "is_new_folder": True,
                "placement_reason": f"Error during similarity check: {str(e)}"
            }
    
    def _get_session_folders(self, session_id: str) -> List[str]:
        """Get a list of folders in a session"""
        try:
            session = self.get_session(session_id)
            session_folder = session["folder_path"]
            
            # List objects with the session folder prefix
            response = self.s3_service.s3_client.list_objects_v2(
                Bucket=self.s3_service.master_bucket,
                Prefix=f"{session_folder}/",
                Delimiter='/'
            )
            
            folders = []
            if 'CommonPrefixes' in response:
                for prefix in response['CommonPrefixes']:
                    full_prefix = prefix['Prefix']
                    # Extract just the folder name without the session path
                    folder_name = full_prefix.replace(f"{session_folder}/", "").rstrip('/')
                    if folder_name:
                        folders.append(folder_name)
            
            return folders
        except Exception as e:
            print(f"Error getting session folders: {str(e)}")
            return []
    
    def _get_folder_documents(self, session_id: str, folder: str) -> List[Dict[str, Any]]:
        """Get documents in a specific folder of a session"""
        try:
            session = self.get_session(session_id)
            session_folder = session["folder_path"]
            full_folder_path = f"{session_folder}/{folder}"
            
            # List document objects in this folder
            documents = []
            
            # Get document metadata from S3
            response = self.s3_service.s3_client.list_objects_v2(
                Bucket=self.s3_service.master_bucket,
                Prefix=f"{full_folder_path}/"
            )
            
            if 'Contents' in response:
                for obj in response['Contents']:
                    key = obj['Key']
                    # Skip folder markers
                    if key.endswith('/'):
                        continue
                    
                    # Extract document ID from key
                    parts = key.split('/')
                    if len(parts) > 1:
                        file_name = parts[-1]
                        if '_' in file_name:
                            doc_id = file_name.split('_')[0]
                            documents.append({
                                "id": doc_id,
                                "key": key,
                                "folder": folder,
                                "filename": file_name
                            })
            
            return documents
        except Exception as e:
            print(f"Error getting folder documents: {str(e)}")
            return []
    
    def _get_document_text(self, doc_id: str, folder: str) -> str:
        """Get the text content of a document"""
        try:
            # Get document metadata to find the actual file
            metadata_key = f"metadata/{doc_id}.json"
            try:
                metadata_obj = self.s3_service.s3_client.get_object(
                    Bucket=self.s3_service.master_bucket,
                    Key=metadata_key
                )
                metadata = json.loads(metadata_obj['Body'].read().decode('utf-8'))
                filename = metadata.get("filename", "")
                
                # Get document content
                doc_key = f"{metadata.get('folder', folder)}/{doc_id}_{filename}"
                
                # Download file
                file_obj = self.s3_service.s3_client.get_object(
                    Bucket=self.s3_service.master_bucket,
                    Key=doc_key
                )
                content = file_obj['Body'].read()
                
                # Extract text
                text = self.document_service._extract_text(filename, content)
                return text
            except Exception as e:
                print(f"Error getting document content: {str(e)}")
                return ""
        except Exception as e:
            print(f"Error extracting document text: {str(e)}")
            return ""
    
    def _update_session_document_count(self, session_id: str):
        """Update document and folder count in session metadata"""
        try:
            session = self.get_session(session_id)
            folders = self._get_session_folders(session_id)
            
            document_count = 0
            for folder in folders:
                folder_docs = self._get_folder_documents(session_id, folder)
                document_count += len(folder_docs)
            
            # Update session metadata
            session["document_count"] = document_count
            session["folder_count"] = len(folders)
            session["updated_at"] = datetime.now().isoformat()
            
            # Save updated metadata
            self.s3_service.upload_file_content(
                self.session_metadata_folder,
                f"{session_id}.json",
                json.dumps(session).encode('utf-8')
            )
        except Exception as e:
            print(f"Error updating session document count: {str(e)}")
    
    def get_session_documents(self, session_id: str) -> List[Dict[str, Any]]:
        """Get all documents in a session across all folders"""
        try:
            session = self.get_session(session_id)
            folders = self._get_session_folders(session_id)
            
            documents = []
            for folder in folders:
                folder_docs = self._get_folder_documents(session_id, folder)
                
                # Add folder info to each document
                for doc in folder_docs:
                    doc["session_id"] = session_id
                    doc["session_name"] = session.get("name", "")
                    documents.append(doc)
            
            return documents
        except Exception as e:
            print(f"Error getting session documents: {str(e)}")
            return []
    
    def get_session_folder_stats(self, session_id: str) -> List[Dict[str, Any]]:
        """Get statistics for each folder in a session"""
        try:
            session = self.get_session(session_id)
            folders = self._get_session_folders(session_id)
            
            folder_stats = []
            for folder in folders:
                folder_docs = self._get_folder_documents(session_id, folder)
                
                folder_stats.append({
                    "folder": folder,
                    "document_count": len(folder_docs),
                    "documents": folder_docs
                })
            
            return folder_stats
        except Exception as e:
            print(f"Error getting session folder stats: {str(e)}")
            return []
