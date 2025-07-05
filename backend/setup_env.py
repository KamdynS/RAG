#!/usr/bin/env python3
"""
Setup script for RAG Production System environment variables.
Run this script to create a .env file with the required configuration.
"""

import os
from pathlib import Path

def create_env_file():
    """Create a .env file with template values."""
    
    env_template = """# Application Configuration
DEBUG=true
APP_NAME="RAG Production System"
APP_VERSION="1.0.0"
LOG_LEVEL=INFO

# API Configuration
API_PREFIX="/api"

# Database Configuration (Update with your database details)
DATABASE_URL="postgresql://user:password@localhost:5432/rag_production"

# Redis Configuration
REDIS_URL="redis://localhost:6379"

# OpenAI Configuration (REQUIRED - Get from https://platform.openai.com/api-keys)
OPENAI_API_KEY="your-openai-api-key-here"
OPENAI_MODEL="gpt-4-turbo-preview"
OPENAI_EMBEDDING_MODEL="text-embedding-3-small"

# Pinecone Configuration (REQUIRED - Get from https://www.pinecone.io/)
PINECONE_API_KEY="your-pinecone-api-key-here"
PINECONE_ENVIRONMENT="your-pinecone-environment"
PINECONE_INDEX_NAME="rag-documents"

# Document Processing Configuration
MAX_FILE_SIZE=52428800  # 50MB in bytes
CHUNK_SIZE=1000
CHUNK_OVERLAP=200

# Authentication Configuration
SECRET_KEY="your-secret-key-for-jwt-tokens-make-it-long-and-secure"
ALGORITHM="HS256"
ACCESS_TOKEN_EXPIRE_MINUTES=30

# CORS Configuration
CORS_ORIGINS="http://localhost:3000,http://localhost:3001"

# AWS Configuration (Optional - for S3 storage)
AWS_ACCESS_KEY_ID=""
AWS_SECRET_ACCESS_KEY=""
AWS_REGION="us-east-1"
S3_BUCKET_NAME=""

# Allowed file types (comma-separated)
ALLOWED_FILE_TYPES="pdf,docx,pptx,txt,md"
"""
    
    env_file_path = Path(__file__).parent / ".env"
    
    if env_file_path.exists():
        response = input(f".env file already exists at {env_file_path}. Overwrite? (y/N): ")
        if response.lower() != 'y':
            print("Cancelled. Existing .env file preserved.")
            return
    
    with open(env_file_path, 'w') as f:
        f.write(env_template)
    
    print(f"✅ Created .env file at {env_file_path}")
    print("\n📋 Next steps:")
    print("1. Edit the .env file and add your API keys:")
    print("   - OpenAI API key (required)")
    print("   - Pinecone API key and environment (required)")
    print("   - Database URL (if using PostgreSQL)")
    print("2. Install dependencies: pip install -r requirements.txt")
    print("3. Run the application: python main.py")
    print("\n💡 Tips:")
    print("- Get OpenAI API key from: https://platform.openai.com/api-keys")
    print("- Get Pinecone account from: https://www.pinecone.io/")
    print("- For development, you can use in-memory storage (no Pinecone required)")

def check_requirements():
    """Check if all required packages are installed."""
    try:
        import fastapi
        import openai
        import pydantic
        print("✅ Core packages are installed")
    except ImportError as e:
        print(f"❌ Missing required packages: {e}")
        print("Run: pip install -r requirements.txt")
        return False
    
    return True

def main():
    """Main setup function."""
    print("🚀 RAG Production System Setup")
    print("=" * 40)
    
    # Check if we're in the right directory
    if not Path("requirements.txt").exists():
        print("❌ Please run this script from the backend directory")
        return
    
    # Create .env file
    create_env_file()
    
    # Check requirements
    print("\n🔍 Checking dependencies...")
    check_requirements()
    
    print("\n🎉 Setup complete! Don't forget to update your .env file with real API keys.")

if __name__ == "__main__":
    main() 