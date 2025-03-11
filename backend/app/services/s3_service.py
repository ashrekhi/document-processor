import boto3
import os
from io import BytesIO

class S3Service:
    def __init__(self):
        self.s3_client = boto3.client(
            's3',
            aws_access_key_id=os.getenv('AWS_ACCESS_KEY_ID'),
            aws_secret_access_key=os.getenv('AWS_SECRET_ACCESS_KEY'),
            region_name=os.getenv('AWS_REGION', 'us-east-1')
        )
    
    def create_bucket(self, bucket_name):
        """Create a new S3 bucket for document isolation"""
        region = os.getenv('AWS_REGION', 'us-east-1')
        
        # Check if bucket already exists
        try:
            self.s3_client.head_bucket(Bucket=bucket_name)
            return f"s3://{bucket_name}"
        except:
            # Create the bucket
            if region == 'us-east-1':
                self.s3_client.create_bucket(Bucket=bucket_name)
            else:
                location = {'LocationConstraint': region}
                self.s3_client.create_bucket(
                    Bucket=bucket_name,
                    CreateBucketConfiguration=location
                )
            
            # Set bucket policy for private access
            self.s3_client.put_bucket_policy(
                Bucket=bucket_name,
                Policy=f'''{{
                    "Version": "2012-10-17",
                    "Statement": [
                        {{
                            "Sid": "DenyPublicAccess",
                            "Effect": "Deny",
                            "Principal": "*",
                            "Action": "s3:*",
                            "Resource": [
                                "arn:aws:s3:::{bucket_name}",
                                "arn:aws:s3:::{bucket_name}/*"
                            ],
                            "Condition": {{
                                "Bool": {{
                                    "aws:SecureTransport": "false"
                                }}
                            }}
                        }}
                    ]
                }}'''
            )
            
            return f"s3://{bucket_name}"
    
    def upload_file(self, bucket_name, key, content):
        """Upload a file to S3"""
        self.s3_client.put_object(
            Bucket=bucket_name,
            Key=key,
            Body=content
        )
        return f"s3://{bucket_name}/{key}"
    
    def download_file(self, bucket_name, key):
        """Download a file from S3"""
        buffer = BytesIO()
        self.s3_client.download_fileobj(bucket_name, key, buffer)
        buffer.seek(0)
        return buffer
    
    def delete_bucket(self, bucket_name):
        """Delete a bucket and all its contents"""
        # First delete all objects
        objects = self.s3_client.list_objects_v2(Bucket=bucket_name)
        if 'Contents' in objects:
            for obj in objects['Contents']:
                self.s3_client.delete_object(Bucket=bucket_name, Key=obj['Key'])
        
        # Then delete the bucket
        self.s3_client.delete_bucket(Bucket=bucket_name) 