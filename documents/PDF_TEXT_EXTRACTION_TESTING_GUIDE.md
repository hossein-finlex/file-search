# PDF Text Extraction Testing Guide

## Overview
This document provides testing commands to verify that PDF text extraction and semantic search functionality is working correctly.

## What We Implemented
- ✅ Added `pypdf>=3.0.0` library for PDF text extraction
- ✅ Updated `EmbeddingService` with PDF-specific text extraction
- ✅ Extensible architecture for different file types (text, image, PDF, generic)
- ✅ Docker container rebuilt with PDF support
- ✅ Real semantic search over PDF content (not just metadata)

## Prerequisites
- Docker service running: `docker-compose -f docker-compose.dev.yml up -d`
- Service healthy: `curl -s http://localhost:8000/health`

## Testing Commands

### 1. Check Service Health
```bash
curl -s http://localhost:8000/health
```
**Expected**: `"status":"healthy"` and `"embedding_service":true`

### 2. Verify PDF Content Extraction
```bash
docker exec s3vector-service-dev python -c "
from pypdf import PdfReader
with open('/app/tests/sample.pdf', 'rb') as f:
    reader = PdfReader(f)
    text = ''
    for page in reader.pages:
        text += page.extract_text()
    print('=== PDF TEXT CONTENT ===')
    print(repr(text))
    print(f'=== TOTAL LENGTH: {len(text)} characters ===')
"
```
**Expected**: Should show `'Dummy PDF file'` (14 characters)

### 3. Test PDF Text-Based Semantic Search

#### 3.1 Excellent Match - Search for "PDF file"
```bash
curl -X POST "http://localhost:8000/query" -H "Content-Type: application/json" -d '{"query_text": "PDF file", "top_k": 3}'
```
**Expected Similarity Score**: ~0.70+ (excellent match)

#### 3.2 Good Match - Search for "Dummy"
```bash
curl -X POST "http://localhost:8000/query" -H "Content-Type: application/json" -d '{"query_text": "Dummy", "top_k": 3}'
```
**Expected Similarity Score**: ~0.25+ (moderate match)

#### 3.3 Excellent Match - Search for "Dummy PDF file"
```bash
curl -X POST "http://localhost:8000/query" -H "Content-Type: application/json" -d '{"query_text": "Dummy PDF file", "top_k": 3}'
```
**Expected Similarity Score**: ~0.80+ (near-perfect match)

#### 3.4 Poor Match - Search for Unrelated Content
```bash
curl -X POST "http://localhost:8000/query" -H "Content-Type: application/json" -d '{"query_text": "pizza recipe cooking", "top_k": 3}'
```
**Expected Similarity Score**: ~0.10 (very poor match)

### 4. Test with Similarity Threshold

#### 4.1 Filter Out Poor Matches
```bash
curl -X POST "http://localhost:8000/query" -H "Content-Type: application/json" -d '{"query_text": "pizza recipe", "top_k": 3, "similarity_threshold": 0.3}'
```
**Expected**: Should return no results (empty results array)

#### 4.2 Include Good Matches Only
```bash
curl -X POST "http://localhost:8000/query" -H "Content-Type: application/json" -d '{"query_text": "PDF file", "top_k": 3, "similarity_threshold": 0.3}'
```
**Expected**: Should return the PDF file (similarity > 0.3)

### 5. Pretty-Formatted Output (with jq)

#### 5.1 Just Similarity Scores
```bash
curl -X POST "http://localhost:8000/query" -H "Content-Type: application/json" -d '{"query_text": "PDF file", "top_k": 3}' | jq '.results[0].similarity_score'
```

#### 5.2 File Names and Scores
```bash
curl -X POST "http://localhost:8000/query" -H "Content-Type: application/json" -d '{"query_text": "PDF file", "top_k": 3}' | jq '.results[] | {file_name: .file_info.file_name, score: .similarity_score}'
```

#### 5.3 Complete Clean Output
```bash
curl -X POST "http://localhost:8000/query" -H "Content-Type: application/json" -d '{"query_text": "PDF file", "top_k": 3}' | jq '{total_results, query_time_ms, results: [.results[] | {file_name: .file_info.file_name, similarity_score}]}'
```

## Expected Results Summary

| Search Term | Expected Score | Quality | Reason |
|-------------|---------------|---------|---------|
| "PDF file" | 0.70+ | Excellent | Exact phrase match from PDF content |
| "Dummy PDF file" | 0.80+ | Near-perfect | Complete content match |
| "Dummy" | 0.25+ | Moderate | Partial content match |
| "W3C" | 0.40+ | Good | Matches metadata |
| "sample" | 0.30+ | Good | Matches filename |
| "pizza recipe" | 0.10 | Poor | Completely unrelated |

## Troubleshooting

### PDF Not Found Error
```bash
# Check if PDF exists in container
docker exec s3vector-service-dev ls -la /app/tests/sample.pdf
```

### Service Not Responding
```bash
# Check service logs
docker-compose -f docker-compose.dev.yml logs --tail=20

# Restart service
docker-compose -f docker-compose.dev.yml restart
```

### No PDF Support Warning
```bash
# Check if pypdf is installed
docker exec s3vector-service-dev python -c "import pypdf; print('pypdf available')"
```

## Performance Expectations
- Query time: 100-2000ms (depending on model loading)
- PDF text extraction: Fast for small PDFs (<1MB)
- Memory usage: Acceptable for sentence-transformers model

## Validation Checklist
- [ ] Service health check passes
- [ ] PDF content extraction shows actual text
- [ ] "PDF file" search returns high similarity (>0.7)
- [ ] Unrelated searches return low similarity (<0.2)
- [ ] Similarity threshold filtering works
- [ ] Query responses exclude vector by default
- [ ] All commands copy-paste successfully

## Integration Tests

### Run Complete Integration Test Suite
```bash
# Run all integration tests including PDF tests
python tests/run_integration_tests.py
```

### Run Only PDF-Related Tests
```bash
# Run specific PDF tests
python -m unittest tests.test_integration.TestS3VectorIntegration.test_10_pdf_upload_and_text_extraction -v
python -m unittest tests.test_integration.TestS3VectorIntegration.test_11_pdf_content_semantic_search -v
python -m unittest tests.test_integration.TestS3VectorIntegration.test_12_pdf_vs_unrelated_content_search -v
python -m unittest tests.test_integration.TestS3VectorIntegration.test_13_pdf_similarity_threshold_filtering -v
```

### PDF Integration Test Coverage
- ✅ **test_10_pdf_upload_and_text_extraction**: Verifies PDF upload and text extraction
- ✅ **test_11_pdf_content_semantic_search**: Tests semantic search on actual PDF content
- ✅ **test_12_pdf_vs_unrelated_content_search**: Validates relevance scoring
- ✅ **test_13_pdf_similarity_threshold_filtering**: Tests threshold filtering

## File Structure Changes
- ✅ PDF moved to `tests/sample.pdf` for better organization
- ✅ Integration tests updated to include comprehensive PDF testing
- ✅ Docker configuration includes test directory
- ✅ All tests reference correct PDF path: `/app/tests/sample.pdf`

## Notes
- The sample PDF contains only "Dummy PDF file" text (14 characters)
- PDF file location: `tests/sample.pdf` (accessible as `/app/tests/sample.pdf` in container)
- Vector embeddings are 768-dimensional using `all-mpnet-base-v2` model
- S3 Vector index name is `test-bucket-index-2`
- Service runs on port 8000 in Docker container 