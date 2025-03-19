#!/usr/bin/env python3
import os
import json
import sys

def check_files_exist(files):
    missing_files = []
    for file_path in files:
        if not os.path.exists(file_path):
            missing_files.append(file_path)
    return missing_files

def check_env_vars_in_dotenv(file_path, required_vars):
    if not os.path.exists(file_path):
        return required_vars, []
    
    found_vars = []
    with open(file_path, 'r') as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith('#'):
                var_name = line.split('=')[0].strip()
                found_vars.append(var_name)
    
    missing_vars = [var for var in required_vars if var not in found_vars]
    return missing_vars, found_vars

def main():
    print("🔍 Running pre-deployment check for Document Processor...\n")
    
    # Check critical files
    required_files = [
        "render.yaml",
        "backend/requirements.txt", 
        "backend/app/main.py",
        "frontend/package.json",
        "frontend/src/services/api.js",
        "RENDER_DEPLOYMENT.md"
    ]
    
    missing_files = check_files_exist(required_files)
    
    if missing_files:
        print("❌ Error: The following required files are missing:")
        for file in missing_files:
            print(f"  - {file}")
        print("\nPlease create these files before deploying.")
    else:
        print("✅ All required files are present.")
    
    # Check backend environment variables
    backend_env_file = "backend/.env"
    backend_required_vars = [
        "AWS_ACCESS_KEY_ID", 
        "AWS_SECRET_ACCESS_KEY", 
        "AWS_REGION",
        "OPENAI_API_KEY",
        "METADATA_BUCKET",
        "PINECONE_API_KEY",
        "PINECONE_INDEX",
        "PINECONE_CLOUD",
        "PINECONE_REGION",
    ]
    
    backend_missing_vars, backend_found_vars = check_env_vars_in_dotenv(backend_env_file, backend_required_vars)
    
    print(f"\n📋 Backend Environment Variables (.env file):")
    if os.path.exists(backend_env_file):
        print(f"  ✅ Backend .env file exists")
        if backend_missing_vars:
            print(f"  ❌ Missing required environment variables:")
            for var in backend_missing_vars:
                print(f"    - {var}")
        else:
            print(f"  ✅ All required environment variables found")
    else:
        print(f"  ❌ Backend .env file not found. This is fine for Render deployment as you'll set them in the UI.")
    
    # Check frontend environment variables
    frontend_env_file = "frontend/.env"
    frontend_required_vars = ["REACT_APP_API_URL"]
    
    frontend_missing_vars, frontend_found_vars = check_env_vars_in_dotenv(frontend_env_file, frontend_required_vars)
    
    print(f"\n📋 Frontend Environment Variables (.env file):")
    if os.path.exists(frontend_env_file):
        print(f"  ✅ Frontend .env file exists")
        if frontend_missing_vars:
            print(f"  ❌ Missing required environment variables:")
            for var in frontend_missing_vars:
                print(f"    - {var}")
        else:
            print(f"  ✅ All required environment variables found")
    else:
        print(f"  ❌ Frontend .env file not found. This is fine for Render deployment as you'll set them in the UI.")
    
    # Check package.json for frontend
    try:
        with open("frontend/package.json", "r") as f:
            package_json = json.load(f)
        print("\n📦 Frontend Package.json:")
        if "scripts" in package_json and "build" in package_json["scripts"]:
            print(f"  ✅ build script found: {package_json['scripts']['build']}")
        else:
            print(f"  ❌ No build script found in package.json. This is required for Render deployment.")
    except Exception as e:
        print(f"\n❌ Error checking package.json: {str(e)}")
    
    # Check render.yaml
    try:
        with open("render.yaml", "r") as f:
            render_yaml_content = f.read()
        
        print("\n🚀 Render.yaml:")
        if "document-processor-api" in render_yaml_content:
            print(f"  ✅ Backend service configuration found")
        else:
            print(f"  ❌ Backend service configuration missing")
            
        if "document-processor-frontend" in render_yaml_content:
            print(f"  ✅ Frontend service configuration found")
        else:
            print(f"  ❌ Frontend service configuration missing")
    except Exception as e:
        print(f"\n❌ Error checking render.yaml: {str(e)}")
    
    print("\n🔍 Pre-deployment check complete.")
    print("\nReminder: Before deploying to Render, make sure you have:")
    print("1. Configured all environment variables in Render UI or render.yaml")
    print("2. Connected your GitHub repository to Render")
    print("3. Read the RENDER_DEPLOYMENT.md for detailed instructions")

if __name__ == "__main__":
    main() 