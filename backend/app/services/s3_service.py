import boto3
import os
from io import BytesIO
from botocore.exceptions import ClientError

class S3Service:
    def __init__(self):
        self.s3_client = boto3.client(
            's3',
            aws_access_key_id=os.getenv('AWS_ACCESS_KEY_ID'),
            aws_secret_access_key=os.getenv('AWS_SECRET_ACCESS_KEY'),
            region_name=os.getenv('AWS_REGION', 'us-east-1')
        )
        self.master_bucket = os.getenv('MASTER_BUCKET', 'doc-processor-master')
        
        # Ensure master bucket exists
        try:
            self.create_bucket(self.master_bucket, use_existing=True)
        except Exception as e:
            print(f"Error creating master bucket: {str(e)}")
    
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
                for obj in response['Contents']:
                    self.s3_client.delete_object(
                        Bucket=self.master_bucket,
                        Key=obj['Key']
                    )
            
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