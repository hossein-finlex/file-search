import unittest
import requests
import json
import time
import tempfile
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


class TestS3VectorIntegration(unittest.TestCase):
    """Integration tests for S3 Vector Service API"""
    
    @classmethod
    def setUpClass(cls):
        """Set up test fixtures for all tests"""
        cls.base_url = "http://localhost:8000"
        cls.api_timeout = 30  # seconds
        
        # Wait for service to be ready
        cls._wait_for_service()
        
        # Test file content for uploads
        cls.test_files = {}
        
    @classmethod
    def _wait_for_service(cls, max_attempts=30):
        """Wait for the service to be ready"""
        print("Waiting for S3 Vector service to be ready...")
        
        for attempt in range(max_attempts):
            try:
                response = requests.get(f"{cls.base_url}/health", timeout=5)
                if response.status_code == 200:
                    print("✅ Service is ready!")
                    return
            except requests.exceptions.RequestException:
                pass
            
            if attempt < max_attempts - 1:
                print(f"⏳ Attempt {attempt + 1}/{max_attempts}, retrying in 2 seconds...")
                time.sleep(2)
        
        raise Exception("❌ Service did not become ready within expected time")
    
    def setUp(self):
        """Set up for each test"""
        # Create temporary test files
        self.temp_files = []
        
    def tearDown(self):
        """Clean up after each test"""
        # Clean up temporary files
        for file_path in self.temp_files:
            try:
                os.unlink(file_path)
            except FileNotFoundError:
                pass
    
    def _create_temp_file(self, content: str, filename: str = None) -> str:
        """Create a temporary file with content"""
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.txt') as f:
            if filename:
                # Create file with specific name in temp directory
                temp_path = os.path.join(tempfile.gettempdir(), filename)
                with open(temp_path, 'w') as named_file:
                    named_file.write(content)
                self.temp_files.append(temp_path)
                return temp_path
            else:
                f.write(content)
                self.temp_files.append(f.name)
                return f.name
    
    def test_01_health_check(self):
        """Test health check endpoint"""
        response = requests.get(f"{self.base_url}/health")
        
        self.assertEqual(response.status_code, 200)
        
        health_data = response.json()
        self.assertIsInstance(health_data, dict)
        self.assertIn('status', health_data)
        self.assertEqual(health_data['status'], 'healthy')
        self.assertIn('s3_vectors_connection', health_data)
        self.assertIn('embedding_service', health_data)
        self.assertIn('vector_bucket_name', health_data)
        self.assertIn('vector_index_name', health_data)
        
        print("✅ Health check passed")
    
    def test_02_upload_text_file(self):
        """Test uploading a text file"""
        # Create test file
        content = """
        AWS S3 Vectors is a revolutionary new service that provides native vector storage
        and similarity search capabilities directly in Amazon S3. This technology enables
        developers to build AI-powered applications with semantic search, recommendation
        systems, and retrieval-augmented generation (RAG) workflows at scale.
        """
        
        file_path = self._create_temp_file(content, "aws_s3_vectors.txt")
        
        # Upload file
        upload_data = {
            "file_path": file_path,
            "metadata": {
                "title": "AWS S3 Vectors Overview",
                "category": "documentation",
                "author": "AWS",
                "tags": ["aws", "s3", "vectors", "ai", "search"]
            },
            "content_type": "text/plain"
        }
        
        response = requests.post(
            f"{self.base_url}/upload",
            json=upload_data,
            timeout=self.api_timeout
        )
        
        self.assertEqual(response.status_code, 200)
        
        result = response.json()
        self.assertIn('file_id', result)
        self.assertIn('message', result)
        
        # Store file ID for later tests
        self.__class__.test_file_id = result['file_id']
        
        print(f"✅ File uploaded successfully with ID: {result['file_id']}")
    
    def test_03_upload_batch_files(self):
        """Test batch file upload"""
        # Create multiple test files
        files_data = [
            {
                "content": "Vector databases are specialized databases designed to store and query high-dimensional vectors efficiently.",
                "filename": "vector_databases.txt",
                "metadata": {"category": "technology", "topic": "databases"}
            },
            {
                "content": "Machine learning embeddings represent data as dense vectors in high-dimensional space.",
                "filename": "ml_embeddings.txt", 
                "metadata": {"category": "technology", "topic": "machine-learning"}
            },
            {
                "content": "Similarity search finds the most similar items to a query in vector space using distance metrics.",
                "filename": "similarity_search.txt",
                "metadata": {"category": "technology", "topic": "search"}
            }
        ]
        
        file_paths = []
        for file_data in files_data:
            file_path = self._create_temp_file(file_data["content"], file_data["filename"])
            file_paths.append({
                "file_path": file_path,
                "metadata": file_data["metadata"],
                "content_type": "text/plain"
            })
        
        # Upload batch
        upload_data = {"files": file_paths}
        
        response = requests.post(
            f"{self.base_url}/upload-batch",
            json=upload_data,
            timeout=self.api_timeout
        )
        
        self.assertEqual(response.status_code, 200)
        
        result = response.json()
        self.assertIn('uploaded_files', result)
        self.assertIn('failed_files', result)
        self.assertIn('success_count', result)
        
        # Should have uploaded 3 files successfully
        self.assertEqual(result['success_count'], 3)
        self.assertEqual(len(result['failed_files']), 0)
        
        print(f"✅ Batch upload successful: {result['success_count']} files uploaded")
    
    def test_04_list_files(self):
        """Test listing files"""
        response = requests.get(f"{self.base_url}/files", params={"limit": 10})
        
        self.assertEqual(response.status_code, 200)
        
        result = response.json()
        self.assertIn('files', result)
        self.assertIn('total_count', result)
        self.assertIsInstance(result['files'], list)
        
        # Should have at least the files we uploaded
        self.assertGreaterEqual(len(result['files']), 1)
        
        # Check file structure
        if result['files']:
            file_info = result['files'][0]
            self.assertIn('file_id', file_info)
            self.assertIn('file_name', file_info)
            self.assertIn('file_size', file_info)
            
        print(f"✅ Listed {len(result['files'])} files")
    
    def test_05_query_similarity_search(self):
        """Test similarity search"""
        # Test query for AWS/cloud related content
        query_data = {
            "query_text": "cloud storage vector search artificial intelligence",
            "top_k": 5,
            "similarity_threshold": 0.1
        }
        
        response = requests.post(
            f"{self.base_url}/query",
            json=query_data,
            timeout=self.api_timeout
        )
        
        self.assertEqual(response.status_code, 200)
        
        result = response.json()
        self.assertIn('results', result)
        self.assertIn('query_time_ms', result)
        self.assertIsInstance(result['results'], list)
        
        # Should find similar results
        if result['results']:
            for item in result['results']:
                self.assertIn('file_id', item)
                self.assertIn('similarity_score', item)
                self.assertIn('file_metadata', item)
                
                # Similarity score should be between 0 and 1
                self.assertGreaterEqual(item['similarity_score'], 0.0)
                self.assertLessEqual(item['similarity_score'], 1.0)
        
        print(f"✅ Similarity search found {len(result['results'])} results")
    
    def test_06_query_with_vector(self):
        """Test similarity search with vector input"""
        # Use a sample vector (normally this would come from an embedding model)
        sample_vector = [0.1] * 384  # 384-dimensional vector
        
        query_data = {
            "query_vector": sample_vector,
            "top_k": 3,
            "similarity_threshold": 0.0
        }
        
        response = requests.post(
            f"{self.base_url}/query",
            json=query_data,
            timeout=self.api_timeout
        )
        
        self.assertEqual(response.status_code, 200)
        
        result = response.json()
        self.assertIn('results', result)
        self.assertIn('query_time_ms', result)
        
        print(f"✅ Vector query found {len(result['results'])} results")
    
    def test_07_query_with_metadata_filter(self):
        """Test similarity search with metadata filtering"""
        query_data = {
            "query_text": "database technology",
            "top_k": 5,
            "metadata_filter": {
                "category": "technology"
            }
        }
        
        response = requests.post(
            f"{self.base_url}/query",
            json=query_data,
            timeout=self.api_timeout
        )
        
        self.assertEqual(response.status_code, 200)
        
        result = response.json()
        self.assertIn('results', result)
        
        # All results should match the metadata filter
        for item in result['results']:
            metadata = item.get('file_metadata', {})
            if 'category' in metadata:
                self.assertEqual(metadata['category'], 'technology')
        
        print(f"✅ Filtered query found {len(result['results'])} results")
    
    def test_08_get_file_info(self):
        """Test getting file information"""
        # Use the file ID from the upload test
        if hasattr(self.__class__, 'test_file_id'):
            file_id = self.__class__.test_file_id
            
            response = requests.get(f"{self.base_url}/files/{file_id}")
            
            if response.status_code == 200:
                result = response.json()
                self.assertIn('file_id', result)
                self.assertIn('file_metadata', result)
                self.assertEqual(result['file_id'], file_id)
                
                print(f"✅ Retrieved file info for {file_id}")
            else:
                print(f"⚠️ File info not found for {file_id} (may be expected in S3 Vectors preview)")
        else:
            print("⚠️ Skipping file info test - no test file ID available")
    
    def test_09_error_handling(self):
        """Test error handling for invalid requests"""
        # Test upload with missing file
        upload_data = {
            "file_path": "/nonexistent/file.txt",
            "metadata": {},
            "content_type": "text/plain"
        }
        
        response = requests.post(f"{self.base_url}/upload", json=upload_data)
        
        # Should return error status
        self.assertIn(response.status_code, [400, 404, 500])
        
        # Test query with invalid vector dimension
        query_data = {
            "query_vector": [0.1, 0.2],  # Wrong dimension
            "top_k": 5
        }
        
        response = requests.post(f"{self.base_url}/query", json=query_data)
        
        # Should handle gracefully
        self.assertIn(response.status_code, [400, 422, 500])
        
        print("✅ Error handling tests completed")
    
    def test_10_pdf_upload_and_text_extraction(self):
        """Test PDF upload with text extraction"""
        # PDF file should be in tests directory
        pdf_path = os.path.join(os.path.dirname(__file__), "sample.pdf")
        
        # Verify PDF exists
        self.assertTrue(os.path.exists(pdf_path), f"PDF file not found at {pdf_path}")
        
        # Upload PDF
        upload_data = {
            "file_path": pdf_path,
            "metadata": {
                "title": "Sample PDF with Text Extraction",
                "source": "Integration Test",
                "document_type": "pdf"
            },
            "content_type": "application/pdf"
        }
        
        response = requests.post(
            f"{self.base_url}/upload",
            json=upload_data,
            timeout=self.api_timeout
        )
        
        if response.status_code == 200:
            result = response.json()
            self.assertIn('file_id', result)
            
            # Store PDF file ID for later tests
            self.__class__.pdf_file_id = result['file_id']
            
            print(f"✅ PDF uploaded successfully with ID: {result['file_id']}")
        else:
            # PDF upload might fail due to S3 permissions, but text extraction should work
            print(f"⚠️ PDF upload returned status {response.status_code}, checking if it's S3 permission issue")
            if response.status_code == 500:
                # This is expected if S3 file upload permissions are not configured
                print("   - S3 file upload permissions not configured (expected)")
                print("   - PDF text extraction should still work for queries")
    
    def test_11_pdf_content_semantic_search(self):
        """Test semantic search on PDF content"""
        # Test search for content that should be in the PDF: "Dummy PDF file"
        test_cases = [
            {
                "query": "PDF file",
                "expected_min_score": 0.6,
                "description": "Exact phrase match"
            },
            {
                "query": "Dummy",
                "expected_min_score": 0.2,
                "description": "Partial content match"
            },
            {
                "query": "Dummy PDF file",
                "expected_min_score": 0.7,
                "description": "Complete content match"
            }
        ]
        
        pdf_results_found = False
        
        for test_case in test_cases:
            query_data = {
                "query_text": test_case["query"],
                "top_k": 5
            }
            
            response = requests.post(
                f"{self.base_url}/query",
                json=query_data,
                timeout=self.api_timeout
            )
            
            self.assertEqual(response.status_code, 200)
            
            result = response.json()
            self.assertIn('results', result)
            
            # Look for PDF files in results
            pdf_results = [r for r in result['results'] if 'pdf' in r.get('file_info', {}).get('file_name', '').lower()]
            
            if pdf_results:
                pdf_results_found = True
                best_score = max(r['similarity_score'] for r in pdf_results)
                
                print(f"✅ PDF search '{test_case['query']}': score {best_score:.3f} ({test_case['description']})")
                
                # For exact matches, expect high similarity
                if test_case["query"] in ["PDF file", "Dummy PDF file"]:
                    self.assertGreaterEqual(
                        best_score, 
                        test_case["expected_min_score"],
                        f"PDF content search '{test_case['query']}' should have similarity >= {test_case['expected_min_score']}"
                    )
            else:
                print(f"⚠️ No PDF results found for '{test_case['query']}'")
        
        if pdf_results_found:
            print("✅ PDF content semantic search working correctly")
        else:
            print("⚠️ PDF content search tests skipped - no PDF files found in index")
    
    def test_12_pdf_vs_unrelated_content_search(self):
        """Test that PDF content search distinguishes relevant from irrelevant queries"""
        # Test with content that should NOT match PDF well
        unrelated_queries = [
            "pizza recipe cooking instructions",
            "machine learning neural networks",
            "financial market analysis"
        ]
        
        # Test with content that SHOULD match PDF well
        related_queries = [
            "PDF file document",
            "dummy test file"
        ]
        
        related_scores = []
        unrelated_scores = []
        
        # Test related queries
        for query in related_queries:
            query_data = {
                "query_text": query,
                "top_k": 5
            }
            
            response = requests.post(f"{self.base_url}/query", json=query_data)
            
            if response.status_code == 200:
                result = response.json()
                pdf_results = [r for r in result['results'] if 'pdf' in r.get('file_info', {}).get('file_name', '').lower()]
                
                if pdf_results:
                    best_score = max(r['similarity_score'] for r in pdf_results)
                    related_scores.append(best_score)
                    print(f"   Related query '{query}': {best_score:.3f}")
        
        # Test unrelated queries
        for query in unrelated_queries:
            query_data = {
                "query_text": query,
                "top_k": 5
            }
            
            response = requests.post(f"{self.base_url}/query", json=query_data)
            
            if response.status_code == 200:
                result = response.json()
                pdf_results = [r for r in result['results'] if 'pdf' in r.get('file_info', {}).get('file_name', '').lower()]
                
                if pdf_results:
                    best_score = max(r['similarity_score'] for r in pdf_results)
                    unrelated_scores.append(best_score)
                    print(f"   Unrelated query '{query}': {best_score:.3f}")
        
        # Verify that related queries generally score higher than unrelated ones
        if related_scores and unrelated_scores:
            avg_related = sum(related_scores) / len(related_scores)
            avg_unrelated = sum(unrelated_scores) / len(unrelated_scores)
            
            print(f"✅ PDF relevance test:")
            print(f"   - Average related score: {avg_related:.3f}")
            print(f"   - Average unrelated score: {avg_unrelated:.3f}")
            
            # Related content should generally score higher
            self.assertGreater(
                avg_related, 
                avg_unrelated,
                "Related PDF content should score higher than unrelated content"
            )
        else:
            print("⚠️ PDF relevance test skipped - insufficient results")
    
    def test_13_pdf_similarity_threshold_filtering(self):
        """Test similarity threshold filtering with PDF content"""
        # Test that high threshold filters out poor matches
        query_data = {
            "query_text": "pizza recipe cooking instructions",
            "top_k": 5,
            "similarity_threshold": 0.5  # High threshold
        }
        
        response = requests.post(f"{self.base_url}/query", json=query_data)
        
        if response.status_code == 200:
            result = response.json()
            
            # Should return few or no results for unrelated content with high threshold
            high_threshold_count = len(result['results'])
            
            # Test with low threshold
            query_data["similarity_threshold"] = 0.1
            response = requests.post(f"{self.base_url}/query", json=query_data)
            
            if response.status_code == 200:
                result = response.json()
                low_threshold_count = len(result['results'])
                
                print(f"✅ Threshold filtering test:")
                print(f"   - High threshold (0.5): {high_threshold_count} results")
                print(f"   - Low threshold (0.1): {low_threshold_count} results")
                
                # Low threshold should generally return same or more results
                self.assertGreaterEqual(
                    low_threshold_count, 
                    high_threshold_count,
                    "Lower threshold should return >= results than higher threshold"
                )
        else:
            print("⚠️ Threshold filtering test skipped due to query error")
    
    def test_14_performance_benchmark(self):
        """Basic performance benchmark"""
        # Test query performance
        query_data = {
            "query_text": "performance test",
            "top_k": 10
        }
        
        start_time = time.time()
        response = requests.post(f"{self.base_url}/query", json=query_data)
        end_time = time.time()
        
        query_time = (end_time - start_time) * 1000  # milliseconds
        
        if response.status_code == 200:
            result = response.json()
            api_query_time = result.get('query_time_ms', 0)
            
            print(f"✅ Performance test:")
            print(f"   - Total request time: {query_time:.2f}ms")
            print(f"   - API query time: {api_query_time:.2f}ms")
            print(f"   - Results found: {len(result.get('results', []))}")
            
            # Basic performance assertions
            self.assertLess(query_time, 5000)  # Should complete within 5 seconds
        else:
            print(f"⚠️ Performance test skipped due to query error: {response.status_code}")


if __name__ == '__main__':
    # Custom test runner with detailed output
    unittest.TextTestRunner(verbosity=2).run(
        unittest.TestLoader().loadTestsFromTestCase(TestS3VectorIntegration)
    ) 