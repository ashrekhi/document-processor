import os
import pinecone
from dotenv import load_dotenv
import traceback
import requests

# Load environment variables
load_dotenv()

def check_pinecone_account():
    # Get Pinecone credentials from environment
    api_key = os.getenv('PINECONE_API_KEY')
    environment = os.getenv('PINECONE_ENVIRONMENT', 'us-east-1-aws')
    
    if not api_key:
        print("ERROR: PINECONE_API_KEY not set in environment variables")
        return False
    
    print(f"Checking Pinecone account with:")
    print(f"  API Key: {api_key[:5]}...{api_key[-5:]} (length: {len(api_key)})")
    print(f"  Environment: {environment}")
    
    try:
        # Initialize Pinecone
        print("Initializing Pinecone...")
        pinecone.init(api_key=api_key, environment=environment)
        
        # List indexes with detailed error handling
        print("Listing indexes...")
        try:
            indexes = pinecone.list_indexes()
            print(f"Available indexes: {indexes}")
            
            # Check if we have any indexes
            if not indexes:
                print("No indexes found in your Pinecone account.")
                print("This could be because:")
                print("1. You haven't created any indexes yet")
                print("2. You're using a different environment than where your indexes are located")
                print("3. Your API key doesn't have access to the indexes")
                print("4. Your Pinecone account has limitations on index creation")
            
            # Try to get account information
            print("\nAttempting to get account information...")
            try:
                # This is not part of the official API, but might work
                headers = {
                    "Api-Key": api_key,
                    "Accept": "application/json"
                }
                response = requests.get(
                    f"https://controller.{environment}.pinecone.io/actions/whoami",
                    headers=headers
                )
                if response.status_code == 200:
                    print(f"Account info: {response.json()}")
                else:
                    print(f"Failed to get account info: {response.status_code} {response.text}")
            except Exception as account_error:
                print(f"Error getting account info: {str(account_error)}")
            
            return True
        except Exception as list_error:
            print(f"Error listing indexes: {str(list_error)}")
            print("Detailed error:")
            traceback.print_exc()
            return False
    except Exception as e:
        print(f"Error in Pinecone account check: {str(e)}")
        print("Detailed error:")
        traceback.print_exc()
        return False

if __name__ == "__main__":
    check_pinecone_account() 