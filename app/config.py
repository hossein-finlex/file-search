"""
Centralized configuration management for S3 Vector Service.

This module handles all configuration values, environment variables,
and provides type-safe access to application settings.
"""

import os
import logging
from typing import List, Set, Optional, Dict, Any, Union
from pathlib import Path
from pydantic import Field, validator
from pydantic_settings import BaseSettings
from enum import Enum

logger = logging.getLogger(__name__)


class LogLevel(str, Enum):
    """Logging levels enum"""
    CRITICAL = "CRITICAL"
    ERROR = "ERROR"
    WARNING = "WARNING"
    INFO = "INFO"
    DEBUG = "DEBUG"


class AWSRegion(str, Enum):
    """Supported AWS regions for S3 Vectors"""
    US_EAST_1 = "us-east-1"
    US_EAST_2 = "us-east-2"
    US_WEST_2 = "us-west-2"
    AP_SOUTHEAST_2 = "ap-southeast-2"
    EU_CENTRAL_1 = "eu-central-1"


class EmbeddingModel(str, Enum):
    """Supported embedding models"""
    ALL_MINILM_L6_V2 = "all-MiniLM-L6-v2"
    ALL_MPNET_BASE_V2 = "all-mpnet-base-v2"
    PARAPHRASE_MINILM_L3_V2 = "paraphrase-MiniLM-L3-v2"


class ServerConfig(BaseSettings):
    """Server configuration settings"""
    
    # Server settings
    host: str = Field(default="0.0.0.0", description="Server host address")
    port: int = Field(default=8000, ge=1, le=65535, description="Server port")
    debug: bool = Field(default=False, description="Debug mode")
    log_level: LogLevel = Field(default=LogLevel.INFO, description="Logging level")
    
    # API settings
    api_title: str = Field(default="S3 Vector Service", description="API title")
    api_version: str = Field(default="1.0.0", description="API version")
    docs_url: str = Field(default="/docs", description="API documentation URL")
    redoc_url: str = Field(default="/redoc", description="ReDoc documentation URL")
    
    class Config:
        env_prefix = ""
        case_sensitive = False


class AWSConfig(BaseSettings):
    """AWS configuration settings"""
    
    # AWS credentials
    aws_access_key_id: Optional[str] = Field(default=None, description="AWS Access Key ID")
    aws_secret_access_key: Optional[str] = Field(default=None, description="AWS Secret Access Key")
    aws_region: AWSRegion = Field(default=AWSRegion.US_EAST_1, description="AWS region")
    aws_profile: Optional[str] = Field(default=None, description="AWS profile name")
    
    # S3 Vector settings
    s3_vector_bucket_name: str = Field(..., description="S3 Vector bucket name")
    s3_vector_index_name: str = Field(default="default-index", description="Vector index name")
    s3_bucket_region: Optional[AWSRegion] = Field(default=None, description="S3 bucket region override")
    
    @validator('s3_bucket_region', pre=True, always=True)
    def set_bucket_region(cls, v, values):
        """Set bucket region to AWS region if not specified"""
        return v or values.get('aws_region')
    
    class Config:
        env_prefix = ""
        case_sensitive = False


class VectorConfig(BaseSettings):
    """Vector processing configuration"""
    
    # Vector settings
    vector_dimension: int = Field(default=768, ge=1, le=4096, description="Vector embedding dimension")
    embedding_model: EmbeddingModel = Field(default=EmbeddingModel.ALL_MPNET_BASE_V2, description="Embedding model")
    
    # Text processing
    max_text_length: int = Field(default=512, ge=1, le=8192, description="Maximum text length for processing")
    text_truncation_strategy: str = Field(default="end", pattern="^(start|end|middle)$", description="Text truncation strategy")
    
    # Image processing
    image_resize_width: int = Field(default=224, ge=32, le=1024, description="Image resize width")
    image_resize_height: int = Field(default=224, ge=32, le=1024, description="Image resize height")
    image_format: str = Field(default="JPEG", pattern="^(JPEG|PNG|RGB)$", description="Image processing format")
    
    # Query defaults (AWS S3 Vectors limits: topK must be 1-30)
    default_top_k: int = Field(default=10, ge=1, le=30, description="Default number of results to return")
    max_top_k: int = Field(default=30, ge=1, le=30, description="Maximum number of results allowed (AWS S3 Vectors limit)")
    default_similarity_threshold: float = Field(default=0.0, ge=0.0, le=1.0, description="Default similarity threshold")
    
    # API limits (AWS S3 Vectors limits: topK must be 1-30)
    max_list_limit: int = Field(default=30, ge=1, le=30, description="Maximum list API limit (AWS S3 Vectors limit)")
    default_list_limit: int = Field(default=10, ge=1, le=30, description="Default list limit")
    
    class Config:
        env_prefix = ""
        case_sensitive = False


