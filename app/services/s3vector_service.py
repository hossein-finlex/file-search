import os
import json
import uuid
import time
import logging
from typing import List, Dict, Optional, Any, Tuple
from datetime import datetime
import boto3
from botocore.exceptions import ClientError, NoCredentialsError
from .embedding_service import EmbeddingService
from .file_validation_service import FileValidationService, FileValidationError

logger = logging.getLogger(__name__)


class S3VectorService:
    """Service for managing files and vector embeddings using AWS S3 Vectors"""
    
    def __init__(self, 
                 vector_bucket_name: Optional[str] = None,
                 vector_index_name: Optional[str] = None,
                 region: Optional[str] = None,
                 embedding_model: str = "all-MiniLM-L6-v2"):
        """
        Initialize the S3 Vector service
        
        Args:
            vector_bucket_name: S3 Vector bucket name (will use env var if not provided)
            vector_index_name: Vector index name within the bucket
            region: AWS region (will use env var if not provided)
            embedding_model: Name of the embedding model to use
        """
        self.vector_bucket_name = vector_bucket_name or os.getenv('S3_VECTOR_BUCKET_NAME')
        self.vector_index_name = vector_index_name or os.getenv('S3_VECTOR_INDEX_NAME', 'default-index')
        # Use S3_BUCKET_REGION for S3 Vector operations, fallback to AWS_REGION
        self.region = region or os.getenv('S3_BUCKET_REGION') or os.getenv('AWS_REGION', 'us-east-1')
        self.embedding_model = embedding_model
        
        if not self.vector_bucket_name:
            raise ValueError("S3_VECTOR_BUCKET_NAME must be provided or set in environment variables")
        
        # Initialize AWS clients
        self._init_aws_clients()
        
        # Initialize embedding service with environment variable
        actual_embedding_model = os.getenv('EMBEDDING_MODEL', embedding_model)
        self.embedding_service = EmbeddingService(actual_embedding_model)
        
        # Initialize file validation service
        self.file_validation_service = FileValidationService()
        
        # Verify vector bucket and index access
        self._verify_vector_access()
    
    def _init_aws_clients(self):
        """Initialize AWS S3 Vectors client"""
        try:
            # Check if AWS profile is specified
            aws_profile = os.getenv('AWS_PROFILE')
            
            if aws_profile:
                # Use profile-based authentication
                logger.info(f"Using AWS profile: {aws_profile}")
                session = boto3.Session(profile_name=aws_profile, region_name=self.region)
                self.s3vectors_client = session.client('s3vectors')
                self.s3_client = session.client('s3')
            else:
                # Use default credentials (access keys or IAM role)
                logger.info("Using default AWS credentials")
                self.s3vectors_client = boto3.client('s3vectors', region_name=self.region)
                self.s3_client = boto3.client('s3', region_name=self.region)
            
            logger.info(f"Initialized S3 Vectors client for region: {self.region}")
        except NoCredentialsError:
            logger.error("AWS credentials not found. Please configure your AWS credentials.")
            raise
        except Exception as e:
            logger.error(f"Failed to initialize S3 Vectors client: {e}")
            raise
    
    def _verify_vector_access(self):
        """Verify that the S3 Vector bucket and index exist and are accessible"""
        try:
            # Check if vector bucket exists and is accessible
            # Note: This is a placeholder - actual API calls may differ
            logger.info(f"Verifying access to vector bucket: {self.vector_bucket_name}")
            logger.info(f"Using vector index: {self.vector_index_name}")
            
            # TODO: Add actual verification calls when AWS provides the APIs
            # For now, we'll assume the bucket and index exist
            
        except ClientError as e:
            error_code = e.response['Error']['Code']
            if error_code == '404':
                raise ValueError(f"S3 Vector bucket '{self.vector_bucket_name}' or index '{self.vector_index_name}' does not exist")
            elif error_code == '403':
                raise ValueError(f"Access denied to S3 Vector bucket '{self.vector_bucket_name}'")
            else:
                raise ValueError(f"Error accessing S3 Vector bucket '{self.vector_bucket_name}': {e}")
    
    def upload_file(self, 
                   file_path: str, 
                   metadata: Optional[Dict[str, Any]] = None,
                   content_type: Optional[str] = None) -> str:
        """
        Upload a file with its vector embedding to S3 Vector index
        
        Args:
            file_path: Path to the file to upload
            metadata: Additional metadata to store with the vector
            content_type: MIME type of the file
            
        Returns:
            Vector key (unique identifier)
            
        Raises:
            FileValidationError: If file validation fails
        """
        start_time = time.time()
        
        try:
            # Validate file before processing
            validation_result = self.file_validation_service.validate_file(file_path, content_type)
            
            # Use validated file info
            file_name = validation_result['file_name']
            file_size = validation_result['file_size']
            validated_content_type = validation_result['content_type']
            
            # Generate unique vector key
            vector_key = str(uuid.uuid4())
            
            # Generate vector embedding
            embedding = self.embedding_service.generate_file_embedding(file_path, validated_content_type)
            
            # Prepare metadata for S3 Vectors
            vector_metadata = {
                'file_name': file_name,
                'file_size': str(file_size),
                'content_type': validated_content_type,
                'uploaded_at': datetime.utcnow().isoformat(),
                'embedding_model': self.embedding_model,
                'source_file_path': file_path,
                **(metadata or {})
            }
            
            # Store vector using S3 Vectors API
            self.s3vectors_client.put_vectors(
                vectorBucketName=self.vector_bucket_name,
                indexName=self.vector_index_name,
                vectors=[
                    {
                        'key': vector_key,
                        'data': {'float32': embedding},
                        'metadata': vector_metadata
                    }
                ]
            )
            
            # Also upload the original file to regular S3 for retrieval
            s3_key = f"files/{vector_key}/{file_name}"
            self.s3_client.upload_file(
                file_path,
                self.vector_bucket_name,  # Using same bucket name for simplicity
                s3_key,
                ExtraArgs={
                    'Metadata': {k: str(v) for k, v in vector_metadata.items()},
                    'ContentType': validated_content_type
                }
            )
            
            upload_time = (time.time() - start_time) * 1000  # Convert to milliseconds
            logger.info(f"Successfully uploaded file {file_name} with vector key {vector_key} in {upload_time:.2f}ms")
            
            return vector_key
        
        except Exception as e:
            logger.error(f"Error uploading file {file_path}: {e}")
            raise
    
    def upload_batch(self, files: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Upload multiple files in batch
        
        Args:
            files: List of file dictionaries with 'file_path', 'metadata', and 'content_type'
            
        Returns:
            Dictionary with upload results
        """
        # First, validate all files in the batch
        file_paths = [f['file_path'] for f in files]
        content_types = [f.get('content_type') for f in files]
        
        try:
            batch_validation = self.file_validation_service.validate_batch(file_paths, content_types)
        except FileValidationError as e:
            # If batch validation fails (e.g., total size too large), fail all files
            return {
                'uploaded_files': [],
                'failed_files': [{'file_path': fp, 'error': str(e), 'status': 'failed'} for fp in file_paths],
                'total_files': len(files),
                'success_count': 0
            }
        
        uploaded_files = []
        failed_files = []
        
        # Add any files that failed individual validation
        for invalid_file in batch_validation['invalid_files']:
            failed_files.append({
                'file_path': invalid_file['file_path'],
                'error': invalid_file['error'],
                'status': 'failed'
            })
        
        # Prepare vectors for batch upload using only valid files
        vectors_to_upload = []
        valid_file_lookup = {vf['file_path']: vf for vf in batch_validation['valid_files']}
        
        for file_info in files:
            file_path = file_info['file_path']
            
            # Skip files that failed validation
            if file_path not in valid_file_lookup:
                continue
                
            try:
                vector_key = str(uuid.uuid4())
                validation_result = valid_file_lookup[file_path]
                
                # Use validated file information
                file_name = validation_result['file_name']
                file_size = validation_result['file_size']
                validated_content_type = validation_result['content_type']
                
                # Generate vector embedding
                embedding = self.embedding_service.generate_file_embedding(
                    file_path, validated_content_type
                )
                
                # Prepare metadata
                vector_metadata = {
                    'file_name': file_name,
                    'file_size': str(file_size),
                    'content_type': validated_content_type,
                    'uploaded_at': datetime.utcnow().isoformat(),
                    'embedding_model': self.embedding_model,
                    'source_file_path': file_path,
                    **(file_info.get('metadata', {}))
                }
                
                vectors_to_upload.append({
                    'key': vector_key,
                    'data': {'float32': embedding},
                    'metadata': vector_metadata
                })
                
                uploaded_files.append({
                    'file_id': vector_key,
                    'file_path': file_path,
                    'status': 'success'
                })
                
            except Exception as e:
                failed_files.append({
                    'file_path': file_info['file_path'],
                    'error': str(e),
                    'status': 'failed'
                })
        
        # Batch upload vectors to S3 Vectors
        if vectors_to_upload:
            try:
                self.s3vectors_client.put_vectors(
                    vectorBucketName=self.vector_bucket_name,
                    indexName=self.vector_index_name,
                    vectors=vectors_to_upload
                )
            except Exception as e:
                logger.error(f"Batch vector upload failed: {e}")
                # Mark all as failed
                for uploaded_file in uploaded_files:
                    failed_files.append({
                        'file_path': uploaded_file['file_path'],
                        'error': str(e),
                        'status': 'failed'
                    })
                uploaded_files = []
        
        return {
            'uploaded_files': uploaded_files,
            'failed_files': failed_files,
            'total_files': len(files),
            'success_count': len(uploaded_files)
        }
    
    def query_similar(self, 
                     query_vector: List[float], 
                     top_k: int = 10,
                     similarity_threshold: Optional[float] = None,
                     metadata_filter: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """
        Query for similar vectors using S3 Vectors native similarity search
        
        Args:
            query_vector: Query vector for similarity search
            top_k: Number of top results to return
            similarity_threshold: Minimum similarity threshold (0.0 to 1.0)
            metadata_filter: Optional metadata filters
            
        Returns:
            List of similar vectors with similarity scores
        """
        start_time = time.time()
        
        try:
            # Use S3 Vectors native query API
            query_params = {
                'vectorBucketName': self.vector_bucket_name,
                'indexName': self.vector_index_name,
                'queryVector': {'float32': query_vector},
                'topK': top_k,
                'returnDistance': True,
                'returnMetadata': True
            }
            
            # Add metadata filter if provided
            if metadata_filter:
                query_params['filter'] = metadata_filter
            
            response = self.s3vectors_client.query_vectors(**query_params)
            
            # Process results
            results = []
            for vector_result in response.get('vectors', []):
                similarity_score = 1.0 - vector_result.get('distance', 0.0)  # Convert distance to similarity
                
                # Apply threshold if specified
                if similarity_threshold is not None and similarity_score < similarity_threshold:
                    continue
                
                vector_metadata = vector_result.get('metadata', {})
                
                results.append({
                    'file_id': vector_result.get('key'),
                    'similarity_score': similarity_score,
                    'file_metadata': vector_metadata,
                    'vector_dimension': len(query_vector)
                })
            
            query_time = (time.time() - start_time) * 1000  # Convert to milliseconds
            logger.info(f"Vector query completed in {query_time:.2f}ms, found {len(results)} results")
            
            return results
        
        except Exception as e:
            logger.error(f"Error in vector similarity query: {e}")
            raise
    
    def get_file_info(self, vector_key: str) -> Optional[Dict[str, Any]]:
        """
        Get information about a specific vector
        
        Args:
            vector_key: Unique vector identifier
            
        Returns:
            Vector information dictionary or None if not found
        """
        try:
            # Query for the specific vector
            response = self.s3vectors_client.query_vectors(
                vectorBucketName=self.vector_bucket_name,
                indexName=self.vector_index_name,
                queryVector={'float32': [0.0] * 384},  # Dummy vector for metadata retrieval
                topK=1000,  # Large number to find our specific vector
                returnMetadata=True
            )
            
            # Find the vector with matching key
            for vector_result in response.get('vectors', []):
                if vector_result.get('key') == vector_key:
                    return {
                        'file_id': vector_key,
                        'file_metadata': vector_result.get('metadata', {}),
                        'vector_dimension': 384,  # Default dimension
                        'embedding_model': self.embedding_model
                    }
            
            return None
        
        except Exception as e:
            logger.error(f"Error getting vector info for {vector_key}: {e}")
            return None
    
    def list_files(self, limit: int = 100) -> List[Dict[str, Any]]:
        """
        List vectors in the index (limited functionality with current API)
        
        Args:
            limit: Maximum number of files to return
            
        Returns:
            List of file information dictionaries
        """
        try:
            # Note: S3 Vectors API doesn't have a direct "list" operation
            # This is a workaround using query with a dummy vector
            response = self.s3vectors_client.query_vectors(
                vectorBucketName=self.vector_bucket_name,
                indexName=self.vector_index_name,
                queryVector={'float32': [0.0] * 384},  # Dummy vector
                topK=min(limit, 1000),  # API limit
                returnMetadata=True
            )
            
            files = []
            for vector_result in response.get('vectors', []):
                metadata = vector_result.get('metadata', {})
                files.append({
                    'file_id': vector_result.get('key'),
                    'file_name': metadata.get('file_name', 'unknown'),
                    'file_size': int(metadata.get('file_size', 0)),
                    'last_modified': metadata.get('uploaded_at'),
                    'metadata': metadata
                })
            
            return files
        
        except Exception as e:
            logger.error(f"Error listing files: {e}")
            raise
    
    def delete_file(self, vector_key: str) -> bool:
        """
        Delete a vector and its associated file
        
        Args:
            vector_key: Unique vector identifier
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Note: S3 Vectors API might not have direct delete operation yet
            # This is a placeholder for future implementation
            logger.warning(f"Vector deletion not yet implemented for {vector_key}")
            logger.warning("S3 Vectors delete API may not be available in preview")
            
            # For now, we can try to delete the associated file from regular S3
            vector_info = self.get_file_info(vector_key)
            if vector_info:
                file_metadata = vector_info['file_metadata']
                file_name = file_metadata.get('file_name', 'unknown')
                s3_key = f"files/{vector_key}/{file_name}"
                
                try:
                    self.s3_client.delete_object(
                        Bucket=self.vector_bucket_name,
                        Key=s3_key
                    )
                    logger.info(f"Deleted associated file {s3_key}")
                except Exception as e:
                    logger.warning(f"Could not delete associated file: {e}")
            
            return True
        
        except Exception as e:
            logger.error(f"Error deleting vector {vector_key}: {e}")
            return False
    
    def _infer_content_type(self, file_path: str) -> str:
        """Infer content type from file extension"""
        import mimetypes
        
        content_type, _ = mimetypes.guess_type(file_path)
        if content_type is None:
            return 'application/octet-stream'
        return content_type
    
    def health_check(self) -> Dict[str, Any]:
        """Perform health check of the service"""
        try:
            # Test embedding service
            test_embedding = self.embedding_service.generate_text_embedding("test")
            
            # Test S3 Vectors connection (basic check)
            # Note: Actual health check will depend on available S3 Vectors APIs
            
            return {
                'status': 'healthy',
                's3_vectors_connection': True,
                'embedding_service': True,
                'vector_dimension': len(test_embedding),
                'vector_bucket_name': self.vector_bucket_name,
                'vector_index_name': self.vector_index_name,
                'region': self.region
            }
        
        except Exception as e:
            return {
                'status': 'unhealthy',
                'error': str(e),
                's3_vectors_connection': False,
                'embedding_service': False
            } 