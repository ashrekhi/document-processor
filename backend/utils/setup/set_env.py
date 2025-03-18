import os

# Set environment variables manually
os.environ['OPENAI_API_KEY'] = 'your_actual_openai_api_key_here'
os.environ['PINECONE_API_KEY'] = 'your_actual_pinecone_api_key_here'
os.environ['AWS_ACCESS_KEY_ID'] = 'your_actual_aws_access_key_here'
os.environ['AWS_SECRET_ACCESS_KEY'] = 'your_actual_aws_secret_key_here'
os.environ['AWS_REGION'] = 'us-west-2'
os.environ['METADATA_BUCKET'] = 'doc-processor-main'
os.environ['PINECONE_INDEX'] = 'radiant-documents'

# Print environment variables to confirm they're set
print(f"OPENAI_API_KEY: {'Set' if os.getenv('OPENAI_API_KEY') else 'Not set'}")
print(f"PINECONE_API_KEY: {'Set' if os.getenv('PINECONE_API_KEY') else 'Not set'}")
print(f"AWS_ACCESS_KEY_ID: {'Set' if os.getenv('AWS_ACCESS_KEY_ID') else 'Not set'}")
print(f"AWS_SECRET_ACCESS_KEY: {'Set' if os.getenv('AWS_SECRET_ACCESS_KEY') else 'Not set'}")
print(f"AWS_REGION: {os.getenv('AWS_REGION', 'Not set')}")
print(f"METADATA_BUCKET: {os.getenv('METADATA_BUCKET', 'Not set')}")
print(f"PINECONE_INDEX: {os.getenv('PINECONE_INDEX', 'Not set')}") 