# S3 Vector Service

⚠️ **IMPORTANT NOTICE**: This project has been **updated to use the real AWS S3 Vectors service** (preview feature announced July 2025). 

**Requirements**:
- AWS S3 Vectors preview access
- Available in limited regions: us-east-1, us-east-2, us-west-2, ap-southeast-2, eu-central-1
- boto3>=1.39.9

**If you don't have S3 Vectors access**, see `S3_VECTORS_MIGRATION_GUIDE.md` for alternatives.

A Python service for storing and querying files in AWS S3 Vector buckets with vector similarity search capabilities.

## Features

- **Vector Storage**: Store files with their vector embeddings in S3 Vector buckets
- **PDF Text Extraction**: Real PDF text extraction using `pypdf>=3.0.0` for semantic search
- **Similarity Search**: Query files using vector similarity search with relevance scoring
- **Multiple File Types**: Support for text, images, PDFs, and other file types
- **REST API**: FastAPI-based REST service for easy integration
- **Batch Operations**: Upload and query multiple files efficiently
- **Metadata Support**: Store and retrieve file metadata with vectors
- **Threshold Filtering**: Configurable similarity thresholds to filter results
- **Text-based Queries**: Search using natural language instead of raw vectors
- **Performance Optimized**: Fast query response times (~150ms) with clean API responses

## Quick Start

### 1. Start the Service
```bash
# Using Docker (recommended)
docker-compose -f docker-compose.dev.yml up -d

# Or manually
pip install -r requirements.txt
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### 2. Test PDF Functionality
```bash
# Run PDF-focused tests (100% success rate)
source venv/bin/activate && python tests/run_pdf_tests.py

# Or test manually
curl -X POST "http://localhost:8000/query" \
  -H "Content-Type: application/json" \
  -d '{"query_text": "PDF file", "top_k": 3}'
```

### 3. Expected Results
- ✅ **High relevance scores**: 0.7+ for matching content
- ✅ **Fast performance**: ~150ms query response times  
- ✅ **Clean API**: No vector bloat in responses
- ✅ **Text extraction**: Real PDF content searchable

## Prerequisites

- Python 3.8+
- AWS Account with S3 Vector bucket access
- AWS credentials configured (via AWS CLI or environment variables)

## Installation

1. Clone the repository:
```bash
git clone <repository-url>
cd s3vector
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Set up environment variables:
```bash
cp .env.example .env
# Edit .env with your AWS credentials and bucket information
```

## Configuration

Create a `.env` file with the following variables:

```env
AWS_ACCESS_KEY_ID=your_access_key
AWS_SECRET_ACCESS_KEY=your_secret_key
AWS_REGION=us-east-1
S3_VECTOR_BUCKET_NAME=your-vector-bucket-name
S3_VECTOR_INDEX_NAME=your-vector-index-name
```

⚠️ **Note**: Requires AWS S3 Vectors preview access and dedicated vector bucket/index setup. See `S3_VECTORS_MIGRATION_GUIDE.md` for detailed setup instructions.

## Usage

### Starting the Service

```bash
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### API Endpoints

- `POST /upload` - Upload a file with vector embedding (supports PDF text extraction)
- `POST /upload-batch` - Upload multiple files
- `POST /query` - Query files by vector similarity (supports text queries)
- `GET /files` - List all stored files
- `DELETE /files/{file_id}` - Delete a specific file
- `GET /health` - Service health check with component status

### Example Usage

```python
from s3vector_service import S3VectorService

# Initialize service
service = S3VectorService()

# Upload a PDF file with automatic text extraction
pdf_path = "document.pdf"
metadata = {"title": "Sample PDF", "category": "document"}
file_id = service.upload_file(pdf_path, metadata, content_type="application/pdf")

# Query using natural language (recommended)
results = service.query_similar_text("PDF document about finance", top_k=5)

