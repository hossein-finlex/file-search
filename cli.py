#!/usr/bin/env python3
"""
Command Line Interface for S3 Vector Service
"""

import argparse
import json
import sys
import os
from pathlib import Path
from typing import List, Optional

from app.services.s3vector_service import S3VectorService
from app.services.embedding_service import EmbeddingService


def upload_file(service: S3VectorService, file_path: str, metadata: Optional[dict] = None):
    """Upload a single file"""
    try:
        file_id = service.upload_file(file_path, metadata or {})
        print(f"✅ File uploaded successfully: {file_id}")
        return file_id
    except Exception as e:
        print(f"❌ Failed to upload file: {e}")
        return None


def upload_batch(service: S3VectorService, file_paths: List[str], metadata: Optional[dict] = None):
    """Upload multiple files"""
    files = []
    for file_path in file_paths:
        files.append({
            'file_path': file_path,
            'metadata': metadata or {}
        })
    
    try:
        result = service.upload_batch(files)
        print(f"✅ Batch upload completed:")
        print(f"   Successfully uploaded: {result['success_count']}/{result['total_files']}")
        
        if result['failed_files']:
            print("   Failed files:")
            for failed in result['failed_files']:
                print(f"     - {failed['file_path']}: {failed['error']}")
        
        return result
    except Exception as e:
        print(f"❌ Failed to upload batch: {e}")
        return None


def query_similar(service: S3VectorService, query_text: str, top_k: int = 5):
    """Query for similar files using text"""
    try:
        # Generate embedding for query text
        embedding_service = EmbeddingService()
        query_vector = embedding_service.generate_text_embedding(query_text)
        
        # Query similar files
        results = service.query_similar(query_vector, top_k=top_k)
        
        print(f"🔍 Query: '{query_text}'")
        print(f"📊 Found {len(results)} similar files:")
        
        for i, result in enumerate(results, 1):
            file_metadata = result['file_metadata']
            print(f"   {i}. {file_metadata.get('file_name', 'unknown')}")
            print(f"      Similarity: {result['similarity_score']:.4f}")
            print(f"      File ID: {result['file_id']}")
            print(f"      Size: {file_metadata.get('file_size', 0)} bytes")
        
        return results
    except Exception as e:
        print(f"❌ Failed to query files: {e}")
        return None


def list_files(service: S3VectorService, limit: int = 20):
    """List files in the bucket"""
    try:
        files = service.list_files(limit=limit)
        
        print(f"📋 Found {len(files)} files:")
        for file_info in files:
            print(f"   📄 {file_info['file_name']}")
            print(f"      ID: {file_info['file_id']}")
            print(f"      Size: {file_info['file_size']} bytes")
            print(f"      Modified: {file_info['last_modified']}")
        
        return files
    except Exception as e:
        print(f"❌ Failed to list files: {e}")
        return None


def get_file_info(service: S3VectorService, file_id: str):
    """Get information about a specific file"""
    try:
        file_info = service.get_file_info(file_id)
        if not file_info:
            print(f"❌ File {file_id} not found")
            return None
        
        metadata = file_info['file_metadata']
        print(f"📖 File Information:")
        print(f"   ID: {file_id}")
        print(f"   Name: {metadata.get('file_name', 'unknown')}")
        print(f"   Size: {metadata.get('file_size', 0)} bytes")
        print(f"   Type: {metadata.get('content_type', 'unknown')}")
        print(f"   Vector Dimension: {file_info['vector_dimension']}")
        print(f"   Uploaded: {metadata.get('uploaded_at', 'unknown')}")
        
        if metadata.get('category'):
            print(f"   Category: {metadata['category']}")
        
        return file_info
    except Exception as e:
        print(f"❌ Failed to get file info: {e}")
        return None


def delete_file(service: S3VectorService, file_id: str):
    """Delete a file"""
    try:
        success = service.delete_file(file_id)
        if success:
            print(f"✅ File {file_id} deleted successfully")
        else:
            print(f"❌ Failed to delete file {file_id}")
        return success
    except Exception as e:
        print(f"❌ Error deleting file: {e}")
        return False


def health_check(service: S3VectorService):
    """Perform health check"""
    try:
        health = service.health_check()
        print(f"🏥 Health Check:")
        print(f"   Status: {health['status']}")
        print(f"   S3 Connection: {health['s3_connection']}")
        print(f"   Vector Dimension: {health.get('vector_dimension', 'N/A')}")
        print(f"   Bucket: {health.get('bucket_name', 'N/A')}")
        print(f"   Region: {health.get('region', 'N/A')}")
        
        if health['status'] == 'unhealthy':
            print(f"   Error: {health.get('error', 'Unknown error')}")
        
        return health['status'] == 'healthy'
    except Exception as e:
        print(f"❌ Health check failed: {e}")
        return False


def main():
    """Main CLI function"""
    parser = argparse.ArgumentParser(description="S3 Vector Service CLI")
    parser.add_argument("--bucket", help="S3 bucket name")
    parser.add_argument("--region", help="AWS region", default="us-east-1")
    
    subparsers = parser.add_subparsers(dest="command", help="Available commands")
    
    # Upload command
    upload_parser = subparsers.add_parser("upload", help="Upload a file")
    upload_parser.add_argument("file_path", help="Path to the file to upload")
    upload_parser.add_argument("--metadata", help="JSON metadata for the file")
    
    # Batch upload command
    batch_parser = subparsers.add_parser("upload-batch", help="Upload multiple files")
    batch_parser.add_argument("file_paths", nargs="+", help="Paths to files to upload")
    batch_parser.add_argument("--metadata", help="JSON metadata for all files")
    
    # Query command
    query_parser = subparsers.add_parser("query", help="Query similar files")
    query_parser.add_argument("query_text", help="Text to search for")
    query_parser.add_argument("--top-k", type=int, default=5, help="Number of results to return")
    
    # List command
    list_parser = subparsers.add_parser("list", help="List files")
    list_parser.add_argument("--limit", type=int, default=20, help="Maximum number of files to list")
    
    # Info command
    info_parser = subparsers.add_parser("info", help="Get file information")
    info_parser.add_argument("file_id", help="File ID to get information for")
    
    # Delete command
    delete_parser = subparsers.add_parser("delete", help="Delete a file")
    delete_parser.add_argument("file_id", help="File ID to delete")
    
    # Health command
    subparsers.add_parser("health", help="Perform health check")
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return
    
    # Initialize service
    try:
        service = S3VectorService(
            bucket_name=args.bucket,
            region=args.region
        )
    except Exception as e:
        print(f"❌ Failed to initialize service: {e}")
        sys.exit(1)
    
    # Parse metadata if provided
    metadata = None
    if hasattr(args, 'metadata') and args.metadata:
        try:
            metadata = json.loads(args.metadata)
        except json.JSONDecodeError:
            print("❌ Invalid JSON metadata")
            sys.exit(1)
    
    # Execute command
    if args.command == "upload":
        upload_file(service, args.file_path, metadata)
    
    elif args.command == "upload-batch":
        upload_batch(service, args.file_paths, metadata)
    
    elif args.command == "query":
        query_similar(service, args.query_text, args.top_k)
    
    elif args.command == "list":
        list_files(service, args.limit)
    
    elif args.command == "info":
        get_file_info(service, args.file_id)
    
    elif args.command == "delete":
        delete_file(service, args.file_id)
    
    elif args.command == "health":
        health_check(service)


if __name__ == "__main__":
    main() 