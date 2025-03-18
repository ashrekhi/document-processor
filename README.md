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
   PINECONE_ENVIRONMENT=your_pinecone_environment
   PINECONE_INDEX=your_pinecone_index
   ```

6. Start the backend server:
   ```
   uvicorn app.main:app --reload
   ```

### Frontend Setup

1. Navigate to the frontend directory:
   ```
   cd frontend
   ```

2. Install dependencies:
   ```
   npm install
   ```

3. Create a `.env` file in the frontend directory:
   ```
   REACT_APP_API_URL=http://localhost:8000
   ```

4. Start the frontend server:
   ```
   npm start
   ```

## Deployment

This application can be deployed to Render or other cloud platforms. For detailed Render deployment instructions, please see [RENDER_DEPLOYMENT.md](./RENDER_DEPLOYMENT.md).

## Docker Deployment

The application includes Docker configuration for containerized deployment:

1. Make sure Docker and Docker Compose are installed on your system
2. Create a `.env` file in the root directory with all required environment variables
3. Run the application:
   ```
   docker-compose up
   ```

## License

[MIT License](LICENSE) 