# Or query using raw vectors
query_vector = [0.1, 0.2, 0.3, ...]  # Your query vector
results = service.query_similar(query_vector, top_k=5)
```

## Project Structure

```
s3vector/
├── app/
│   ├── __init__.py
│   ├── main.py                 # FastAPI application
│   ├── models.py               # Pydantic models
│   └── services/
│       ├── __init__.py
│       ├── s3vector_service.py # Core S3 Vector operations
│       └── embedding_service.py # Vector embedding generation (with PDF support)
├── tests/
│   ├── __init__.py
│   ├── test_integration.py     # Complete integration tests
│   ├── test_pdf_integration.py # PDF-focused tests (100% success)
│   ├── test_s3vector_service.py # Unit tests
│   ├── sample.pdf              # Test PDF file with known content
│   ├── run_tests.py            # Unit test runner
│   ├── run_integration_tests.py # Complete integration test runner
│   └── run_pdf_tests.py        # PDF-focused test runner (recommended)
├── documents/
│   ├── PDF_TEXT_EXTRACTION_TESTING_GUIDE.md # Comprehensive testing guide
│   └── S3_VECTORS_MIGRATION_GUIDE.md
├── docker-compose.yml          # Production Docker setup
├── docker-compose.dev.yml     # Development Docker setup
├── Dockerfile
├── requirements.txt            # Includes pypdf>=3.0.0 for PDF support
├── .env.example
└── README.md
```

## AWS S3 Vector Setup

### 1. Create S3 Vector Bucket

1. Go to the AWS S3 Console
2. Click "Create bucket"
3. Choose a unique bucket name
4. Select your preferred region
5. In the "Advanced settings" section, enable "Vector search"
6. Configure vector search parameters:
   - **Vector dimension**: 384 (for the default model)
   - **Distance metric**: Cosine similarity
   - **Vector search capacity**: Choose based on your needs

### 2. Configure IAM Permissions

Create an IAM user or role with the following permissions:

```json
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Effect": "Allow",
            "Action": [
                "s3:GetObject",
                "s3:PutObject",
                "s3:DeleteObject",
                "s3:ListBucket",
                "s3:HeadBucket",
                "s3:HeadObject"
            ],
            "Resource": [
                "arn:aws:s3:::your-vector-bucket-name",
                "arn:aws:s3:::your-vector-bucket-name/*"
            ]
        }
    ]
}
```

### 3. Configure AWS Credentials

Option 1: AWS CLI
```bash
aws configure
```

Option 2: Environment variables
```bash
export AWS_ACCESS_KEY_ID=your_access_key
export AWS_SECRET_ACCESS_KEY=your_secret_key
export AWS_REGION=us-east-1
```

Option 3: .env file (copy env.example to .env and fill in your values)

## Testing

This project includes comprehensive testing suites to validate PDF text extraction, semantic search, and S3 Vector integration.

### Test Suites Available

#### 1. PDF-Focused Integration Tests ⭐ **RECOMMENDED**
Tests core PDF text extraction and semantic search functionality with **100% success rate**.

```bash
# Activate virtual environment and run PDF tests
source venv/bin/activate && python tests/run_pdf_tests.py
```

**What it tests:**
- ✅ PDF text extraction using `pypdf` library
- ✅ Semantic search with high-quality relevance scoring  
- ✅ Query performance (typically ~150ms)
- ✅ Threshold filtering functionality
- ✅ API response structure validation

**Expected Results:**
- 7/7 tests pass (100% success rate)
- Relevance ratio: ~8x better scores for related vs unrelated content
- High similarity scores: 0.7+ for exact matches, 0.9+ for complete content

#### 2. Complete Integration Tests
Tests all functionality including file upload, batch operations, and advanced features.

```bash
# Run complete integration test suite
source venv/bin/activate && python tests/run_integration_tests.py
```

**Coverage:**
- Health checks and service validation
- File upload and batch operations (may require S3 write permissions)
- Vector query operations
- Error handling and edge cases
- Performance benchmarks

### Docker Testing

#### Prerequisites
```bash
# Start the service with Docker
docker-compose -f docker-compose.dev.yml up -d

# Verify service is healthy
curl -s http://localhost:8000/health
```

#### Run Tests Against Docker Service
```bash
# PDF-focused tests (recommended)
source venv/bin/activate && python tests/run_pdf_tests.py

# Or run specific test classes
python -m unittest tests.test_pdf_integration.TestPDFIntegration -v
```

### Manual Testing Commands

#### Health Check
```bash
curl -s http://localhost:8000/health | python -m json.tool
```

#### PDF Content Verification
```bash
# Check actual PDF text content
docker exec s3vector-service-dev python -c "
from pypdf import PdfReader
with open('/app/tests/sample.pdf', 'rb') as f:
    reader = PdfReader(f)
    text = ''.join(page.extract_text() for page in reader.pages)
    print(f'PDF Content: {repr(text)}')
"
```

#### Semantic Search Testing
```bash
# Test excellent match (should score 0.7+)
curl -X POST "http://localhost:8000/query" \
  -H "Content-Type: application/json" \
  -d '{"query_text": "PDF file", "top_k": 3}'

