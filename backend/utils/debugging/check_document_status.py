import os
import json
import boto3
from dotenv import load_dotenv
import sys

# Load environment variables
load_dotenv()

def check_document_status(doc_id):
    """Check the processing status of a document"""
    try:
        # Get S3 credentials from environment
        aws_access_key = os.getenv('AWS_ACCESS_KEY_ID')
        aws_secret_key = os.getenv('AWS_SECRET_ACCESS_KEY')
        aws_region = os.getenv('AWS_REGION', 'us-west-2')
        bucket_name = os.getenv('METADATA_BUCKET', 'doc-processor-main')
        
        # Initialize S3 client
        s3_client = boto3.client(
            's3',
            aws_access_key_id=aws_access_key,
            aws_secret_access_key=aws_secret_key,
            region_name=aws_region
        )
        
        # Get metadata from S3
        try:
            metadata_key = f"metadata/{doc_id}.json"
            print(f"Checking for metadata at s3://{bucket_name}/{metadata_key}")
            
            metadata_obj = s3_client.get_object(
                Bucket=bucket_name,
                Key=metadata_key
            )
            metadata = json.loads(metadata_obj['Body'].read().decode('utf-8'))
            
            print(f"Document ID: {doc_id}")
            print(f"Filename: {metadata.get('filename', 'unknown')}")
            print(f"Upload Date: {metadata.get('upload_date', 'unknown')}")
            print(f"Processed: {metadata.get('processed', False)}")
            print(f"Processing: {metadata.get('processing', False)}")
            print(f"Error: {metadata.get('error', 'none')}")
            
            # Check if document content exists
            document_key = metadata.get('document_key')
            folder = metadata.get('folder', 'root')
            content_key = f"{folder}/{document_key}"
            
            try:
                s3_client.head_object(
                    Bucket=bucket_name,
                    Key=content_key
                )
                print(f"Document content exists at s3://{bucket_name}/{content_key}")
            except Exception as content_error:
                print(f"Document content does not exist at s3://{bucket_name}/{content_key}")
                print(f"Error: {str(content_error)}")
            
            return metadata
        except Exception as metadata_error:
            print(f"Error getting metadata for document {doc_id}: {str(metadata_error)}")
            print("Metadata file does not exist or cannot be accessed")
            return None
    except Exception as e:
        print(f"Error checking document status: {str(e)}")
        return None

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python check_document_status.py <doc_id>")
        sys.exit(1)
    
    doc_id = sys.argv[1]
    check_document_status(doc_id) 