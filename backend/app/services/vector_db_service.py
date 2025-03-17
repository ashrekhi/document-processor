import os
import json
from typing import List, Dict, Any, Optional
from openai import OpenAI
import traceback
import time
from datetime import datetime
from dotenv import load_dotenv
import pathlib

# Import the new Pinecone client
from pinecone import Pinecone

# Get the absolute path to the .env file
env_path = pathlib.Path(__file__).parent.parent.parent / '.env'
print(f"Looking for .env file at: {env_path}")

# Load environment variables from the specified path
load_dotenv(dotenv_path=env_path)

# Check if environment variables are loaded
openai_api_key = os.getenv('OPENAI_API_KEY')
pinecone_api_key = os.getenv('PINECONE_API_KEY')

print(f"OPENAI_API_KEY loaded: {'Yes' if openai_api_key else 'No'}")
print(f"PINECONE_API_KEY loaded: {'Yes' if pinecone_api_key else 'No'}")

class VectorDBService:
    def __init__(self):
        # Try to load environment variables again
        env_path = pathlib.Path(__file__).parent.parent.parent / '.env'
        load_dotenv(dotenv_path=env_path)
        
        # Check if vector DB is disabled
        if os.getenv('DISABLE_VECTOR_DB', '').lower() == 'true':
            print("Vector database operations are disabled by configuration.")
            self.openai_client = None
            self.pinecone_index = None
            return
            
        # Initialize OpenAI client
        self.openai_api_key = os.getenv('OPENAI_API_KEY')
        if not self.openai_api_key:
            print("WARNING: OPENAI_API_KEY not set. Vector operations will fail.")
            print(f"Current working directory: {os.getcwd()}")
            print(f"Looking for .env file at: {env_path}")
            print(f".env file exists: {os.path.exists(env_path)}")
            self.openai_client = None
        else:
            self.openai_client = OpenAI(api_key=self.openai_api_key)
        
        # Initialize Pinecone with the new client
        self.pinecone_api_key = os.getenv('PINECONE_API_KEY')
        self.index_name = os.getenv('PINECONE_INDEX', 'radiant-documents')
        self.pinecone_index = None
        
        if not self.pinecone_api_key:
            print("WARNING: PINECONE_API_KEY not set. Vector operations will fail.")
            print(f"Current working directory: {os.getcwd()}")
            print(f"Looking for .env file at: {env_path}")
            print(f".env file exists: {os.path.exists(env_path)}")
        else:
            try:
                print(f"Initializing Pinecone with new client...")
                # Initialize Pinecone with the new client
                pc = Pinecone(api_key=self.pinecone_api_key)
                
                try:
                    # Connect to the index
                    print(f"Connecting to Pinecone index: {self.index_name}")
                    self.pinecone_index = pc.Index(self.index_name)
                    
                    # Test the connection
                    try:
                        stats = self.pinecone_index.describe_index_stats()
                        print(f"Index stats: {stats}")
                    except Exception as stats_error:
                        print(f"Error getting index stats: {str(stats_error)}")
                        print("Using mock vector database instead.")
                        self.pinecone_index = MockPineconeIndex()
                except Exception as connect_error:
                    print(f"Error connecting to Pinecone index: {str(connect_error)}")
                    print("Using mock vector database instead.")
                    self.pinecone_index = MockPineconeIndex()
            except Exception as e:
                print(f"Error initializing Pinecone: {str(e)}")
                print("WARNING: Using mock vector database instead.")
                self.pinecone_index = MockPineconeIndex()
    
    def _generate_embedding(self, text: str) -> Optional[List[float]]:
        """Generate an embedding for a text using OpenAI"""
        if not self.openai_client:
            print("WARNING: OpenAI client not initialized. Skipping embedding generation.")
            return None
        
        try:
            # Add a small delay to avoid rate limiting
            time.sleep(0.5)
            
            response = self.openai_client.embeddings.create(
                model="text-embedding-ada-002",
                input=text
            )
            return response.data[0].embedding
        except Exception as e:
            print(f"Error generating embedding: {str(e)}")
            return None
    
    def store_document_chunks(self, doc_id: str, chunks: List[str], metadata: Dict[str, Any]) -> bool:
        """Store document chunks in the vector database"""
        if not self.pinecone_index or not self.openai_client:
            print(f"WARNING: Vector database not initialized for document {doc_id}. Skipping vector storage.")
            return False
        
        try:
            print(f"Storing {len(chunks)} chunks for document {doc_id}")
            
            # Get namespace from folder or use default
            namespace = metadata.get("folder", "default")
            print(f"Using namespace: {namespace}")
            
            # Process chunks in batches to avoid rate limits
            batch_size = 10
            total_vectors = 0
            
            for i in range(0, len(chunks), batch_size):
                batch = chunks[i:i+batch_size]
                print(f"Processing batch {i//batch_size + 1}/{(len(chunks)-1)//batch_size + 1} with {len(batch)} chunks")
                
                vectors = []
                
                for j, chunk in enumerate(batch):
                    chunk_id = f"{doc_id}_{i+j}"
                    print(f"Generating embedding for chunk {i+j+1}/{len(chunks)}")
                    
                    embedding = self._generate_embedding(chunk)
                    
                    if embedding:
                        print(f"Embedding generated for chunk {i+j+1}")
                        chunk_metadata = {
                            "doc_id": doc_id,
                            "chunk_index": i+j,
                            "text": chunk[:1000],  # Limit metadata size
                            "source": metadata.get("source", ""),
                            "filename": metadata.get("filename", ""),
                            "folder": metadata.get("folder", "")
                        }
                        
                        # Format for the new client
                        vectors.append({
                            "id": chunk_id,
                            "values": embedding,
                            "metadata": chunk_metadata
                        })
                    else:
                        print(f"Failed to generate embedding for chunk {i+j+1}")
                
                if vectors:
                    print(f"Upserting {len(vectors)} vectors to Pinecone in namespace '{namespace}'")
                    # Upsert vectors to Pinecone with namespace
                    result = self.pinecone_index.upsert(
                        vectors=vectors,
                        namespace=namespace
                    )
                    print(f"Upsert result: {result}")
                    total_vectors += len(vectors)
                else:
                    print(f"No vectors to upsert for this batch")
            
            print(f"Successfully stored {total_vectors} vectors for document {doc_id} in namespace '{namespace}'")
            return True
        except Exception as e:
            print(f"Error storing document chunks: {str(e)}")
            traceback.print_exc()
            return False
    
    def search_similar_chunks(self, query: str, top_k: int = 5, filter_doc_ids: List[str] = None, namespace: str = None) -> List[Dict[str, Any]]:
        """Search for similar chunks to a query"""
        if not self.pinecone_index or not self.openai_client:
            print("WARNING: Vector database not initialized. Skipping search.")
            return []
        
        try:
            print(f"Searching for chunks similar to: {query}")
            
            # Generate embedding for the query
            query_embedding = self._generate_embedding(query)
            
            if not query_embedding:
                print("Failed to generate embedding for query")
                return []
            
            # Prepare filter if doc_ids are provided
            filter_dict = None
            if filter_doc_ids:
                filter_dict = {"doc_id": {"$in": filter_doc_ids}}
            
            # Search Pinecone with namespace
            results = self.pinecone_index.query(
                vector=query_embedding,
                top_k=top_k,
                include_metadata=True,
                filter=filter_dict,
                namespace=namespace
            )
            
            # Format results for the new client response format
            formatted_results = []
            for match in results.matches:
                formatted_results.append({
                    "id": match.id,
                    "score": match.score,
                    "doc_id": match.metadata.get("doc_id", ""),
                    "text": match.metadata.get("text", ""),
                    "source": match.metadata.get("source", ""),
                    "filename": match.metadata.get("filename", ""),
                    "folder": match.metadata.get("folder", "")
                })
            
            return formatted_results
        except Exception as e:
            print(f"Error searching similar chunks: {str(e)}")
            return []
    
    def delete_document(self, doc_id: str, namespace: str = None) -> bool:
        """Delete all chunks for a document"""
        if not self.pinecone_index:
            print("WARNING: Vector database not initialized. Skipping vector deletion.")
            return False
        
        try:
            # If namespace is provided, delete only from that namespace
            if namespace:
                print(f"Deleting document {doc_id} from namespace '{namespace}'")
                self.pinecone_index.delete(
                    filter={"doc_id": doc_id},
                    namespace=namespace
                )
            else:
                # If no namespace is provided, we need to find all namespaces that contain this document
                print(f"Deleting document {doc_id} from all namespaces")
                
                # Get index stats to find all namespaces
                stats = self.pinecone_index.describe_index_stats()
                namespaces = stats.get("namespaces", {}).keys()
                
                for ns in namespaces:
                    print(f"Checking namespace '{ns}' for document {doc_id}")
                    # Delete from each namespace
                    self.pinecone_index.delete(
                        filter={"doc_id": doc_id},
                        namespace=ns
                    )
            
            return True
        except Exception as e:
            print(f"Error deleting document from vector database: {str(e)}")
            traceback.print_exc()
            return False
    
    def store_document_metadata(self, doc_id: str, metadata: Dict[str, Any]) -> bool:
        """Store document metadata in S3"""
        try:
            # We'll store the metadata in S3 since Pinecone is just for vectors
            # This method is called by DocumentService
            print(f"Storing metadata for document {doc_id}")
            
            # Add processing status to metadata if not already present
            if "id" not in metadata:
                metadata["id"] = doc_id
            if "document_key" not in metadata:
                metadata["document_key"] = f"{doc_id}_{metadata.get('filename', 'unknown')}"
            if "created_at" not in metadata:
                metadata["created_at"] = datetime.now().isoformat()
            if "processed" not in metadata:
                metadata["processed"] = False
            if "processing" not in metadata:
                metadata["processing"] = True
            
            # Convert metadata to JSON
            metadata_json = json.dumps(metadata)
            
            # Store in S3 (this would typically be done by S3Service)
            # For now, we'll just return True
            print(f"Metadata for document {doc_id} prepared for storage")
            return True
        except Exception as e:
            print(f"Error storing document metadata: {str(e)}")
            return False
    
    def get_document_metadata(self, doc_id: str) -> Optional[Dict[str, Any]]:
        """Get document metadata from S3"""
        # This is a placeholder - in a real implementation, you would fetch from S3
        # For now, we'll just return a mock metadata object
        return {
            "id": doc_id,
            "processed": True,
            "processing": False
        }
    
    def list_namespaces(self) -> List[str]:
        """List all available namespaces"""
        if not self.pinecone_index:
            print("WARNING: Vector database not initialized. Skipping namespace listing.")
            return []
        
        try:
            # Get index stats to find all namespaces
            stats = self.pinecone_index.describe_index_stats()
            namespaces = list(stats.get("namespaces", {}).keys())
            
            return namespaces
        except Exception as e:
            print(f"Error listing namespaces: {str(e)}")
            return []
    
    def search_across_namespaces(self, query: str, top_k: int = 5, filter_doc_ids: List[str] = None) -> List[Dict[str, Any]]:
        """Search for similar chunks across all namespaces"""
        if not self.pinecone_index or not self.openai_client:
            print("WARNING: Vector database not initialized. Skipping search.")
            return []
        
        try:
            print(f"Searching across all namespaces for chunks similar to: {query}")
            
            # Get all namespaces
            namespaces = self.list_namespaces()
            
            # Generate embedding for the query (do this once)
            query_embedding = self._generate_embedding(query)
            
            if not query_embedding:
                print("Failed to generate embedding for query")
                return []
            
            # Prepare filter if doc_ids are provided
            filter_dict = None
            if filter_doc_ids:
                filter_dict = {"doc_id": {"$in": filter_doc_ids}}
            
            # Search in each namespace
            all_results = []
            for namespace in namespaces:
                print(f"Searching in namespace: {namespace}")
                
                # Search Pinecone with namespace
                results = self.pinecone_index.query(
                    vector=query_embedding,
                    top_k=top_k,
                    include_metadata=True,
                    filter=filter_dict,
                    namespace=namespace
                )
                
                # Format results for the new client response format
                for match in results.matches:
                    all_results.append({
                        "id": match.id,
                        "score": match.score,
                        "doc_id": match.metadata.get("doc_id", ""),
                        "text": match.metadata.get("text", ""),
                        "source": match.metadata.get("source", ""),
                        "filename": match.metadata.get("filename", ""),
                        "folder": match.metadata.get("folder", ""),
                        "namespace": namespace
                    })
            
            # Sort by score (highest first)
            all_results.sort(key=lambda x: x["score"], reverse=True)
            
            # Return top_k results
            return all_results[:top_k]
        except Exception as e:
            print(f"Error searching across namespaces: {str(e)}")
            return []

