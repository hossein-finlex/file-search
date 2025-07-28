from pydantic import BaseModel, Field
from typing import List, Dict, Optional, Any
from datetime import datetime
import uuid


class FileUploadRequest(BaseModel):
    """Request model for file upload with metadata"""
    file_path: str = Field(..., description="Path to the file to upload")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="File metadata")
    content_type: Optional[str] = Field(None, description="Content type of the file")


class BatchUploadRequest(BaseModel):
    """Request model for batch file upload"""
    files: List[FileUploadRequest] = Field(..., description="List of files to upload")


class QueryRequest(BaseModel):
    """Request model for vector similarity query"""
    query_vector: Optional[List[float]] = Field(None, description="Query vector for similarity search")
    query_text: Optional[str] = Field(None, description="Query text to be embedded for similarity search")
    top_k: int = Field(default=10, ge=1, le=100, description="Number of top results to return")
    similarity_threshold: Optional[float] = Field(None, ge=0.0, le=1.0, description="Minimum similarity threshold")
    metadata_filter: Optional[Dict[str, Any]] = Field(None, description="Metadata filter for query results")
    
    @classmethod
    def model_validate(cls, data):
        """Validate that either query_vector or query_text is provided, but not both"""
        if isinstance(data, dict):
            query_vector = data.get('query_vector')
            query_text = data.get('query_text')
            
            if query_vector is not None and query_text is not None:
                raise ValueError("Provide either query_vector or query_text, not both")
            if query_vector is None and query_text is None:
                raise ValueError("Either query_vector or query_text must be provided")
        
        return super().model_validate(data)


class FileResponse(BaseModel):
    """Response model for file information"""
    file_id: str = Field(..., description="Unique file identifier")
    file_name: str = Field(..., description="Original file name")
    file_size: int = Field(..., description="File size in bytes")
    content_type: str = Field(..., description="File content type")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="File metadata")
    vector_dimension: int = Field(..., description="Vector dimension")
    uploaded_at: datetime = Field(..., description="Upload timestamp")
    s3_key: str = Field(..., description="S3 object key")


class QueryResult(BaseModel):
    """Response model for query results"""
    file_id: str = Field(..., description="File identifier")
    similarity_score: float = Field(..., description="Similarity score")
    file_info: FileResponse = Field(..., description="File information")


class QueryResponse(BaseModel):
    """Response model for similarity query"""
    query_vector: Optional[List[float]] = Field(None, description="Query vector used (optional)")
    results: List[QueryResult] = Field(..., description="Query results")
    total_results: int = Field(..., description="Total number of results")
    query_time_ms: float = Field(..., description="Query execution time in milliseconds")


class UploadResponse(BaseModel):
    """Response model for file upload"""
    file_id: str = Field(..., description="Unique file identifier")
    file_name: str = Field(..., description="Original file name")
    file_size: int = Field(..., description="File size in bytes")
    vector_dimension: int = Field(..., description="Vector dimension")
    upload_time_ms: float = Field(..., description="Upload time in milliseconds")
    s3_key: str = Field(..., description="S3 object key")


class BatchUploadResponse(BaseModel):
    """Response model for batch upload"""
    uploaded_files: List[UploadResponse] = Field(..., description="Successfully uploaded files")
    failed_files: List[Dict[str, Any]] = Field(default_factory=list, description="Failed uploads with error details")
    total_files: int = Field(..., description="Total number of files processed")
    success_count: int = Field(..., description="Number of successfully uploaded files")


class ErrorResponse(BaseModel):
    """Error response model"""
    error: str = Field(..., description="Error message")
    details: Optional[str] = Field(None, description="Additional error details")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Error timestamp")


class HealthResponse(BaseModel):
    """Health check response model"""
    status: str = Field(..., description="Service status")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Health check timestamp")
    version: str = Field(default="1.0.0", description="Service version")
    s3_connection: bool = Field(..., description="S3 connection status")
    s3_vectors_connection: Optional[bool] = Field(None, description="S3 Vectors connection status")
    embedding_service: Optional[bool] = Field(None, description="Embedding service status")
    vector_bucket_name: Optional[str] = Field(None, description="Vector bucket name")
    vector_index_name: Optional[str] = Field(None, description="Vector index name")
    error: Optional[str] = Field(None, description="Error message if unhealthy") 