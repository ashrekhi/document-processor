# Document Processor

A modern enterprise application for processing documents using RAG (Retrieval-Augmented Generation) technology. Upload your documents, organize them into folders, and ask questions to generate answers based on document content.

## Features

- Upload and manage documents (PDF, TXT, MD)
- Organize documents in folders
- Ask questions about your documents using RAG
- Enterprise-grade UI with Material UI
- Responsive design for all device sizes

## Technology Stack

### Frontend
- React
- Material UI
- React Router
- Axios for API communication

### Backend
- FastAPI (Python)
- OpenAI API for RAG
- Pinecone for vector storage
- AWS S3 for document storage

## Local Development

### Backend Setup

1. Navigate to the backend directory:
   ```
   cd backend
   ```

2. Create a virtual environment:
   ```
   python -m venv venv
   ```

3. Activate the virtual environment:
   - Windows: `venv\Scripts\activate`
   - macOS/Linux: `source venv/bin/activate`

4. Install dependencies:
   ```
   pip install -r requirements.txt
   ```

5. Create a `.env` file in the backend directory with the following variables:
   ```
   AWS_ACCESS_KEY_ID=your_aws_access_key
   AWS_SECRET_ACCESS_KEY=your_aws_secret_key
   AWS_REGION=your_aws_region
   OPENAI_API_KEY=your_openai_api_key
   METADATA_BUCKET=your_s3_bucket_name
   PINECONE_API_KEY=your_pinecone_api_key
   PINECONE_INDEX=your_pinecone_index_name
   PINECONE_CLOUD=aws
   PINECONE_REGION=us-east-1
   ```

6. Start the backend server:
   ```
   uvicorn app.main:app --reload
   ```