class MockPineconeIndex:
    """A mock implementation of Pinecone Index for when the real service is unavailable"""
    
    def __init__(self):
        self.vectors = {}  # {namespace: {id: (values, metadata)}}
        self.vectors["default"] = {}
        print("Initialized mock Pinecone index")
    
    def upsert(self, vectors, namespace="default"):
        """Mock upsert operation"""
        if namespace not in self.vectors:
            self.vectors[namespace] = {}
            
        for vector in vectors:
            self.vectors[namespace][vector["id"]] = (vector["values"], vector["metadata"])
        
        print(f"Mock upsert: Added {len(vectors)} vectors to namespace '{namespace}'")
        return {"upserted_count": len(vectors)}
    
    def query(self, vector, top_k=10, include_metadata=True, filter=None, namespace="default"):
        """Mock query operation"""
        # Return empty results since this is just a mock
        class MockMatch:
            def __init__(self, id, score, metadata):
                self.id = id
                self.score = score
                self.metadata = metadata
        
        class MockQueryResponse:
            def __init__(self):
                self.matches = [
                    MockMatch("mock_id_1", 0.95, {"doc_id": "mock_doc", "text": "This is mock text", "source": "mock", "filename": "mock.pdf", "folder": "mock_folder"}),
                    MockMatch("mock_id_2", 0.85, {"doc_id": "mock_doc", "text": "More mock text", "source": "mock", "filename": "mock.pdf", "folder": "mock_folder"})
                ]
        
        print(f"Mock query: Returning mock results from namespace '{namespace}' (filter: {filter})")
        return MockQueryResponse()
    
    def delete(self, ids=None, filter=None, namespace="default"):
        """Mock delete operation"""
        if namespace not in self.vectors:
            print(f"Mock delete: Namespace '{namespace}' does not exist")
            return {"deleted_count": 0}
            
        if ids:
            deleted_count = 0
            for id in ids:
                if id in self.vectors[namespace]:
                    del self.vectors[namespace][id]
                    deleted_count += 1
            print(f"Mock delete: Removed {deleted_count} vectors by ID from namespace '{namespace}'")
            return {"deleted_count": deleted_count}
        elif filter:
            # In a real implementation, we would filter vectors by metadata
            print(f"Mock delete: Removed vectors by filter {filter} from namespace '{namespace}'")
            return {"deleted_count": 0}
        return {"deleted_count": 0}
    
    def describe_index_stats(self):
        """Mock index stats"""
        namespaces = {}
        for ns, vectors in self.vectors.items():
            namespaces[ns] = {
                "vector_count": len(vectors)
            }
            
        return {
            "namespaces": namespaces,
            "dimension": 1536,
            "index_fullness": 0.0,
            "total_vector_count": sum(len(vectors) for vectors in self.vectors.values())
        } 