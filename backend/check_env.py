import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Check if environment variables are loaded
print(f"OPENAI_API_KEY: {'Set' if os.getenv('OPENAI_API_KEY') else 'Not set'}")
print(f"PINECONE_API_KEY: {'Set' if os.getenv('PINECONE_API_KEY') else 'Not set'}")
print(f"AWS_ACCESS_KEY_ID: {'Set' if os.getenv('AWS_ACCESS_KEY_ID') else 'Not set'}")
print(f"AWS_SECRET_ACCESS_KEY: {'Set' if os.getenv('AWS_SECRET_ACCESS_KEY') else 'Not set'}")
print(f"AWS_REGION: {os.getenv('AWS_REGION', 'Not set')}")
print(f"METADATA_BUCKET: {os.getenv('METADATA_BUCKET', 'Not set')}")
print(f"PINECONE_INDEX: {os.getenv('PINECONE_INDEX', 'Not set')}")

# Print the current working directory
print(f"Current working directory: {os.getcwd()}")

# Check if .env file exists
env_path = os.path.join(os.getcwd(), '.env')
print(f".env file exists: {os.path.exists(env_path)}")

# Try to read the .env file
try:
    with open(env_path, 'r') as f:
        print(f"First few lines of .env file:")
        for i, line in enumerate(f):
            if i < 3:  # Print only the first 3 lines
                # Mask sensitive information
                if line.startswith(('OPENAI_API_KEY', 'PINECONE_API_KEY', 'AWS_ACCESS_KEY_ID', 'AWS_SECRET_ACCESS_KEY')):
                    key, value = line.strip().split('=', 1)
                    masked_value = value[:4] + '*' * (len(value) - 8) + value[-4:] if len(value) > 8 else '*' * len(value)
                    print(f"  {key}={masked_value}")
                else:
                    print(f"  {line.strip()}")
except Exception as e:
    print(f"Error reading .env file: {str(e)}") 