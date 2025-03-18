import json
import os
import time
import traceback
from typing import List, Dict, Any, Optional
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
    
    def answer_question(self, question: str, document_ids: List[str], model: str = "gpt-3.5-turbo", prompt_template: Optional[str] = None) -> str:
        """Answer a question based on the documents"""
        print(f"{'='*80}")
        print(f"RAG SERVICE: Starting question answering at {time.strftime('%H:%M:%S')}")
        print(f"RAG SERVICE: Question: '{question}'")
        print(f"RAG SERVICE: Using model: {model}")
        print(f"RAG SERVICE: Document IDs: {document_ids}")
        
        # Log more details about document IDs
        if document_ids:
            for i, doc_id in enumerate(document_ids):
                print(f"RAG SERVICE: Document ID {i+1}: '{doc_id}'")
        
        # Check if any document IDs look malformed
        for i, doc_id in enumerate(document_ids):
            if not isinstance(doc_id, str):
                print(f"RAG SERVICE WARNING: Document ID at position {i} is not a string: {type(doc_id)}")
            elif len(doc_id) < 10:  # Most IDs should be longer
                print(f"RAG SERVICE WARNING: Document ID at position {i} seems unusually short: '{doc_id}'")
            elif not doc_id.strip():
                print(f"RAG SERVICE WARNING: Document ID at position {i} is empty or only whitespace")
        
        # Check OpenAI client
        if not self.client:
            error_msg = "OpenAI client not initialized in RAG service"
            print(f"RAG SERVICE ERROR: {error_msg}")
            return f"Error: {error_msg}. Please check your API keys and try again."
        
        # Validate model
        if not model or model.strip() == "":
            model = "gpt-3.5-turbo"
            print(f"RAG SERVICE: Empty model specified, defaulting to {model}")
        
        # Validate document_ids
        if not document_ids or len(document_ids) == 0:
            error_msg = "No document IDs provided for question answering"
            print(f"RAG SERVICE ERROR: {error_msg}")
            return f"Error: {error_msg}. Please select at least one document to ask questions about."
        
        # Get relevant chunks from vector database
        try:
            print(f"RAG SERVICE: Searching for relevant chunks from {len(document_ids)} document(s)...")
            print(f"RAG SERVICE: Document IDs being searched: {document_ids}")
            
            # Check vector db service initialization
            print(f"RAG SERVICE: Vector DB service type: {type(self.vector_db_service)}")
            
            # Validate the vector db service and Pinecone index
            if not hasattr(self.vector_db_service, 'pinecone_index') or self.vector_db_service.pinecone_index is None:
                print(f"RAG SERVICE ERROR: Vector database service is not properly initialized")
                return "Error: Vector database is not available. Please check your Pinecone configuration."
            
            # Check what type of pinecone index we're using
            index_type = type(self.vector_db_service.pinecone_index).__name__
            print(f"RAG SERVICE: Pinecone index implementation: {index_type}")
            
            # Check if using the mock implementation
            if hasattr(self.vector_db_service.pinecone_index, '__class__') and self.vector_db_service.pinecone_index.__class__.__name__ == 'SimpleMockIndex':
                print(f"RAG SERVICE WARNING: Using mock Pinecone index. Search results will be generic.")
            
            # Get available namespaces
            try:
                namespaces = self.vector_db_service.list_namespaces()
                print(f"RAG SERVICE: Available namespaces: {namespaces}")
                
                # Get index stats
                try:
                    stats = self.vector_db_service.pinecone_index.describe_index_stats()
                    print(f"RAG SERVICE: Index stats: {stats}")
                    
                    # Check if any documents exist in index
                    if "namespaces" in stats:
                        for ns, ns_stats in stats.get("namespaces", {}).items():
                            count = ns_stats.get("vector_count", 0)
                            print(f"RAG SERVICE: Namespace '{ns}' contains {count} vectors")
                except Exception as stats_error:
                    print(f"RAG SERVICE WARNING: Error getting index stats: {str(stats_error)}")
            except Exception as ns_error:
                print(f"RAG SERVICE WARNING: Error listing namespaces: {str(ns_error)}")

            search_start_time = time.time()
            
            # Get a mapping of potential namespaces from document IDs
            doc_namespaces = {}
            found_relevant_chunks = False
            
            # 1. First try with specific namespace if we can detect it
            try:
                # Try to get namespace information for each document by looking at stats
                if "namespaces" in stats:
                    for namespace, ns_stats in stats.get("namespaces", {}).items():
                        if ns_stats.get("vector_count", 0) > 0:
                            print(f"RAG SERVICE: Trying namespace '{namespace}' which has {ns_stats.get('vector_count', 0)} vectors")
                            
                            # Try search in this namespace
                            namespace_search_start = time.time()
                            namespace_chunks = self.vector_db_service.search_similar_chunks(
                                question, 
                                top_k=5, 
                                filter_doc_ids=document_ids,
                                namespace=namespace
                            )
                            namespace_search_time = time.time() - namespace_search_start
                            
                            # If we found chunks, use them
                            if namespace_chunks and len(namespace_chunks) > 0:
                                print(f"RAG SERVICE: Found {len(namespace_chunks)} chunks in namespace '{namespace}' in {namespace_search_time:.2f}s")
                                relevant_chunks = namespace_chunks
                                found_relevant_chunks = True
                                break
                            else:
                                print(f"RAG SERVICE: No chunks found in namespace '{namespace}' in {namespace_search_time:.2f}s")
            except Exception as ns_search_error:
                print(f"RAG SERVICE WARNING: Error searching in specific namespaces: {str(ns_search_error)}")
            
            # 2. If we didn't find anything yet, try without specifying namespace (which will try default and root)
            if not found_relevant_chunks:
                print(f"RAG SERVICE: Trying search without specifying namespace")
                print(f"RAG SERVICE: Calling search_similar_chunks with params: query='{question[:30]}...', top_k=5, filter_doc_ids=[{len(document_ids)} ids], namespace=None")
                default_chunks = self.vector_db_service.search_similar_chunks(question, top_k=5, filter_doc_ids=document_ids)
                
                if default_chunks and len(default_chunks) > 0:
                    print(f"RAG SERVICE: Found {len(default_chunks)} chunks using default namespace search")
                    relevant_chunks = default_chunks
                    found_relevant_chunks = True
                else:
                    print(f"RAG SERVICE: No chunks found using default namespace search")
            
            # 3. If still no results, try the search_across_namespaces method as last resort
            if not found_relevant_chunks:
                print(f"RAG SERVICE: Trying search across all namespaces")
                try:
                    cross_ns_chunks = self.vector_db_service.search_across_namespaces(
                        question, 
                        top_k=5, 
                        filter_doc_ids=document_ids
                    )
                    
                    if cross_ns_chunks and len(cross_ns_chunks) > 0:
                        print(f"RAG SERVICE: Found {len(cross_ns_chunks)} chunks using cross-namespace search")
                        relevant_chunks = cross_ns_chunks
                        found_relevant_chunks = True
                    else:
                        print(f"RAG SERVICE: No chunks found using cross-namespace search")
                except Exception as cross_ns_error:
                    print(f"RAG SERVICE WARNING: Error in cross-namespace search: {str(cross_ns_error)}")
            
            search_time = time.time() - search_start_time
            print(f"RAG SERVICE: Found {len(relevant_chunks)} relevant chunks in {search_time:.2f} seconds")
            
            # Debug: Print the first chunk to help with debugging
            if relevant_chunks and len(relevant_chunks) > 0:
                first_chunk = relevant_chunks[0]
                print(f"RAG SERVICE: Top chunk - ID: {first_chunk.get('id', 'unknown')}, " +
                      f"Score: {first_chunk.get('score', 'unknown')}, " +
                      f"Doc ID: {first_chunk.get('doc_id', 'unknown')}")
                text_sample = first_chunk.get('text', '')[:100] + '...' if first_chunk.get('text') else 'No text available'
                print(f"RAG SERVICE: Top chunk text sample: {text_sample}")
                
                # Print details of all chunks
                print(f"RAG SERVICE: Details of all {len(relevant_chunks)} chunks:")
                for i, chunk in enumerate(relevant_chunks):
                    chunk_id = chunk.get('id', 'unknown')
                    doc_id = chunk.get('doc_id', 'unknown')
                    score = chunk.get('score', 'unknown')
                    text_length = len(chunk.get('text', ''))
                    print(f"  Chunk {i+1}: ID={chunk_id}, Doc ID={doc_id}, Score={score}, Text length={text_length}")
            else:
                print("RAG SERVICE WARNING: No relevant chunks found for the query")
                
                # Check if the index is empty
                try:
                    if hasattr(self.vector_db_service.pinecone_index, 'describe_index_stats'):
                        stats = self.vector_db_service.pinecone_index.describe_index_stats()
                        print(f"RAG SERVICE DEBUG: Pinecone index stats: {stats}")
                        
                        vector_count = 0
                        if isinstance(stats, dict) and 'total_vector_count' in stats:
                            vector_count = stats['total_vector_count']
                        
                        if vector_count == 0:
                            return "The system doesn't contain any document embeddings yet. Please process some documents first before asking questions."
                except Exception as stats_error:
                    print(f"RAG SERVICE WARNING: Error getting index stats: {str(stats_error)}")
                
                # Try with root namespace explicitly
                try:
                    print(f"RAG SERVICE: Trying search with 'root' namespace explicitly...")
                    root_chunks = self.vector_db_service.search_similar_chunks(question, top_k=5, filter_doc_ids=document_ids, namespace="root")
                    if root_chunks and len(root_chunks) > 0:
                        print(f"RAG SERVICE: Found {len(root_chunks)} chunks in root namespace")
                        relevant_chunks = root_chunks
                    else:
                        print(f"RAG SERVICE: No results found in root namespace either")
                except Exception as root_error:
                    print(f"RAG SERVICE: Error searching in root namespace: {str(root_error)}")
                
                # If still no chunks, return message about no relevant information
                if not relevant_chunks or len(relevant_chunks) == 0:
                    # Return a message about no relevant information found
                    return "I couldn't find any relevant information in the documents to answer your question. Please try rephrasing or asking about a different topic covered in the documents."
            
            # Construct context
            context = ""
            for chunk in relevant_chunks:
                chunk_text = chunk.get("text", "")
                chunk_id = chunk.get("id", "unknown")
                if chunk_text:
                    context += f"{chunk_text}\n\n"
                    print(f"RAG SERVICE: Added chunk {chunk_id} to context, length: {len(chunk_text)} chars")
                else:
                    print(f"RAG SERVICE WARNING: Chunk {chunk_id} has no text")
            
            print(f"RAG SERVICE: Total context length for prompt: {len(context)} chars")
            
            # Use provided template or default
            if not prompt_template:
                prompt_template = """
                You are an AI assistant that helps answer questions based on the provided document context.
                Answer the following question based ONLY on the information provided in the context below.
                If you can't find the answer in the context, say "I couldn't find information about that in the document."
                Don't use prior knowledge. Be concise and to the point.
                
                Context:
                {context}
                
                Question: {question}
                
                Answer:
                """
            
            # Format the prompt
            prompt = prompt_template.format(context=context, question=question)
            print(f"RAG SERVICE: Final prompt length: {len(prompt)} chars")
            
            # Call OpenAI API with timeout
            print(f"RAG SERVICE: Calling OpenAI at {time.strftime('%H:%M:%S')} with model {model}")
            
            openai_start_time = time.time()
            try:
                response = self.client.chat.completions.create(
                    model=model,
                    messages=[
                        {"role": "system", "content": "You are a helpful assistant that answers questions based on document context."},
                        {"role": "user", "content": prompt}
                    ],
                    temperature=0,
                    timeout=30  # 30 second timeout to prevent hanging
                )
                openai_time = time.time() - openai_start_time
                print(f"RAG SERVICE: OpenAI API call completed in {openai_time:.2f} seconds")
                
                if response and hasattr(response, 'choices') and len(response.choices) > 0:
                    answer = response.choices[0].message.content
                    answer_length = len(answer) if answer else 0
                    print(f"RAG SERVICE: Received answer of length {answer_length} chars")
                    answer_preview = answer[:150].replace('\n', ' ') + '...' if len(answer) > 150 else answer
                    print(f"RAG SERVICE: Answer preview: '{answer_preview}'")
                    return answer
                else:
                    print(f"RAG SERVICE ERROR: Unexpected response format from OpenAI")
                    print(f"RAG SERVICE: Response structure: {response}")
                    return "Sorry, I encountered an error while processing your question. Please try again."
                    
            except Exception as openai_error:
                openai_time = time.time() - openai_start_time
                error_type = type(openai_error).__name__
                print(f"RAG SERVICE ERROR: OpenAI API call failed after {openai_time:.2f} seconds with error type {error_type}")
                print(f"RAG SERVICE ERROR: {str(openai_error)}")
                
                # Check for timeout errors
                if "timeout" in str(openai_error).lower() or "time" in str(openai_error).lower():
                    print(f"RAG SERVICE ERROR: Request timed out to OpenAI API")
                    return "Sorry, the request timed out while waiting for a response. Please try again or try with a shorter question."
                
                # Check for API key errors
                if "api key" in str(openai_error).lower() or "apikey" in str(openai_error).lower():
                    print(f"RAG SERVICE ERROR: API key issue detected")
                    return "There seems to be an issue with the OpenAI API key. Please check that it's configured correctly."
                
                # General error message
                return f"Sorry, an error occurred while processing your question: {str(openai_error)}"
        
        except Exception as e:
            error_type = type(e).__name__
            print(f"RAG SERVICE ERROR: Exception during question answering: {error_type}")
            print(f"RAG SERVICE ERROR: {str(e)}")
            import traceback
            print(f"RAG SERVICE ERROR: Full error details:\n{traceback.format_exc()}")
            return f"An error occurred while processing your question: {str(e)}" 