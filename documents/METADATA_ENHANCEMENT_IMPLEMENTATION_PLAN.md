# S3 Vector Service - Metadata Enhancement Implementation Plan

## Table of Contents
- [Overview](#overview)
- [Current State Assessment](#current-state-assessment)
- [Implementation Tasks](#implementation-tasks)
- [API Changes](#api-changes)
- [Testing Strategy](#testing-strategy)
- [Postman Collection Updates](#postman-collection-updates)
- [Definition of Done](#definition-of-done)

## Overview

This document outlines the implementation plan for enhancing metadata functionality in the S3 Vector Service. The goal is to provide comprehensive metadata support including saving metadata during upload, updating metadata for existing files, and utilizing metadata filters in query operations.

### Key Features to Implement
1. **Enhanced Metadata Query Filtering** - Expose existing backend metadata filtering capabilities through the API
2. **Comprehensive Testing** - Complete integration test coverage for metadata upload and query operations
3. **Documentation Updates** - Update Postman collection with metadata examples

## Current State Assessment

### ✅ Already Implemented
- **Upload with Metadata**: The service supports metadata during file upload via `FileUploadRequest.metadata`
- **Backend Metadata Filtering**: `S3VectorService.query_similar()` method supports `metadata_filter` parameter
- **Metadata Storage**: S3 Vectors service stores and retrieves metadata correctly
- **Basic Integration Tests**: Some metadata tests exist in `test_integration.py`

### ⚠️ Partially Implemented
- **API Metadata Filtering**: Backend supports it but not exposed in `/query` endpoint
- **Integration Tests**: Exist but need expansion for comprehensive coverage
- **Postman Collection**: Basic structure exists but lacks metadata examples

### ❌ Not Implemented
- **Advanced Metadata Filter Examples**: Complex filtering scenarios not documented in Postman collection



## Implementation Tasks

### Task 1: Update QueryRequest Model  
**File**: `app/models.py`
```python
class QueryRequest(BaseModel):
    """Request model for vector similarity query"""
    query_vector: Optional[List[float]] = Field(None, description="Query vector for similarity search")
    query_text: Optional[str] = Field(None, description="Query text to be embedded for similarity search")
    top_k: int = Field(default=10, ge=1, le=100, description="Number of top results to return")
    similarity_threshold: Optional[float] = Field(None, ge=0.0, le=1.0, description="Minimum similarity threshold")
    metadata_filter: Optional[Dict[str, Any]] = Field(None, description="Metadata filter for query results")
```

### Task 2: Update Query Endpoint
**File**: `app/main.py`
- Modify `/query` endpoint to accept and pass `metadata_filter` to the service

```python
@app.post("/query", response_model=QueryResponse)
async def query_similar(request: QueryRequest, include_vector: bool = False):
    # ... existing code ...
    
    # Perform similarity query with metadata filtering
    results = s3vector_service.query_similar(
        query_vector=query_vector,
        top_k=request.top_k,
        similarity_threshold=request.similarity_threshold,
        metadata_filter=request.metadata_filter  # NEW
    )
```

### Task 3: Expand Integration Tests
**File**: `tests/test_integration.py`

New test methods to add:
```python
def test_08_query_with_complex_metadata_filter(self):
    """Test complex metadata filtering with AND/OR operations"""

def test_09_query_with_range_metadata_filter(self):
    """Test metadata filtering with range operations ($gt, $lt, etc.)"""

def test_10_update_file_metadata(self):
    """Test updating metadata for existing file"""

def test_11_update_nonexistent_file_metadata(self):
    """Test error handling for updating non-existent file metadata"""

def test_12_invalid_metadata_filter(self):
    """Test error handling for invalid metadata filters"""

def test_13_metadata_filter_performance(self):
    """Test performance impact of metadata filtering"""
```

### Task 4: Update Postman Collection
**File**: `documents/S3_Vector_Service_Postman_Collection.json`

Add new requests:
1. **Query with Simple Metadata Filter**
2. **Query with Complex Metadata Filter (AND/OR)**  
3. **Query with Range Metadata Filter**
4. **Upload with Rich Metadata Examples**

## API Changes

### Enhanced Query Endpoint (Modified)
```http
POST /query
Content-Type: application/json

{
  "query_text": "search query",
  "top_k": 5,
  "metadata_filter": {
    "category": "technology",
    "priority": {"$gte": 3},
    "tags": {"$in": ["ai", "ml"]}
  }
}
```

### Metadata Filter Syntax

#### Supported Operators
```python
{
  # Equality
  "field": "value",
  "field": {"$eq": "value"},
  
  # Inequality
  "field": {"$ne": "value"},
  
  # Range
  "field": {"$gt": 100},
  "field": {"$gte": 100},
  "field": {"$lt": 500},
  "field": {"$lte": 500},
  
  # Array operations
  "field": {"$in": ["value1", "value2"]},
  "field": {"$nin": ["value1", "value2"]},
  
  # Logical operations
  "$and": [
    {"field1": "value1"},
    {"field2": {"$gt": 100}}
  ],
  "$or": [
    {"field1": "value1"},
    {"field2": "value2"}
  ]
}
```

## Testing Strategy

### Key Tests to Add
1. **Upload with Metadata** - Test file uploads with various metadata structures
2. **Query with Metadata Filters** - Test simple and complex metadata filtering
3. **Error Handling** - Test invalid metadata filter formats

### Test Data Examples
```python
# Simple metadata for uploads and queries
{"category": "technology", "priority": "high"}

# Complex metadata for testing filters
{
    "category": "technology", 
    "tags": ["ml", "nlp", "vector"],
    "priority": 5,
    "is_public": True,
    "created_date": "2024-01-15"
}

# Test filter examples
{"category": "technology"}
{"priority": {"$gte": 3}}
{"tags": {"$in": ["ml", "ai"]}}
```

## Postman Collection Updates

### New Request Categories

#### 1. 📊 Metadata Query Operations
- **Simple Metadata Filter**
- **Complex AND Filter**
- **Complex OR Filter**
- **Range Filter (Numbers)**
- **Range Filter (Dates)**
- **Array Operations (IN/NIN)**

#### 2. ✏️ Metadata Management
- **Update File Metadata**
- **Bulk Metadata Update**
- **Validate Metadata Format**

#### 3. ❌ Error Scenarios
- **Invalid Filter Syntax**
- **Update Non-existent File**
- **Large Metadata Object**

### Sample Postman Requests

#### Complex Metadata Filter Query
```json
{
  "name": "Query with Complex Metadata Filter",
  "request": {
    "method": "POST",
    "header": [{"key": "Content-Type", "value": "application/json"}],
    "url": "{{base_url}}/query",
    "body": {
      "raw": "{\n  \"query_text\": \"machine learning\",\n  \"top_k\": 10,\n  \"metadata_filter\": {\n    \"$and\": [\n      {\"category\": \"technology\"},\n      {\"priority\": {\"$gte\": 3}},\n      {\"tags\": {\"$in\": [\"ai\", \"ml\"]}}\n    ]\n  }\n}"
    }
  },
  "event": [
    {
      "listen": "test",
      "script": {
        "exec": [
          "pm.test('Status code is 200', function () {",
          "    pm.response.to.have.status(200);",
          "});",
          "",
          "pm.test('Results match metadata filter', function () {",
          "    const response = pm.response.json();",
          "    response.results.forEach(result => {",
          "        const metadata = result.file_info.metadata;",
          "        pm.expect(metadata.category).to.eql('technology');",
          "        pm.expect(metadata.priority).to.be.at.least(3);",
          "    });",
          "});"
        ]
      }
    }
  ]
}
```



## Definition of Done

### Core Requirements ✅
- [ ] Query endpoint accepts and processes `metadata_filter` parameter
- [ ] Integration tests for metadata upload and query operations
- [ ] Postman collection updated with metadata filter examples
- [ ] Backward compatibility maintained

### Optional Enhancements ✅
- [ ] Advanced metadata filter operators ($and, $or, $gt, etc.)
- [ ] Comprehensive error handling and validation

---

## Quick Implementation Guide

### Key Files to Modify
1. **`app/models.py`** - Add `metadata_filter` to `QueryRequest`
2. **`app/main.py`** - Update `/query` endpoint to pass `metadata_filter` to service
3. **`tests/test_integration.py`** - Add comprehensive metadata upload and query tests
4. **`documents/S3_Vector_Service_Postman_Collection.json`** - Add metadata filter examples

### Quick Test
```bash
# Run existing metadata test
python -m pytest tests/test_integration.py::TestS3VectorIntegration::test_07_query_with_metadata_filter -v
```

This focused plan implements metadata filtering in queries and comprehensive testing, building on the existing metadata upload functionality. 