# Deploying Document Processor to Render

This guide will walk you through the process of deploying the Document Processor application to [Render](https://render.com).

## Prerequisites

1. A Render account (sign up at [render.com](https://render.com) if you don't have one)
2. Access to all the required environment variables:
   - AWS credentials (for S3 storage)
   - OpenAI API key
   - Pinecone API key and configuration

## Deployment Options

There are two ways to deploy this application to Render:

1. **Blueprint Deployment** (Recommended): Using the `render.yaml` file in this repository
2. **Manual Deployment**: Setting up each service individually

## Option 1: Blueprint Deployment

This is the easiest way to deploy both the frontend and backend services in one go.

1. Fork this repository to your own GitHub account
2. Log in to your Render dashboard
3. Click on the "New" button and select "Blueprint"
4. Connect your GitHub account if you haven't already
5. Select the forked repository
6. Render will detect the `render.yaml` file and show you the services to be created
7. Configure the environment variables:
   - AWS_ACCESS_KEY_ID
   - AWS_SECRET_ACCESS_KEY
   - AWS_REGION
   - OPENAI_API_KEY
   - METADATA_BUCKET
   - PINECONE_API_KEY
   - PINECONE_INDEX
   - PINECONE_CLOUD
   - PINECONE_REGION
8. Click "Apply" to deploy both services

## Option 2: Manual Deployment

### Backend Deployment

1. Log in to your Render dashboard
2. Click on the "New" button and select "Web Service"
3. Connect your GitHub account if you haven't already
4. Select the repository
5. Configure the service:
   - **Name**: document-processor-api (or your preferred name)
   - **Environment**: Python
   - **Region**: Choose a region close to your users
   - **Build Command**: `cd backend && pip install -r requirements.txt`
   - **Start Command**: `cd backend && uvicorn app.main:app --host 0.0.0.0 --port $PORT`
6. Add the following environment variables:
   - PYTHON_VERSION: 3.9.0
   - AWS_ACCESS_KEY_ID: your-aws-access-key
   - AWS_SECRET_ACCESS_KEY: your-aws-secret-key
   - AWS_REGION: your-aws-region
   - OPENAI_API_KEY: your-openai-api-key
   - METADATA_BUCKET: your-s3-bucket-name
   - PINECONE_API_KEY: your-pinecone-api-key
   - PINECONE_INDEX: your-pinecone-index
   - PINECONE_CLOUD: aws
   - PINECONE_REGION: us-east-1
7. Click "Create Web Service"

### Frontend Deployment

1. Log in to your Render dashboard
2. Click on the "New" button and select "Static Site"
3. Connect your GitHub account if you haven't already
4. Select the repository
5. Configure the service:
   - **Name**: document-processor-frontend (or your preferred name)
   - **Build Command**: `cd frontend && npm install && npm run build`
   - **Publish Directory**: `frontend/build`
6. Add the following environment variables:
   - REACT_APP_API_URL: the URL of your backend service (e.g., https://document-processor-api.onrender.com)
7. Under the "Advanced" section, add a redirect rule:
   - Source: `/*`
   - Destination: `/index.html`
   - Status: 200
8. Click "Create Static Site"

## Post-Deployment

After deployment is complete:

1. Test the frontend by visiting the frontend service URL
2. Test the backend by visiting `{backend-url}/docs` to see the FastAPI Swagger documentation
3. If you encounter any issues, check the logs in your Render dashboard

## Updating Your Deployment

When you push changes to your GitHub repository, Render will automatically redeploy your services.

## Custom Domains

To use a custom domain with your Render services:

1. Navigate to the service dashboard
2. Click on "Settings"
3. Under "Custom Domain", click "Add Custom Domain"
4. Follow the instructions to configure your domain

## Troubleshooting

If you encounter any issues:

1. Check the service logs in the Render dashboard
2. Verify that all environment variables are set correctly
3. Make sure the backend URL in the frontend environment variable is correct
4. Check for any CORS issues if the frontend cannot communicate with the backend

For more help, refer to the [Render documentation](https://render.com/docs) or contact Render support. 