class FileValidationConfig(BaseSettings):
    """File validation configuration"""
    
    # Size limits (in MB)
    max_file_size_mb: int = Field(default=50, ge=1, le=1000, description="Maximum file size in MB")
    max_batch_size_mb: int = Field(default=200, ge=1, le=5000, description="Maximum batch size in MB")
    
    # File types
    allowed_file_types: str = Field(
        default="text/*,application/pdf,image/*",
        description="Comma-separated list of allowed MIME types"
    )
    blocked_file_extensions: str = Field(
        default=".exe,.bat,.cmd,.scr,.com,.pif,.dll,.sys",
        description="Comma-separated list of blocked file extensions"
    )
    
    # Processing
    allow_empty_files: bool = Field(default=False, description="Allow empty files")
    strict_mime_type_checking: bool = Field(default=True, description="Strict MIME type validation")
    
    @property
    def max_file_size_bytes(self) -> int:
        """Get max file size in bytes"""
        return self.max_file_size_mb * 1024 * 1024
    
    @property
    def max_batch_size_bytes(self) -> int:
        """Get max batch size in bytes"""
        return self.max_batch_size_mb * 1024 * 1024
    
    @property
    def allowed_mime_types_set(self) -> Set[str]:
        """Get allowed MIME types as a set"""
        return {mime_type.strip().lower() for mime_type in self.allowed_file_types.split(',') if mime_type.strip()}
    
    @property
    def blocked_extensions_set(self) -> Set[str]:
        """Get blocked extensions as a set"""
        extensions = set()
        for ext in self.blocked_file_extensions.split(','):
            ext = ext.strip().lower()
            if ext and not ext.startswith('.'):
                ext = '.' + ext
            if ext:
                extensions.add(ext)
        return extensions
    
    class Config:
        env_prefix = ""
        case_sensitive = False


class PerformanceConfig(BaseSettings):
    """Performance and optimization configuration"""
    
    # Timeouts (in seconds)
    request_timeout: int = Field(default=30, ge=1, le=300, description="Request timeout in seconds")
    upload_timeout: int = Field(default=300, ge=1, le=3600, description="Upload timeout in seconds")
    query_timeout: int = Field(default=60, ge=1, le=300, description="Query timeout in seconds")
    
    # Concurrency
    max_concurrent_uploads: int = Field(default=10, ge=1, le=100, description="Maximum concurrent uploads")
    max_concurrent_queries: int = Field(default=50, ge=1, le=500, description="Maximum concurrent queries")
    
    # Caching
    enable_embedding_cache: bool = Field(default=False, description="Enable embedding caching")
    cache_ttl_seconds: int = Field(default=3600, ge=60, le=86400, description="Cache TTL in seconds")
    max_cache_size: int = Field(default=1000, ge=10, le=10000, description="Maximum cache entries")
    
    # Retry settings
    max_retries: int = Field(default=3, ge=0, le=10, description="Maximum retry attempts")
    retry_delay_seconds: float = Field(default=1.0, ge=0.1, le=60.0, description="Retry delay in seconds")
    exponential_backoff: bool = Field(default=True, description="Use exponential backoff for retries")
    
    class Config:
        env_prefix = ""
        case_sensitive = False


