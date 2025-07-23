# AWS S3 Vectors Migration Guide

## Overview

Your codebase has been updated to use the **real AWS S3 Vectors service** instead of a custom implementation. This is a major change that requires several setup steps and has some limitations due to the preview nature of S3 Vectors.

## Key Changes Made

### 1. **Service Architecture**
- **Before**: Custom vector storage using regular S3 buckets + manual similarity search
- **After**: Native AWS S3 Vectors service with dedicated vector buckets and indexes

### 2. **API Changes**
- **Before**: `boto3.client('s3')` with `put_object()` and `get_object()`
- **After**: `boto3.client('s3vectors')` with `put_vectors()` and `query_vectors()`

### 3. **Storage Model**
- **Before**: Files stored in `files/` prefix, vectors stored as JSON in `vectors/` prefix
- **After**: Vector buckets with vector indexes, native similarity search

### 4. **Configuration Changes**
- **Before**: `S3_BUCKET_NAME`
- **After**: `S3_VECTOR_BUCKET_NAME` and `S3_VECTOR_INDEX_NAME`

## Prerequisites for Running

### 1. **AWS S3 Vectors Preview Access**
- S3 Vectors is currently in **limited preview** (announced July 2025)
- You must have preview access granted by AWS
- Available only in 5 regions: `us-east-1`, `us-east-2`, `us-west-2`, `ap-southeast-2`, `eu-central-1`

### 2. **Updated Dependencies**
```bash
pip install boto3>=1.39.9 botocore>=1.39.9
```

### 3. **AWS Resources Setup**
You need to create:
1. **Vector Bucket** (not a regular S3 bucket)
2. **Vector Index** within the bucket
3. **IAM Permissions** for `s3vectors:*` actions

## Setup Instructions

### Step 1: Environment Configuration
```bash
cp env.example .env
```

Edit `.env` with:
```env
# AWS Configuration
AWS_ACCESS_KEY_ID=your_access_key_here
AWS_SECRET_ACCESS_KEY=your_secret_key_here
AWS_REGION=us-east-1

# S3 Vector Configuration
S3_VECTOR_BUCKET_NAME=your-vector-bucket-name
S3_VECTOR_INDEX_NAME=your-vector-index-name

# Vector Configuration
VECTOR_DIMENSION=384
EMBEDDING_MODEL=all-MiniLM-L6-v2
```

### Step 2: Create AWS Resources
You'll need to create these through AWS Console or CLI (specific APIs may vary):

1. **Create Vector Bucket**
   ```bash
   # This is a placeholder - actual CLI commands depend on AWS implementation
   aws s3vectors create-bucket --bucket-name your-vector-bucket-name --region us-east-1
   ```

2. **Create Vector Index**
   ```bash
   # This is a placeholder - actual CLI commands depend on AWS implementation
   aws s3vectors create-index --bucket-name your-vector-bucket-name --index-name your-vector-index-name
   ```

3. **Set IAM Permissions**
   ```json
   {
     "Version": "2012-10-17",
     "Statement": [
       {
         "Effect": "Allow",
         "Action": [
           "s3vectors:*"
         ],
         "Resource": "*"
       }
     ]
   }
   ```

### Step 3: Test the Service
```bash
# Install dependencies
pip install -r requirements.txt

# Run tests
python run_tests.py

# Start the service
python -m uvicorn app.main:app --reload

# Test with example
python example.py
```

## Current Limitations

### 1. **Preview Feature Limitations**
- Limited regional availability
- API may change during preview
- Some operations may not be fully implemented

### 2. **Known Issues in Current Implementation**
- `delete_file()` operation may not work (S3 Vectors delete API unclear)
- `list_files()` uses workaround (no native list API)
- Health checks are basic (limited S3 Vectors health APIs)

### 3. **Scalability Considerations**
- Sub-second query performance for large datasets
- Native vector indexing and optimization
- Cost optimized for vector storage

## Alternative Recommendations

If you can't access AWS S3 Vectors preview, consider these alternatives:

### Option 1: Use Dedicated Vector Database
- **Pinecone**: Managed vector database service
- **Weaviate**: Open-source vector database
- **Qdrant**: Lightweight vector database
- **PostgreSQL + pgvector**: Traditional database with vector extension

### Option 2: Keep Current Implementation (for development)
- The previous implementation will work for small-scale testing
- Good for prototyping and development
- Not recommended for production due to scalability issues

### Option 3: Use Amazon OpenSearch Serverless
- Native vector search capabilities
- Available now (not in preview)
- Good integration with AWS ecosystem

## Troubleshooting

### Common Issues

1. **"Module not found: s3vectors"**
   - Update boto3: `pip install boto3>=1.39.9`
   - Ensure you have AWS S3 Vectors preview access

2. **"Vector bucket not found"**
   - Create vector bucket through AWS Console
   - Verify bucket name in `.env` file
   - Check region availability

3. **"Access denied"**
   - Verify IAM permissions for `s3vectors:*`
   - Check AWS credentials configuration

4. **"Service unavailable"**
   - S3 Vectors may not be available in your region
   - Verify preview access is granted

## Migration Path for Existing Data

If you have existing data in the old format:

1. **Export existing vectors** from old S3 bucket
2. **Reprocess files** to generate new embeddings
3. **Upload to S3 Vectors** using new API
4. **Update client applications** to use new endpoints

## Testing Without S3 Vectors Access

For development without S3 Vectors access:

1. **Mock the service** using unit tests
2. **Use OpenSearch Serverless** as a substitute
3. **Implement local vector storage** for development

## Next Steps

1. **Apply for S3 Vectors preview access** through your AWS account team
2. **Set up vector bucket and index** in a supported region
3. **Test the updated implementation** with small datasets
4. **Monitor AWS documentation** for S3 Vectors updates and changes
5. **Plan production migration** once S3 Vectors becomes generally available

## Support

For issues related to:
- **S3 Vectors preview access**: Contact your AWS account team
- **API changes**: Monitor [AWS S3 Vectors documentation](https://docs.aws.amazon.com/AmazonS3/latest/userguide/s3-vectors.html)
- **Implementation bugs**: Check application logs and error messages

---

**Important**: This implementation is designed for the real AWS S3 Vectors service, which is currently in preview. The API calls and functionality may change as AWS finalizes the service. 