import boto3
import os
import time
from io import BytesIO
from botocore.exceptions import ClientError
import json

class S3Service:
    def __init__(self):
        self.s3_client = boto3.client(
            's3',
            aws_access_key_id=os.getenv('AWS_ACCESS_KEY_ID'),
            aws_secret_access_key=os.getenv('AWS_SECRET_ACCESS_KEY'),
            region_name=os.getenv('AWS_REGION', 'us-west-2')
        )
        self.master_bucket = os.getenv('METADATA_BUCKET', 'doc-processor-metadata')
        self.metadata_folder = "metadata"
        
        # Ensure the master bucket exists with retry
        self.ensure_bucket_exists(self.master_bucket)
    
    def ensure_bucket_exists(self, bucket_name, max_retries=5):
        """Ensure bucket exists with retry logic"""
        try:
            self.s3_client.head_bucket(Bucket=bucket_name)
            print(f"Bucket {bucket_name} exists")
            return True
        except ClientError as e:
            if e.response['Error']['Code'] == '404' or e.response['Error']['Code'] == 'NoSuchBucket':
                print(f"Bucket {bucket_name} does not exist, creating...")
                
                # Try to create with retries
                for attempt in range(max_retries):
                    try:
                        region = os.getenv('AWS_REGION', 'us-west-2')
                        if region == 'us-east-1':
                            self.s3_client.create_bucket(Bucket=bucket_name)
                        else:
                            location = {'LocationConstraint': region}
                            self.s3_client.create_bucket(
                                Bucket=bucket_name,
                                CreateBucketConfiguration=location
                            )
                        print(f"Bucket {bucket_name} created successfully")
                        return True
                    except ClientError as create_error:
                        if create_error.response['Error']['Code'] == 'OperationAborted':
                            wait_time = 2 ** attempt  # Exponential backoff
                            print(f"Bucket creation conflict, retrying in {wait_time} seconds...")
                            time.sleep(wait_time)
                        else:
                            print(f"Error creating bucket: {str(create_error)}")
                            raise
                
                # If we get here, all retries failed
                print(f"Failed to create bucket after {max_retries} attempts")
                raise Exception(f"Failed to create bucket {bucket_name}")
            else:
                print(f"Error checking bucket: {str(e)}")
                raise
    
    def create_bucket(self, bucket_name, use_existing=True):
        """Create a new S3 bucket or use existing"""
        region = os.getenv('AWS_REGION', 'us-east-1')
        
        # Check if bucket already exists
        try:
            self.s3_client.head_bucket(Bucket=bucket_name)
            if use_existing:
                return f"s3://{bucket_name}"
            else:
                raise Exception(f"Bucket {bucket_name} already exists and use_existing is False")
        except ClientError as e:
            # If bucket doesn't exist, create it
            if e.response['Error']['Code'] == '404' or e.response['Error']['Code'] == 'NoSuchBucket':
                # Create the bucket
                if region == 'us-east-1':
                    self.s3_client.create_bucket(Bucket=bucket_name)
                else:
                    location = {'LocationConstraint': region}
                    self.s3_client.create_bucket(
                        Bucket=bucket_name,
                        CreateBucketConfiguration=location
                    )
                return f"s3://{bucket_name}"
            else:
                # If it's another error, raise it
                raise
    
    def create_folder(self, folder_name):
        """Create a 'folder' (prefix) within the master bucket"""
        # Create an empty object with the folder name as the key
        self.s3_client.put_object(
            Bucket=self.master_bucket,
            Key=f"{folder_name}/"
        )
        return f"s3://{self.master_bucket}/{folder_name}/"
    
    def list_folders(self):
        """List all 'folders' in the master bucket"""
        try:
            response = self.s3_client.list_objects_v2(
                Bucket=self.master_bucket,
                Delimiter='/'
            )
            
            folders = []
            if 'CommonPrefixes' in response:
                folders = [prefix['Prefix'].rstrip('/') for prefix in response['CommonPrefixes']]
            
            return folders
        except Exception as e:
            print(f"Error listing folders: {str(e)}")
            return []
    
    def delete_folder(self, folder_name):
        """Delete a folder and all its contents"""
        try:
            # List all objects with the folder prefix
            response = self.s3_client.list_objects_v2(
                Bucket=self.master_bucket,
                Prefix=f"{folder_name}/"
            )
            
            if 'Contents' in response:
                # Delete all objects in the folder
                for obj in response['Contents']:
                    self.s3_client.delete_object(
                        Bucket=self.master_bucket,
                        Key=obj['Key']
                    )
                
                # Also delete any metadata for documents in this folder
                metadata_response = self.s3_client.list_objects_v2(
                    Bucket=self.master_bucket,
                    Prefix=f"{self.metadata_folder}/"
                )
                
                if 'Contents' in metadata_response:
                    for obj in metadata_response['Contents']:
                        if obj['Key'].endswith('.json'):
                            try:
                                # Get metadata
                                metadata_obj = self.s3_client.get_object(
                                    Bucket=self.master_bucket,
                                    Key=obj['Key']
                                )
                                metadata = json.loads(metadata_obj['Body'].read().decode('utf-8'))
                                
                                # If this document is in the folder being deleted, delete its metadata
                                if metadata.get('folder') == folder_name:
                                    # Delete metadata file
                                    self.s3_client.delete_object(
                                        Bucket=self.master_bucket,
                                        Key=obj['Key']
                                    )
                                    
                                    # Try to delete from vector database if possible
                                    doc_id = metadata.get('id')
                                    if doc_id:
                                        try:
                                            from app.services.vector_db_service import VectorDBService
                                            vector_db = VectorDBService()
                                            vector_db.delete_document(doc_id)
                                        except Exception as ve:
                                            print(f"Error deleting from vector database: {str(ve)}")
                            except Exception as e:
                                print(f"Error processing metadata during folder deletion: {str(e)}")
            
            # After deleting all folder content and document records, also delete the Pinecone namespace
            try:
                from app.services.vector_db_service import VectorDBService
                vector_db = VectorDBService()
                namespace_deleted = vector_db.delete_namespace(folder_name)
                if namespace_deleted:
                    print(f"Successfully deleted Pinecone namespace for folder '{folder_name}'")
                else:
                    print(f"Failed to delete Pinecone namespace for folder '{folder_name}' or it didn't exist")
            except Exception as ve:
                print(f"Error deleting Pinecone namespace: {str(ve)}")
                # Continue with the operation even if namespace deletion fails
            
            return True
        except Exception as e:
            print(f"Error deleting folder: {str(e)}")
            return False
    
    def upload_file(self, folder_name, key, content):
        """Upload a file to a folder in the master bucket"""
        full_key = f"{folder_name}/{key}"
        self.s3_client.put_object(
            Bucket=self.master_bucket,
            Key=full_key,
            Body=content
        )
        return f"s3://{self.master_bucket}/{full_key}"
    
    def download_file(self, folder_name, key):
        """Download a file from a folder in the master bucket"""
        full_key = f"{folder_name}/{key}"
        buffer = BytesIO()
        self.s3_client.download_fileobj(self.master_bucket, full_key, buffer)
        buffer.seek(0)
        return buffer

    def list_buckets(self):
        """List all available S3 buckets"""
        response = self.s3_client.list_buckets()
        return [bucket['Name'] for bucket in response['Buckets']]
    
    def delete_bucket(self, bucket_name, force=False):
        """Delete a bucket and all its contents"""
        try:
            # First delete all objects
            objects = self.s3_client.list_objects_v2(Bucket=bucket_name)
            if 'Contents' in objects:
                for obj in objects['Contents']:
                    self.s3_client.delete_object(Bucket=bucket_name, Key=obj['Key'])
            
            # Then delete the bucket
            self.s3_client.delete_bucket(Bucket=bucket_name)
            return True
        except ClientError as e:
            if force:
                print(f"Error deleting bucket {bucket_name}: {str(e)}")
                return False
            else:
                raise 

    def ensure_required_folders(self):
        """Ensure that required folders exist in the bucket"""
        required_folders = ["metadata", "documents"]
        
        for folder in required_folders:
            try:
                self.s3_client.put_object(
                    Bucket=self.master_bucket,
                    Key=f"{folder}/"
                )
                print(f"Ensured {folder}/ folder exists")
            except Exception as e:
                print(f"Error ensuring {folder}/ folder exists: {str(e)}")

    def upload_file_content(self, folder: str, filename: str, content: bytes) -> bool:
        """Upload file content to S3"""
        try:
            key = f"{folder}/{filename}"
            self.s3_client.put_object(
                Bucket=self.master_bucket,
                Key=key,
                Body=content
            )
            print(f"Uploaded file content to {key}")
            return True
        except Exception as e:
            print(f"Error uploading file content: {str(e)}")
            return False 