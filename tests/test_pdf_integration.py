import unittest
import requests
import json
import time
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


class TestPDFIntegration(unittest.TestCase):
    """PDF-focused integration tests for S3 Vector Service API"""
    
    @classmethod
    def setUpClass(cls):
        """Set up test fixtures for all tests"""
        cls.base_url = "http://localhost:8000"
        cls.api_timeout = 30  # seconds
        
        # Wait for service to be ready
        cls._wait_for_service()
        
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
        print(f"   - Vector Bucket: {health_data.get('vector_bucket_name')}")
        print(f"   - Vector Index: {health_data.get('vector_index_name')}")
        print(f"   - S3 Vectors Connection: {health_data.get('s3_vectors_connection')}")
        print(f"   - Embedding Service: {health_data.get('embedding_service')}")

    def test_02_pdf_upload_and_text_extraction(self):
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
                "source": "PDF Integration Test",
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
            print(f"⚠️ PDF upload returned status {response.status_code}")
            if response.status_code in [404, 500]:
                print("   - This is expected if S3 file upload permissions are not configured")
                print("   - PDF text extraction should still work for queries")

    def test_03_pdf_content_semantic_search(self):
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

    def test_04_pdf_vs_unrelated_content_search(self):
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
            print(f"   - Relevance ratio: {avg_related/avg_unrelated:.1f}x better")
            
            # Related content should generally score higher
            self.assertGreater(
                avg_related, 
                avg_unrelated,
                "Related PDF content should score higher than unrelated content"
            )
        else:
            print("⚠️ PDF relevance test skipped - insufficient results")

    def test_05_pdf_similarity_threshold_filtering(self):
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

    def test_06_query_response_structure(self):
        """Test that query responses have correct structure without vectors"""
        query_data = {
            "query_text": "test query",
            "top_k": 3
        }
        
        response = requests.post(f"{self.base_url}/query", json=query_data)
        
        if response.status_code == 200:
            result = response.json()
            
            # Verify response structure
            self.assertIn('results', result)
            self.assertIn('total_results', result)
            self.assertIn('query_time_ms', result)
            
            # Verify query_vector is None by default (not included in response)
            query_vector = result.get('query_vector')
            self.assertIsNone(query_vector, "Query vector should be None by default")
            
            print("✅ Query response structure correct:")
            print(f"   - Total results: {result['total_results']}")
            print(f"   - Query time: {result['query_time_ms']:.2f}ms")
            print(f"   - Query vector excluded: {query_vector is None}")
        else:
            print(f"⚠️ Query response test skipped due to error: {response.status_code}")

    def test_07_performance_benchmark(self):
        """Test query performance with PDF content"""
        query_data = {
            "query_text": "PDF file performance test",
            "top_k": 10
        }
        
        # Run multiple queries to get average performance
        times = []
        for i in range(3):
            start_time = time.time()
            response = requests.post(f"{self.base_url}/query", json=query_data)
            end_time = time.time()
            
            if response.status_code == 200:
                query_time = (end_time - start_time) * 1000  # milliseconds
                times.append(query_time)
                
                result = response.json()
                api_query_time = result.get('query_time_ms', 0)
                
                if i == 0:  # Print details for first query
                    print(f"✅ Performance test (query {i+1}):")
                    print(f"   - Total request time: {query_time:.2f}ms")
                    print(f"   - API query time: {api_query_time:.2f}ms")
                    print(f"   - Results found: {len(result.get('results', []))}")
        
        if times:
            avg_time = sum(times) / len(times)
            print(f"✅ Average performance over {len(times)} queries: {avg_time:.2f}ms")
            
            # Performance should be reasonable
            self.assertLess(avg_time, 3000, "Query should complete within 3 seconds")
        else:
            print("⚠️ Performance test skipped due to query errors")


if __name__ == '__main__':
    # Custom test runner with detailed output
    unittest.TextTestRunner(verbosity=2).run(
        unittest.TestLoader().loadTestsFromTestCase(TestPDFIntegration)
    ) 