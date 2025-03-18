import os
import sys

# Print all environment variables
print("System environment variables:")
for key, value in os.environ.items():
    # Mask sensitive information
    if key in ('OPENAI_API_KEY', 'PINECONE_API_KEY', 'AWS_ACCESS_KEY_ID', 'AWS_SECRET_ACCESS_KEY'):
        masked_value = value[:4] + '*' * (len(value) - 8) + value[-4:] if len(value) > 8 else '*' * len(value)
        print(f"  {key}={masked_value}")
    else:
        print(f"  {key}={value}")

# Check Python path
print("\nPython path:")
for path in sys.path:
    print(f"  {path}") 