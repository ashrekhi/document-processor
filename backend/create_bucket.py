import boto3
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Get AWS credentials from environment
aws_access_key = os.getenv('AWS_ACCESS_KEY_ID')
aws_secret_key = os.getenv('AWS_SECRET_ACCESS_KEY')
aws_region = os.getenv('AWS_REGION')
bucket_name = os.getenv('METADATA_BUCKET')

print(f"Creating bucket {bucket_name} in region {aws_region}")

# Create S3 client
s3_client = boto3.client(
    's3',
    aws_access_key_id=aws_access_key,
    aws_secret_access_key=aws_secret_key,
    region_name=aws_region
)

# Check if bucket exists
try:
    s3_client.head_bucket(Bucket=bucket_name)
    print(f"Bucket {bucket_name} already exists")
except Exception as e:
    print(f"Bucket does not exist or error checking: {str(e)}")
    # Create the bucket
    try:
        if aws_region == 'us-east-1':
            s3_client.create_bucket(Bucket=bucket_name)
        else:
            location = {'LocationConstraint': aws_region}
            s3_client.create_bucket(
                Bucket=bucket_name,
                CreateBucketConfiguration=location
            )
        print(f"Bucket {bucket_name} created successfully")
    except Exception as e:
        print(f"Error creating bucket: {str(e)}")

# Create metadata folder
try:
    s3_client.put_object(
        Bucket=bucket_name,
        Key="metadata/"
    )
    print("Created metadata folder")
except Exception as e:
    print(f"Error creating metadata folder: {str(e)}")

# Create documents folder
try:
    s3_client.put_object(
        Bucket=bucket_name,
        Key="documents/"
    )
    print("Created documents folder")
except Exception as e:
    print(f"Error creating documents folder: {str(e)}")

print("Bucket setup complete") 