class S3VectorConfig:
    """Main configuration class that combines all configuration sections"""
    
    def __init__(self, env_file: Optional[str] = None):
        """Initialize configuration from environment variables and optional .env file"""
        self._load_environment(env_file)
        
        # Initialize configuration sections
        self.server = ServerConfig()
        self.aws = AWSConfig()
        self.vector = VectorConfig()
        self.file_validation = FileValidationConfig()
        self.performance = PerformanceConfig()
        
        # Log configuration summary
        self._log_config_summary()
    
    def _load_environment(self, env_file: Optional[str] = None):
        """Load environment variables from .env file if available"""
        if env_file and Path(env_file).exists():
            from dotenv import load_dotenv
            load_dotenv(env_file)
            logger.info(f"Loaded environment from {env_file}")
        elif Path(".env").exists():
            from dotenv import load_dotenv
            load_dotenv()
            logger.info("Loaded environment from .env")
    
    def _log_config_summary(self):
        """Log configuration summary (without sensitive data)"""
        logger.info("Configuration loaded:")
        logger.info(f"  Server: {self.server.host}:{self.server.port} (debug={self.server.debug})")
        logger.info(f"  AWS Region: {self.aws.aws_region}")
        logger.info(f"  Vector Model: {self.vector.embedding_model} (dim={self.vector.vector_dimension})")
        logger.info(f"  File Limits: {self.file_validation.max_file_size_mb}MB individual, {self.file_validation.max_batch_size_mb}MB batch")
        logger.info(f"  Performance: {self.performance.max_concurrent_uploads} uploads, {self.performance.max_concurrent_queries} queries")
    
    def get_dummy_vector(self) -> List[float]:
        """Get a dummy vector with the configured dimension for health checks"""
        import random
        # Generate a normalized random vector instead of zeros
        # This is more likely to be accepted by S3 Vectors index
        vector = [random.gauss(0, 0.1) for _ in range(self.vector.vector_dimension)]
        # Normalize the vector
        magnitude = sum(x*x for x in vector) ** 0.5
        if magnitude > 0:
            vector = [x/magnitude for x in vector]
        return vector
    
    def validate_configuration(self) -> List[str]:
        """Validate configuration and return list of warnings/errors"""
        warnings = []
        
        # Check required AWS settings
        if not self.aws.s3_vector_bucket_name:
            warnings.append("S3_VECTOR_BUCKET_NAME is required")
        
        # Check if AWS credentials are available
        if not self.aws.aws_access_key_id and not self.aws.aws_profile and not os.getenv('AWS_CONTAINER_CREDENTIALS_RELATIVE_URI'):
            warnings.append("No AWS credentials found (keys, profile, or container role)")
        
        # Check vector dimension consistency
        if self.vector.vector_dimension not in [384, 512, 768, 1024]:
            warnings.append(f"Unusual vector dimension: {self.vector.vector_dimension}")
        
        # Check file size limits
        if self.file_validation.max_file_size_mb > self.file_validation.max_batch_size_mb:
            warnings.append("Individual file size limit exceeds batch size limit")
        
        return warnings
    
    def to_dict(self) -> Dict[str, Any]:
        """Export configuration as dictionary (excluding sensitive data)"""
        return {
            'server': self.server.dict(exclude={'aws_access_key_id', 'aws_secret_access_key'}),
            'aws': self.aws.dict(exclude={'aws_access_key_id', 'aws_secret_access_key'}),
            'vector': self.vector.dict(),
            'file_validation': self.file_validation.dict(),
            'performance': self.performance.dict()
        }


# Global configuration instance
_config: Optional[S3VectorConfig] = None


def get_config(env_file: Optional[str] = None, reload: bool = False) -> S3VectorConfig:
    """
    Get the global configuration instance.
    
    Args:
        env_file: Optional path to .env file
        reload: Force reload of configuration
        
    Returns:
        S3VectorConfig instance
    """
    global _config
    
    if _config is None or reload:
        _config = S3VectorConfig(env_file)
        
        # Validate configuration
        warnings = _config.validate_configuration()
        for warning in warnings:
            logger.warning(f"Configuration warning: {warning}")
    
    return _config


def reset_config():
    """Reset the global configuration (useful for testing)"""
    global _config
    _config = None 