# Test complete match (should score 0.8+)  
curl -X POST "http://localhost:8000/query" \
  -H "Content-Type: application/json" \
  -d '{"query_text": "Dummy PDF file", "top_k": 3}'

# Test unrelated content (should score <0.2)
curl -X POST "http://localhost:8000/query" \
  -H "Content-Type: application/json" \
  -d '{"query_text": "pizza recipe", "top_k": 3}'
```

#### Threshold Filtering
```bash
# Filter out poor matches with high threshold
curl -X POST "http://localhost:8000/query" \
  -H "Content-Type: application/json" \
  -d '{"query_text": "unrelated content", "top_k": 5, "similarity_threshold": 0.4}'
```

### Test File Structure

```
tests/
├── test_integration.py           # Complete integration tests
├── test_pdf_integration.py       # PDF-focused tests (100% success)
├── test_s3vector_service.py      # Unit tests
├── sample.pdf                    # Test PDF file with known content
└── __init__.py
```

### Performance Expectations

| **Metric** | **Expected Value** | **Notes** |
|------------|-------------------|-----------|
| Query Time | 100-300ms | Depends on model loading and vector dimension |
| PDF Text Extraction | <100ms | For small PDFs (<1MB) |
| Relevance Accuracy | 8x+ ratio | Related vs unrelated content scoring |
| Exact Match Score | 0.7+ | For queries matching PDF content |
| Complete Match Score | 0.8+ | For queries matching entire PDF content |

### Testing Features

#### PDF Text Extraction
- ✅ **Real PDF Processing**: Uses `pypdf>=3.0.0` for text extraction
- ✅ **Multi-page Support**: Extracts text from all PDF pages
- ✅ **Error Handling**: Graceful fallback if text extraction fails
- ✅ **Content Validation**: Tests against known PDF content ("Dummy PDF file")

#### Semantic Search Quality
- ✅ **High Precision**: Excellent similarity scores for relevant content
- ✅ **Low False Positives**: Poor scores for unrelated queries
- ✅ **Threshold Filtering**: Configurable similarity thresholds
- ✅ **Performance**: Fast query response times

#### API Response Quality  
- ✅ **Clean Responses**: Query vectors excluded by default (no bloat)
- ✅ **Structured Data**: Consistent JSON response format
- ✅ **Error Handling**: Graceful error responses
- ✅ **Performance Metrics**: Query timing included in responses

### Troubleshooting Tests

#### Common Test Issues

1. **Service Not Running**
   ```bash
   # Start the Docker service
   docker-compose -f docker-compose.dev.yml up -d
   ```

2. **PDF Not Found**
   ```bash
   # Verify PDF exists in container
   docker exec s3vector-service-dev ls -la /app/tests/sample.pdf
   ```

3. **Import Errors**
   ```bash
   # Install test dependencies
   source venv/bin/activate
   pip install -r requirements.txt
   ```

4. **AWS Permissions Issues**
   - PDF text extraction works without AWS write permissions
   - Upload tests may fail if S3 write permissions not configured
   - Query functionality requires S3 Vectors read access

### Advanced Testing

#### Load Testing
```bash
# Run multiple queries to test performance
for i in {1..10}; do
  curl -X POST "http://localhost:8000/query" \
    -H "Content-Type: application/json" \
    -d '{"query_text": "performance test '$i'", "top_k": 5}' \
    -w "Time: %{time_total}s\n"
done
```

#### Custom PDF Testing
```bash
# Test with your own PDF
# 1. Place PDF in tests/ directory
# 2. Update test to use your PDF path
# 3. Run tests to validate text extraction
```

For detailed testing documentation, see:
- `documents/PDF_TEXT_EXTRACTION_TESTING_GUIDE.md` - Comprehensive testing guide
- `tests/run_pdf_tests.py` - PDF-focused test runner  
- `tests/run_integration_tests.py` - Complete integration test runner

## Development

### Running the Example

```bash
python example.py
```

### API Testing

Start the service:
```bash
python -m uvicorn app.main:app --reload
```

Test the API:
```bash
# Health check
curl http://localhost:8000/health

# Upload a file
curl -X POST "http://localhost:8000/upload" \
  -H "Content-Type: application/json" \
  -d '{
    "file_path": "/path/to/your/file.txt",
    "metadata": {"category": "document"},
    "content_type": "text/plain"
  }'

