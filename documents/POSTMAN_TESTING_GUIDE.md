# S3 Vector Service - Postman Testing Guide

## 📋 Overview

This guide shows you how to use the Postman collection to manually test all S3 Vector service endpoints. The collection includes automated tests, environment variables, and comprehensive examples.

## 🚀 Quick Setup

### 1. Import the Collection
1. Open Postman
2. Click **Import** → **File** → Select `S3_Vector_Service_Postman_Collection.json`
3. The collection will appear in your workspace

### 2. Environment Setup (Optional)
The collection includes default variables, but you can customize:

- **base_url**: Default `http://localhost:8000` (change if running on different host/port)
- **sample_file_id**: Auto-populated by "List All Files" request
- **last_uploaded_file_id**: Auto-populated by upload requests
- **file_id_to_delete**: Set manually for deletion tests

## 📁 Collection Structure

### 🏥 Health & Configuration
- **Health Check**: Basic service status with automated validation
- **Service Configuration**: Complete service config (non-sensitive)
- **Validation Configuration**: File validation rules

### 📁 File Management  
- **List All Files**: Get all files with auto-population of file IDs
- **List Files with Limit**: Paginated file listing
- **Get File Info**: Retrieve specific file details
- **Delete File**: Remove file and vector embedding

### 📤 File Upload
- **Upload File (Multipart)**: Recommended for real files
- **Upload File (JSON)**: For container-accessible files
- **Batch Upload**: Upload multiple files at once

### 🔍 Similarity Search
- **Search by Text Query**: Natural language similarity search
- **Search with High Threshold**: Find only very similar content
- **Search with Vector Include**: Debug mode with query vector
- **Search by Vector**: Advanced direct vector search

### 🧪 Error Testing
- **Upload Non-existent File**: Error handling validation
- **Get Non-existent File**: 404 error testing
- **Query with Invalid Parameters**: Validation testing

## ⚡ Recommended Testing Workflow

### Phase 1: Health Check
```
1. Run "Health Check" first
   ✅ Verify status: "healthy"
   ✅ Verify s3_connection: true
   ✅ Verify embedding_service: true
```

### Phase 2: Explore Existing Data
```
2. Run "List All Files"
   📝 Note: This auto-populates sample_file_id variable
   
3. Run "Get File Info" 
   📝 Uses the auto-populated file ID
   
4. Run "Search by Text Query"
   📝 Test similarity search with existing content
```

### Phase 3: Upload Testing
```
5. Run "Upload File (Multipart)"
   📎 Select a test file (PDF, TXT, or image)
   📝 Note: Auto-populates last_uploaded_file_id
   
6. Run "Search by Text Query" again
   🔍 Search for content related to your uploaded file
```

### Phase 4: Advanced Testing
```
7. Run "Batch Upload"
8. Run "Search with High Threshold"
9. Test error scenarios in "Error Testing" folder
```

## 🔧 Customization Tips

### Upload File Testing
For **Upload File (Multipart)**:
1. Click on the request
2. Go to **Body** → **form-data**
3. Click **Select Files** next to the "file" field
4. Choose your test file
5. Optionally modify the metadata JSON

### Metadata Examples
```json
{
  "category": "manual_test",
  "author": "your_name", 
  "project": "s3_vector_testing",
  "priority": "high",
  "tags": ["test", "postman", "manual"]
}
```

### Search Query Examples
Try different search texts:
- `"sample document"`
- `"test file content"`
- `"technical documentation"`
- `"image processing"`

## 🧪 Test Automation Features

### Built-in Test Scripts
Each request includes automated tests:

**Health Check Tests:**
- ✅ Status code is 200
- ✅ Service is healthy  
- ✅ S3 connection working

**Upload Tests:**
- ✅ Status code is 200
- ✅ Response has file_id
- ✅ Vector dimension is 768

**Search Tests:**
- ✅ Response has results array
- ✅ Results have similarity scores
- ✅ Query time is reported

### Variable Auto-Population
Smart variable management:
- File IDs auto-captured for reuse
- Environment variables shared across requests
- No manual copy-pasting needed

## 📊 Understanding Responses

### Health Check Response
```json
{
  "status": "healthy",
  "s3_connection": true,
  "s3_vectors_connection": true,
  "embedding_service": true,
  "vector_bucket_name": "test-bucket",
  "vector_index_name": "test-bucket-index-2"
}
```

### Upload Response
```json
{
  "file_id": "uuid-string",
  "file_name": "your-file.txt",
  "file_size": 1234,
  "vector_dimension": 768,
  "upload_time_ms": 156.78,
  "s3_key": "files/uuid/your-file.txt"
}
```

### Search Response
```json
{
  "results": [
    {
      "file_id": "uuid-string",
      "similarity_score": 0.87,
      "file_info": {
        "file_name": "similar-file.txt",
        "content_type": "text/plain",
        "metadata": {...}
      }
    }
  ],
  "total_results": 5,
  "query_time_ms": 23.45
}
```

## 🚨 Common Issues & Solutions

### Issue: Upload Fails with 422 Error
**Solution**: Check file path in JSON upload or ensure file is selected in multipart upload

### Issue: Search Returns No Results  
**Solution**: 
- Lower similarity_threshold (try 0.1 or 0.0)
- Try broader search terms
- Ensure files are uploaded first

### Issue: Get File Info Returns 404
**Solution**: 
- Run "List All Files" first to populate sample_file_id
- Copy a valid file_id from the list response

### Issue: Health Check Shows s3_connection: false
**Solution**: 
- Check if service is running: `docker-compose ps`
- Verify AWS credentials are configured
- Check service logs: `docker-compose logs`

## 🎯 Testing Scenarios

### Scenario 1: Document Upload & Search
1. Upload a text document
2. Search for keywords from the document  
3. Verify the uploaded document appears in results
4. Check similarity scores are reasonable (>0.3)

### Scenario 2: Batch Processing
1. Run batch upload with multiple files
2. Verify all files appear in file list
3. Run searches for different content types

### Scenario 3: Error Handling
1. Try uploading non-existent file
2. Search with invalid parameters
3. Access non-existent file ID
4. Verify proper error responses

## 📈 Performance Testing

Monitor these metrics:
- **Upload Time**: Typically 100-500ms for small files
- **Query Time**: Usually <50ms for text queries  
- **Health Check**: Should be <10ms
- **File List**: Varies by number of files

## 🔍 Debugging Tips

1. **Check Test Results Tab**: See which automated tests pass/fail
2. **View Console**: Check environment variable updates
3. **Inspect Response**: Look at headers and status codes
4. **Check Service Logs**: `docker-compose logs -f` for real-time debugging

## 📝 Advanced Usage

### Running Collection Tests
1. Click collection name → **Run**
2. Select requests to run
3. View automated test results
4. Export test reports

### Environment Management
1. Create separate environments for dev/staging/prod
2. Set different base_url values
3. Share environments with team

### Custom Scripts
Add your own test scripts in the **Tests** tab:
```javascript
pm.test("Custom validation", function () {
    var jsonData = pm.response.json();
    pm.expect(jsonData.custom_field).to.exist;
});
```

---

Happy Testing! 🚀

For questions or issues, check the service logs or API documentation at `http://localhost:8000/docs`. 