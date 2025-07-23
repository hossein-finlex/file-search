import unittest
import tempfile
import os
import json
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

from app.services.s3vector_service import S3VectorService
from app.services.embedding_service import EmbeddingService


class TestEmbeddingService(unittest.TestCase):
    """Test cases for the EmbeddingService"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.embedding_service = EmbeddingService()
    
    def test_generate_text_embedding(self):
        """Test text embedding generation"""
        text = "This is a test document"
        embedding = self.embedding_service.generate_text_embedding(text)
        
        self.assertIsInstance(embedding, list)
        self.assertGreater(len(embedding), 0)
        self.assertIsInstance(embedding[0], float)
    
    def test_get_embedding_dimension(self):
        """Test getting embedding dimension"""
        dimension = self.embedding_service.get_embedding_dimension()
        self.assertIsInstance(dimension, int)
        self.assertGreater(dimension, 0)
    
    def test_similarity_score(self):
        """Test similarity score calculation"""
        embedding1 = [0.1, 0.2, 0.3]
        embedding2 = [0.1, 0.2, 0.3]
        
        similarity = self.embedding_service.similarity_score(embedding1, embedding2)
        self.assertIsInstance(similarity, float)
        self.assertGreaterEqual(similarity, 0.0)
        self.assertLessEqual(similarity, 1.0)
    
    def test_generate_file_embedding(self):
        """Test file embedding generation"""
        # Create a temporary text file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
            f.write("This is a test file for embedding generation.")
            file_path = f.name
        
        try:
            embedding = self.embedding_service.generate_file_embedding(file_path)
            self.assertIsInstance(embedding, list)
            self.assertGreater(len(embedding), 0)
        finally:
            os.unlink(file_path)


class TestS3VectorService(unittest.TestCase):
    """Test cases for the S3VectorService"""
    
    def setUp(self):
        """Set up test fixtures"""
        # Mock environment variables
        self.env_patcher = patch.dict(os.environ, {
            'S3_VECTOR_BUCKET_NAME': 'test-bucket',
            'S3_VECTOR_INDEX_NAME': 'test-bucket-index-2',
            'AWS_REGION': 'us-east-1'
        })
        self.env_patcher.start()
        
        # Mock both s3vectors and s3 clients
        self.s3vectors_client_mock = Mock()
        self.s3_client_mock = Mock()
        
        def mock_boto3_client(service_name, **kwargs):
            if service_name == 's3vectors':
                return self.s3vectors_client_mock
            elif service_name == 's3':
                return self.s3_client_mock
            return Mock()
        
        self.boto3_patcher = patch('boto3.client', side_effect=mock_boto3_client)
        self.boto3_patcher.start()
        
        # Mock embedding service
        self.embedding_service_mock = Mock()
        self.embedding_patcher = patch('app.services.s3vector_service.EmbeddingService', 
                                     return_value=self.embedding_service_mock)
        self.embedding_patcher.start()
        
        # Set up mock responses for S3 Vectors
        self.s3vectors_client_mock.query_vectors.return_value = {
            'vectors': [
                {
                    'key': 'test-id',
                    'distance': 0.15,  # 1 - 0.85 similarity
                    'metadata': {
                        'file_name': 'test.txt',
                        'file_size': '100',
                        'content_type': 'text/plain',
                        'uploaded_at': '2023-01-01T00:00:00'
                    }
                }
            ]
        }
        self.s3vectors_client_mock.put_vectors.return_value = {}
        
        # Set up mock responses for regular S3
        self.s3_client_mock.upload_file.return_value = None
        self.s3_client_mock.delete_object.return_value = {}
        
        # Mock embedding service
        self.embedding_service_mock.generate_file_embedding.return_value = [0.1, 0.2, 0.3]
        self.embedding_service_mock.generate_text_embedding.return_value = [0.1, 0.2, 0.3]
        self.embedding_service_mock.similarity_score.return_value = 0.85
    
    def tearDown(self):
        """Clean up test fixtures"""
        self.env_patcher.stop()
        self.boto3_patcher.stop()
        self.embedding_patcher.stop()
    
    def test_init_success(self):
        """Test successful service initialization"""
        service = S3VectorService()
        self.assertEqual(service.vector_bucket_name, 'test-bucket')
        self.assertEqual(service.region, 'us-east-1')
    
    def test_init_missing_bucket(self):
        """Test initialization with missing bucket name"""
        with patch.dict(os.environ, {}, clear=True):
            with self.assertRaises(ValueError):
                S3VectorService()
    
    def test_upload_file_success(self):
        """Test successful file upload"""
        service = S3VectorService()
        
        # Create a temporary file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
            f.write("Test content")
            file_path = f.name
        
        try:
            file_id = service.upload_file(file_path, metadata={'test': 'value'})
            self.assertIsInstance(file_id, str)
            self.assertGreater(len(file_id), 0)
        finally:
            os.unlink(file_path)
    
    def test_upload_file_not_found(self):
        """Test file upload with non-existent file"""
        service = S3VectorService()
        
        with self.assertRaises(FileNotFoundError):
            service.upload_file("non_existent_file.txt")
    
    def test_query_similar(self):
        """Test similarity query"""
        service = S3VectorService()
        
        query_vector = [0.1, 0.2, 0.3]
        results = service.query_similar(query_vector, top_k=5)
        
        self.assertIsInstance(results, list)
        if results:  # If results exist
            result = results[0]
            self.assertIn('file_id', result)
            self.assertIn('similarity_score', result)
            self.assertIn('file_metadata', result)
            
        # Verify S3 Vectors API was called correctly
        self.s3vectors_client_mock.query_vectors.assert_called_once()
    
    def test_list_files(self):
        """Test listing files"""
        service = S3VectorService()
        
        files = service.list_files(limit=10)
        self.assertIsInstance(files, list)
        
        # Verify S3 Vectors API was called correctly
        self.s3vectors_client_mock.query_vectors.assert_called()
    
    def test_get_file_info(self):
        """Test getting file information"""
        service = S3VectorService()
        
        # Mock S3 list_objects_v2 response for file
        self.s3_client_mock.list_objects_v2.return_value = {
            'Contents': [
                {'Key': 'files/test-id/test.txt'}
            ]
        }
        
        # Mock head_object response
        mock_metadata = {
            'file_name': 'test.txt',
            'file_size': '100',
            'content_type': 'text/plain',
            'uploaded_at': datetime.utcnow().isoformat()
        }
        
        self.s3_client_mock.head_object.return_value = {
            'Metadata': mock_metadata,
            'ContentType': 'text/plain',
            'LastModified': datetime.utcnow()
        }
        
        # Mock get_object response for vector data
        mock_vector_data = {
            'file_id': 'test-id',
            'embedding': [0.1, 0.2, 0.3],
            'dimension': 3,
            'model': 'test-model'
        }
        
        self.s3_client_mock.get_object.return_value = {
            'Body': Mock(read=lambda: json.dumps(mock_vector_data).encode())
        }
        
        file_info = service.get_file_info('test-id')
        self.assertIsInstance(file_info, dict)
        self.assertIn('file_id', file_info)
        self.assertIn('file_metadata', file_info)
    
    def test_delete_file(self):
        """Test file deletion"""
        service = S3VectorService()
        
        # Mock get_file_info to return file info
        mock_file_info = {
            'file_metadata': {
                'file_name': 'test.txt'
            }
        }
        
        with patch.object(service, 'get_file_info', return_value=mock_file_info):
            result = service.delete_file('test-id')
            self.assertTrue(result)
    
    def test_health_check(self):
        """Test health check"""
        service = S3VectorService()
        
        # Mock embedding service
        self.embedding_service_mock.generate_text_embedding.return_value = [0.1, 0.2, 0.3]
        
        health = service.health_check()
        self.assertIsInstance(health, dict)
        self.assertIn('status', health)
        self.assertIn('s3_vectors_connection', health)


if __name__ == '__main__':
    unittest.main() 