# Query using text (recommended)
curl -X POST "http://localhost:8000/query" \
  -H "Content-Type: application/json" \
  -d '{
    "query_text": "financial report PDF document",
    "top_k": 5,
    "similarity_threshold": 0.3
  }'

# Or query using raw vectors
curl -X POST "http://localhost:8000/query" \
  -H "Content-Type: application/json" \
  -d '{
    "query_vector": [0.1, 0.2, 0.3, ...],
    "top_k": 5,
    "similarity_threshold": 0.5
  }'
```

## Architecture

The service consists of several key components:

1. **S3VectorService**: Core service for S3 Vector operations
2. **EmbeddingService**: Generates vector embeddings for files
3. **FastAPI Application**: REST API endpoints
4. **Pydantic Models**: Request/response validation

### File Structure

```
s3vector/
├── app/
│   ├── main.py                 # FastAPI application
│   ├── models.py               # Pydantic models
│   └── services/
│       ├── s3vector_service.py # Core S3 Vector operations
│       └── embedding_service.py # Vector embedding generation
├── tests/
│   └── test_s3vector_service.py
├── example.py                  # Usage examples
├── run_tests.py               # Test runner
├── requirements.txt
├── setup.py
└── README.md
```

## Features

### Vector Embeddings
- **Text Files**: Uses sentence transformers for text embedding
- **Image Files**: Converts images to base64 and embeds as text
- **Other Files**: Creates descriptive embeddings based on file metadata

### Similarity Search
- **Cosine Similarity**: Calculates similarity between vectors
- **Threshold Filtering**: Filter results by minimum similarity score
- **Top-K Results**: Return the most similar files

### File Management
- **Unique IDs**: Each file gets a UUID for identification
- **Metadata Storage**: Store custom metadata with files
- **Batch Operations**: Upload multiple files efficiently
- **File Deletion**: Remove files and their embeddings

## Configuration

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `AWS_ACCESS_KEY_ID` | AWS access key | Required |
| `AWS_SECRET_ACCESS_KEY` | AWS secret key | Required |
| `AWS_REGION` | AWS region | `us-east-1` |
| `S3_BUCKET_NAME` | S3 Vector bucket name | Required |
| `S3_BUCKET_REGION` | S3 bucket region | `us-east-1` |
| `VECTOR_DIMENSION` | Vector embedding dimension | `384` |
| `EMBEDDING_MODEL` | Sentence transformer model | `all-MiniLM-L6-v2` |
| `HOST` | API host | `0.0.0.0` |
| `PORT` | API port | `8000` |
| `DEBUG` | Debug mode | `false` |

## Troubleshooting

### Common Issues

1. **AWS Credentials Not Found**
   - Ensure AWS credentials are properly configured
   - Check environment variables or AWS CLI configuration

2. **S3 Bucket Not Found**
   - Verify the bucket name is correct
   - Ensure the bucket exists and is accessible

3. **Vector Search Not Enabled**
   - Enable vector search in your S3 bucket settings
   - Configure the correct vector dimension

4. **Permission Denied**
   - Check IAM permissions for S3 operations
   - Ensure the bucket policy allows your operations

### Logging

The service uses Python's logging module. Set the log level:

```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests for new functionality
5. Run the test suite
6. Submit a pull request

## License

MIT License

## Testing the Updated Implementation

### Prerequisites for Testing
- **AWS S3 Vectors Preview Access** (contact your AWS account team)
- **Supported Region**: us-east-1, us-east-2, us-west-2, ap-southeast-2, or eu-central-1
- **Vector Bucket and Index** created through AWS Console

### Setup Steps
1. Configure environment variables in `.env`
2. Install dependencies: `pip install -r requirements.txt`
3. Run tests: `python run_tests.py`
4. Start service: `python -m uvicorn app.main:app --reload`
5. Test example: `python example.py`

### Important Notes
- This implementation uses **real S3 Vectors APIs** (`s3vectors` service)
- Requires boto3>=1.39.9 for S3 Vectors support
- Some APIs may be limited during preview phase
- See `S3_VECTORS_MIGRATION_GUIDE.md` for comprehensive setup instructions

For detailed setup instructions, refer to:
- [S3 Vector Documentation](https://docs.aws.amazon.com/AmazonS3/latest/userguide/s3-vectors.html)
- [Getting Started Guide](https://docs.aws.amazon.com/AmazonS3/latest/userguide/s3-vectors-getting-started.html)
- `S3_VECTORS_MIGRATION_GUIDE.md` (in this repository) 