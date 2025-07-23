#!/usr/bin/env python3
"""
Integration Test Runner for S3 Vector Service

This script runs comprehensive integration tests against the running S3 Vector service.
It tests all API endpoints and verifies the service is working correctly with real S3 Vectors.

Usage:
    python run_integration_tests.py

Prerequisites:
    - S3 Vector service running on localhost:8000
    - AWS S3 Vectors configured and accessible
    - Environment variables properly set
"""

import sys
import os
import unittest
import time
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
                print(f"   - Region: {health_data.get('region')}")
                return True
        except requests.exceptions.RequestException as e:
            if attempt == 0:
                print(f"⏳ Service not ready yet, waiting...")
            time.sleep(2)
    
    print("❌ Service is not accessible. Please ensure:")
    print("   1. Docker container is running")
    print("   2. Service is accessible on localhost:8000")
    print("   3. AWS credentials are properly configured")
    return False

def check_environment():
    """Check if required environment variables are set"""
    print("🔍 Checking environment configuration...")
    
    # Check for either profile-based or key-based authentication
    aws_profile = os.getenv('AWS_PROFILE')
    aws_access_key = os.getenv('AWS_ACCESS_KEY_ID')
    aws_secret_key = os.getenv('AWS_SECRET_ACCESS_KEY')
    
    # Required vars for both authentication methods
    required_vars = [
        'AWS_REGION',
        'S3_VECTOR_BUCKET_NAME',
        'S3_VECTOR_INDEX_NAME'
    ]
    
    missing_vars = []
    for var in required_vars:
        if not os.getenv(var):
            missing_vars.append(var)
    
    # Check AWS authentication method
    if not aws_profile and not (aws_access_key and aws_secret_key):
        missing_vars.extend(['AWS_PROFILE (or AWS_ACCESS_KEY_ID + AWS_SECRET_ACCESS_KEY)'])
    
    if missing_vars:
        print("❌ Missing required environment variables:")
        for var in missing_vars:
            print(f"   - {var}")
        print("\nPlease set these in your .env file")
        return False
    
    print("✅ Environment configuration looks good!")
    
    # Show configuration (safely)
    auth_method = f"Profile: {aws_profile}" if aws_profile else "Access Keys"
    print(f"   - AWS Authentication: {auth_method}")
    print(f"   - AWS Region: {os.getenv('AWS_REGION')}")
    print(f"   - Vector Bucket: {os.getenv('S3_VECTOR_BUCKET_NAME')}")
    print(f"   - Vector Index: {os.getenv('S3_VECTOR_INDEX_NAME')}")
    
    return True

def run_integration_tests():
    """Run the integration test suite"""
    print("\n🧪 Running Integration Tests...")
    print("=" * 60)
    
    # Import the test class
    from tests.test_integration import TestS3VectorIntegration
    
    # Create test suite
    loader = unittest.TestLoader()
    suite = loader.loadTestsFromTestCase(TestS3VectorIntegration)
    
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
    print("🏁 Integration Test Summary:")
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
        print("\n🎉 All integration tests passed!")
        return True

def main():
    """Main function"""
    print("🚀 S3 Vector Service Integration Test Runner")
    print("=" * 50)
    
    # Step 1: Check environment
    if not check_environment():
        sys.exit(1)
    
    # Step 2: Check service availability
    if not check_service_availability():
        print("\n💡 To start the service, run:")
        print("   docker-compose -f docker-compose.dev.yml up --build")
        sys.exit(1)
    
    # Step 3: Run integration tests
    success = run_integration_tests()
    
    if success:
        print("\n✅ All tests completed successfully!")
        print("🎯 Your S3 Vector service is working correctly with AWS S3 Vectors!")
        sys.exit(0)
    else:
        print("\n❌ Some tests failed.")
        print("🔧 Please check the error messages above and verify your AWS S3 Vectors setup.")
        sys.exit(1)

if __name__ == '__main__':
    main() 