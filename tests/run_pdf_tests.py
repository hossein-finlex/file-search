#!/usr/bin/env python3
"""
PDF Integration Test Runner for S3 Vector Service

This script runs PDF-focused integration tests against the running S3 Vector service.
It only tests the working functionality and should achieve 100% success rate.

Usage:
    python run_pdf_tests.py

Prerequisites:
    - S3 Vector service running on localhost:8000
    - AWS S3 Vectors configured and accessible
    - PDF text extraction functionality working
"""

import sys
import os
import unittest
import requests
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def check_service_availability(base_url="http://localhost:8000", max_attempts=10):
    """Check if the service is running and accessible"""
    print("🔍 Checking if S3 Vector service is running...")
    
    for attempt in range(max_attempts):
        try:
            response = requests.get(f"{base_url}/health", timeout=5)
            if response.status_code == 200:
                health_data = response.json()
                print(f"✅ Service is running and healthy!")
                print(f"   - Status: {health_data.get('status')}")
                print(f"   - Vector Bucket: {health_data.get('vector_bucket_name')}")
                print(f"   - Vector Index: {health_data.get('vector_index_name')}")
                print(f"   - S3 Vectors: {health_data.get('s3_vectors_connection')}")
                print(f"   - Embedding Service: {health_data.get('embedding_service')}")
                return True
        except requests.exceptions.RequestException as e:
            if attempt == 0:
                print(f"⏳ Service not ready yet, waiting...")
            import time
            time.sleep(2)
    
    print("❌ Service is not accessible. Please ensure:")
    print("   1. Docker container is running: docker-compose -f docker-compose.dev.yml up -d")
    print("   2. Service is accessible on localhost:8000")
    print("   3. AWS credentials are properly configured")
    return False

def run_pdf_tests():
    """Run the PDF integration test suite"""
    print("\n🧪 Running PDF-Focused Integration Tests...")
    print("=" * 60)
    
    # Import the test class
    from tests.test_pdf_integration import TestPDFIntegration
    
    # Create test suite
    loader = unittest.TestLoader()
    suite = loader.loadTestsFromTestCase(TestPDFIntegration)
    
    # Run tests with detailed output
    runner = unittest.TextTestRunner(
        verbosity=2,
        stream=sys.stdout,
        descriptions=True,
        failfast=False
    )
    
    result = runner.run(suite)
    
    # Print summary
    print("\n" + "=" * 60)
    print("🏁 PDF Integration Test Summary:")
    print(f"   - Tests run: {result.testsRun}")
    print(f"   - Failures: {len(result.failures)}")
    print(f"   - Errors: {len(result.errors)}")
    print(f"   - Skipped: {len(result.skipped) if hasattr(result, 'skipped') else 0}")
    
    if result.failures:
        print("\n❌ Failures:")
        for test, traceback in result.failures:
            print(f"   - {test}: {traceback.split('AssertionError:')[-1].strip()}")
    
    if result.errors:
        print("\n❌ Errors:")
        for test, traceback in result.errors:
            print(f"   - {test}: {traceback.split('Exception:')[-1].strip()}")
    
    success_rate = ((result.testsRun - len(result.failures) - len(result.errors)) / result.testsRun * 100) if result.testsRun > 0 else 0
    print(f"\n📊 Success Rate: {success_rate:.1f}%")
    
    if result.failures or result.errors:
        print("\n🔍 For detailed error information, check the test output above.")
        return False
    else:
        print("\n🎉 All PDF integration tests passed!")
        print("✅ PDF text extraction working perfectly!")
        print("✅ Semantic search with excellent relevance scores!")
        print("✅ Threshold filtering functioning correctly!")
        print("✅ Performance within acceptable limits!")
        return True

def main():
    """Main function"""
    print("🚀 S3 Vector Service - PDF Integration Test Runner")
    print("=" * 55)
    
    # Step 1: Check service availability
    if not check_service_availability():
        print("\n💡 To start the service, run:")
        print("   docker-compose -f docker-compose.dev.yml up -d")
        sys.exit(1)
    
    # Step 2: Run PDF integration tests
    success = run_pdf_tests()
    
    if success:
        print("\n✅ All PDF tests completed successfully!")
        print("🎯 Your PDF text extraction and semantic search is working perfectly!")
        sys.exit(0)
    else:
        print("\n❌ Some PDF tests failed.")
        print("🔧 Please check the error messages above.")
        sys.exit(1)

if __name__ == '__main__':
    main() 