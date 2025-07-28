#!/bin/bash

# S3 Vector Service - Integration Test Runner
# Simple bash script to run integration tests with one command

set -e  # Exit on any error

echo "🚀 S3 Vector Service - Integration Test Runner"
echo "=============================================="

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "❌ Virtual environment not found!"
    echo "   Please create it first: python -m venv venv"
    exit 1
fi

# Check if service is running
echo "🔍 Checking if service is running..."
if ! curl -s http://localhost:8000/health > /dev/null; then
    echo "❌ Service is not running!"
    echo "   Please start it first: docker-compose -f docker-compose.dev.yml up"
    exit 1
fi

# Check service health
HEALTH_STATUS=$(curl -s http://localhost:8000/health | grep -o '"status":"[^"]*"' | cut -d'"' -f4)
if [ "$HEALTH_STATUS" != "healthy" ]; then
    echo "⚠️  Service is running but not healthy (status: $HEALTH_STATUS)"
    echo "   Proceeding with tests anyway..."
else
    echo "✅ Service is healthy and ready"
fi

# Activate virtual environment and run tests
echo ""
echo "🧪 Activating virtual environment and running tests..."
echo "====================================================="

# Source the virtual environment
source venv/bin/activate

# Run the integration tests
echo "Running integration tests..."
python -m unittest tests.test_integration.TestS3VectorIntegration -v

# Check if tests passed
if [ $? -eq 0 ]; then
    echo ""
    echo "🎉 All integration tests completed successfully!"
else
    echo ""
    echo "⚠️  Some tests failed or had issues (this may be expected for S3 Vector-only service)"
    echo "   Check the output above for details"
fi

echo ""
echo "📊 Test Summary:"
echo "   - Service Status: $HEALTH_STATUS"
echo "   - Test Runner: Python unittest"
echo "   - Virtual Environment: Activated"
echo ""
echo "💡 To run specific tests:"
echo "   source venv/bin/activate"
echo "   python -m unittest tests.test_integration.TestS3VectorIntegration.test_01_health_check -v"
echo ""
echo "📖 For manual testing, use the Postman collection:"
echo "   documents/S3_Vector_Service_Postman_Collection.json"

deactivate 2>/dev/null || true  # Deactivate virtual environment (ignore errors) 