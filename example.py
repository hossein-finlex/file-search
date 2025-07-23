#!/usr/bin/env python3
"""
Example script demonstrating the S3 Vector service usage
"""

import os
import tempfile
import json
from app.services.s3vector_service import S3VectorService
from app.services.embedding_service import EmbeddingService


def create_sample_files():
    """Create sample files for testing"""
    files = []
    
    # Create a sample text file
    with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
        f.write("This is a sample document about machine learning and artificial intelligence.")
        files.append(f.name)
    
    # Create another sample text file
    with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
        f.write("Python is a programming language used for data science and web development.")
        files.append(f.name)
    
    # Create a third sample text file
    with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
        f.write("AWS S3 Vector buckets provide vector search capabilities for similarity queries.")
        files.append(f.name)
    
    return files


def example_usage():
    """Demonstrate the S3 Vector service functionality"""
    print("🚀 S3 Vector Service Example")
    print("=" * 50)
    
    # Initialize the service
    try:
        service = S3VectorService()
        print("✅ S3 Vector service initialized successfully")
    except Exception as e:
        print(f"❌ Failed to initialize service: {e}")
        return
    
    # Health check
    health = service.health_check()
    print(f"🏥 Health check: {health['status']}")
    print(f"   S3 Connection: {health['s3_connection']}")
    print(f"   Vector Dimension: {health.get('vector_dimension', 'N/A')}")
    
    # Create sample files
    print("\n📁 Creating sample files...")
    sample_files = create_sample_files()
    
    # Upload files
    print("\n📤 Uploading files...")
    uploaded_files = []
    
    for i, file_path in enumerate(sample_files):
        try:
            metadata = {
                "category": "sample",
                "index": i + 1,
                "description": f"Sample file {i + 1}"
            }
            
            file_id = service.upload_file(
                file_path=file_path,
                metadata=metadata,
                content_type="text/plain"
            )
            
            uploaded_files.append(file_id)
            print(f"   ✅ Uploaded: {os.path.basename(file_path)} -> {file_id}")
        
        except Exception as e:
            print(f"   ❌ Failed to upload {file_path}: {e}")
    
    # List files
    print("\n📋 Listing files...")
    try:
        files = service.list_files()
        for file_info in files:
            print(f"   📄 {file_info['file_name']} (ID: {file_info['file_id']})")
    except Exception as e:
        print(f"   ❌ Failed to list files: {e}")
    
    # Query similar files
    print("\n🔍 Querying similar files...")
    try:
        # Create a query vector (you would typically get this from user input)
        embedding_service = EmbeddingService()
        query_text = "machine learning algorithms"
        query_vector = embedding_service.generate_text_embedding(query_text)
        
        results = service.query_similar(
            query_vector=query_vector,
            top_k=3,
            similarity_threshold=0.1
        )
        
        print(f"   Query: '{query_text}'")
        print(f"   Found {len(results)} similar files:")
        
        for i, result in enumerate(results, 1):
            file_metadata = result['file_metadata']
            print(f"   {i}. {file_metadata.get('file_name', 'unknown')}")
            print(f"      Similarity: {result['similarity_score']:.4f}")
            print(f"      File ID: {result['file_id']}")
    
    except Exception as e:
        print(f"   ❌ Failed to query files: {e}")
    
    # Get specific file info
    if uploaded_files:
        print(f"\n📖 Getting file info for {uploaded_files[0]}...")
        try:
            file_info = service.get_file_info(uploaded_files[0])
            if file_info:
                metadata = file_info['file_metadata']
                print(f"   File: {metadata.get('file_name', 'unknown')}")
                print(f"   Size: {metadata.get('file_size', 0)} bytes")
                print(f"   Vector Dimension: {file_info['vector_dimension']}")
                print(f"   Category: {metadata.get('category', 'N/A')}")
        except Exception as e:
            print(f"   ❌ Failed to get file info: {e}")
    
    # Clean up sample files
    print("\n🧹 Cleaning up sample files...")
    for file_path in sample_files:
        try:
            os.unlink(file_path)
        except:
            pass
    
    print("\n✅ Example completed!")


def example_api_usage():
    """Example of how to use the REST API"""
    print("\n🌐 REST API Usage Example")
    print("=" * 50)
    
    print("Start the service with: python -m uvicorn app.main:app --reload")
    print("\nThen use these endpoints:")
    print("  POST /upload - Upload a single file")
    print("  POST /upload-batch - Upload multiple files")
    print("  POST /query - Query similar files")
    print("  GET /files - List all files")
    print("  GET /files/{file_id} - Get file info")
    print("  DELETE /files/{file_id} - Delete a file")
    print("  GET /health - Health check")
    print("\nAPI Documentation: http://localhost:8000/docs")


if __name__ == "__main__":
    example_usage()
    example_api_usage() 