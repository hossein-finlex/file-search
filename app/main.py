import os
import time
import logging
from typing import List, Optional
from fastapi import FastAPI, HTTPException, UploadFile, File, Form
from fastapi.responses import JSONResponse
from dotenv import load_dotenv

from .models import (
    FileUploadRequest, BatchUploadRequest, QueryRequest,
    UploadResponse, BatchUploadResponse, QueryResponse,
    FileResponse, ErrorResponse, HealthResponse
)
from .services.s3vector_service import S3VectorService
from .services.file_validation_service import FileValidationError

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="S3 Vector Service",
    description="A service for storing and querying files in AWS S3 Vector buckets",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Initialize S3 Vector service
s3vector_service = None


@app.on_event("startup")
async def startup_event():
    """Initialize the S3 Vector service on startup"""
    global s3vector_service
    try:
        s3vector_service = S3VectorService()
        logger.info("S3 Vector service initialized successfully")
    except Exception as e:
        logger.error(f"Failed to initialize S3 Vector service: {e}")
        raise


@app.get("/validation-config")
async def get_validation_config():
    """Get current file validation configuration"""
    try:
        if s3vector_service is None:
            raise HTTPException(status_code=503, detail="Service not initialized")
        
        return s3vector_service.file_validation_service.get_validation_config()
    except Exception as e:
        logger.error(f"Error getting validation config: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint"""
    try:
        if s3vector_service is None:
            return HealthResponse(
                status="unhealthy",
                s3_connection=False,
                s3_vectors_connection=False,
                embedding_service=False,
                vector_bucket_name=None,
                vector_index_name=None,
                error="Service not initialized"
            )
        
        health_info = s3vector_service.health_check()
        return HealthResponse(
            status=health_info['status'],
            s3_connection=health_info.get('s3_connection', False),
            s3_vectors_connection=health_info.get('s3_vectors_connection', False),
            embedding_service=health_info.get('embedding_service', False),
            vector_bucket_name=health_info.get('vector_bucket_name'),
            vector_index_name=health_info.get('vector_index_name'),
            version="1.0.0"
        )
    except Exception as e:
        return HealthResponse(
            status="unhealthy",
            s3_connection=False,
            s3_vectors_connection=False,
            embedding_service=False,
            vector_bucket_name=None,
            vector_index_name=None,
            error=str(e)
        )


@app.post("/upload", response_model=UploadResponse)
async def upload_file(request: FileUploadRequest):
    """Upload a single file with vector embedding"""
    try:
        if s3vector_service is None:
            raise HTTPException(status_code=503, detail="Service not initialized")
        
        start_time = time.time()
        
        # Upload file
        file_id = s3vector_service.upload_file(
            file_path=request.file_path,
            metadata=request.metadata,
            content_type=request.content_type
        )
        
        upload_time = (time.time() - start_time) * 1000  # Convert to milliseconds
        
        # Get file info for response
        file_info = s3vector_service.get_file_info(file_id)
        if not file_info:
            raise HTTPException(status_code=500, detail="Failed to retrieve file information")
        
        file_metadata = file_info['file_metadata']
        
        return UploadResponse(
            file_id=file_id,
            file_name=file_metadata.get('file_name', 'unknown'),
            file_size=file_metadata.get('file_size', 0),
            vector_dimension=file_info['vector_dimension'],
            upload_time_ms=upload_time,
            s3_key=f"files/{file_id}/{file_metadata.get('file_name', 'unknown')}"
        )
    
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="File not found")
    except FileValidationError as e:
        logger.warning(f"File validation failed: {e}")
        raise HTTPException(status_code=400, detail=f"File validation failed: {str(e)}")
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error uploading file: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@app.post("/upload-batch", response_model=BatchUploadResponse)
async def upload_batch(request: BatchUploadRequest):
    """Upload multiple files in batch"""
    try:
        if s3vector_service is None:
            raise HTTPException(status_code=503, detail="Service not initialized")
        
        # Prepare files list for batch upload
        files = []
        for file_request in request.files:
            files.append({
                'file_path': file_request.file_path,
                'metadata': file_request.metadata,
                'content_type': file_request.content_type
            })
        
        # Perform batch upload
        result = s3vector_service.upload_batch(files)
        
        # Convert to response format
        uploaded_files = []
        for file_result in result['uploaded_files']:
            file_info = s3vector_service.get_file_info(file_result['file_id'])
            if file_info:
                file_metadata = file_info['file_metadata']
                uploaded_files.append(UploadResponse(
                    file_id=file_result['file_id'],
                    file_name=file_metadata.get('file_name', 'unknown'),
                    file_size=file_metadata.get('file_size', 0),
                    vector_dimension=file_info['vector_dimension'],
                    upload_time_ms=0,  # Batch upload doesn't track individual times
                    s3_key=f"files/{file_result['file_id']}/{file_metadata.get('file_name', 'unknown')}"
                ))
        
        return BatchUploadResponse(
            uploaded_files=uploaded_files,
            failed_files=result['failed_files'],
            total_files=result['total_files'],
            success_count=result['success_count']
        )
    
    except FileValidationError as e:
        logger.warning(f"Batch file validation failed: {e}")
        raise HTTPException(status_code=400, detail=f"Batch validation failed: {str(e)}")
    except Exception as e:
        logger.error(f"Error in batch upload: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@app.post("/query", response_model=QueryResponse)
async def query_similar(request: QueryRequest, include_vector: bool = False):
    """Query for similar files using vector similarity search"""
    try:
        if s3vector_service is None:
            raise HTTPException(status_code=503, detail="Service not initialized")
        
        start_time = time.time()
        
        # Handle text query by embedding it to vector
        query_vector = request.query_vector
        if request.query_text is not None:
            logger.info(f"Embedding query text: {request.query_text}")
            query_vector = s3vector_service.embedding_service.generate_text_embedding(request.query_text)
        
        # Perform similarity query
        results = s3vector_service.query_similar(
            query_vector=query_vector,
            top_k=request.top_k,
            similarity_threshold=request.similarity_threshold
        )
        
        query_time = (time.time() - start_time) * 1000  # Convert to milliseconds
        
        # Convert results to response format
        query_results = []
        for result in results:
            file_metadata = result['file_metadata']
            query_results.append({
                'file_id': result['file_id'],
                'similarity_score': result['similarity_score'],
                'file_info': FileResponse(
                    file_id=result['file_id'],
                    file_name=file_metadata.get('file_name', 'unknown'),
                    file_size=file_metadata.get('file_size', 0),
                    content_type=file_metadata.get('content_type', 'application/octet-stream'),
                    metadata=file_metadata,
                    vector_dimension=result['vector_dimension'],
                    uploaded_at=file_metadata.get('uploaded_at', ''),
                    s3_key=f"files/{result['file_id']}/{file_metadata.get('file_name', 'unknown')}"
                )
            })
        
        return QueryResponse(
            query_vector=query_vector if include_vector else None,
            results=query_results,
            total_results=len(query_results),
            query_time_ms=query_time
        )
    
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error in similarity query: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@app.get("/files", response_model=List[FileResponse])
async def list_files(limit: int = 100):
    """List all files in the bucket"""
    try:
        if s3vector_service is None:
            raise HTTPException(status_code=503, detail="Service not initialized")
        
        files = s3vector_service.list_files(limit=limit)
        
        # Convert to response format
        file_responses = []
        for file_info in files:
            metadata = file_info['metadata']
            file_responses.append(FileResponse(
                file_id=file_info['file_id'],
                file_name=file_info['file_name'],
                file_size=file_info['file_size'],
                content_type=metadata.get('content_type', 'application/octet-stream'),
                metadata=metadata,
                vector_dimension=metadata.get('vector_dimension', 0),
                uploaded_at=metadata.get('uploaded_at', ''),
                s3_key=file_info.get('s3_key', f"files/{file_info['file_id']}/{file_info['file_name']}")
            ))
        
        return file_responses
    
    except Exception as e:
        logger.error(f"Error listing files: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@app.get("/files/{file_id}", response_model=FileResponse)
async def get_file_info(file_id: str):
    """Get information about a specific file"""
    try:
        if s3vector_service is None:
            raise HTTPException(status_code=503, detail="Service not initialized")
        
        file_info = s3vector_service.get_file_info(file_id)
        if not file_info:
            raise HTTPException(status_code=404, detail="File not found")
        
        file_metadata = file_info['file_metadata']
        
        return FileResponse(
            file_id=file_id,
            file_name=file_metadata.get('file_name', 'unknown'),
            file_size=file_metadata.get('file_size', 0),
            content_type=file_metadata.get('content_type', 'application/octet-stream'),
            metadata=file_metadata,
            vector_dimension=file_info['vector_dimension'],
            uploaded_at=file_metadata.get('uploaded_at', ''),
            s3_key=f"files/{file_id}/{file_metadata.get('file_name', 'unknown')}"
        )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting file info: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@app.delete("/files/{file_id}")
async def delete_file(file_id: str):
    """Delete a specific file and its vector embedding"""
    try:
        if s3vector_service is None:
            raise HTTPException(status_code=503, detail="Service not initialized")
        
        success = s3vector_service.delete_file(file_id)
        if not success:
            raise HTTPException(status_code=404, detail="File not found or could not be deleted")
        
        return {"message": f"File {file_id} deleted successfully"}
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting file: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    """Global exception handler"""
    logger.error(f"Unhandled exception: {exc}")
    return JSONResponse(
        status_code=500,
        content=ErrorResponse(
            error="Internal server error",
            details=str(exc)
        ).dict()
    )


if __name__ == "__main__":
    import uvicorn
    
    host = os.getenv("HOST", "0.0.0.0")
    port = int(os.getenv("PORT", "8000"))
    debug = os.getenv("DEBUG", "false").lower() == "true"
    
    uvicorn.run(
        "app.main:app",
        host=host,
        port=port,
        reload=debug,
        log_level="info"
    ) 