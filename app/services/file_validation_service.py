import os
import mimetypes
import logging
from typing import Set, Optional, Dict, Any
from pathlib import Path

logger = logging.getLogger(__name__)


class FileValidationError(ValueError):
    """Custom exception for file validation errors"""
    pass


class FileValidationService:
    """Service for validating file uploads with configurable limits"""
    
    def __init__(self):
        """Initialize the file validation service with environment-based configuration"""
        # File size limits (in bytes)
        self.max_file_size = int(os.getenv('MAX_FILE_SIZE_MB', '50')) * 1024 * 1024  # Default 50MB
        self.max_total_batch_size = int(os.getenv('MAX_BATCH_SIZE_MB', '200')) * 1024 * 1024  # Default 200MB
        
        # Allowed file types (MIME types)
        self.allowed_mime_types = self._parse_allowed_types(
            os.getenv('ALLOWED_FILE_TYPES', 'text/*,application/pdf,image/*')
        )
        
        # Blocked file extensions (security)
        self.blocked_extensions = self._parse_blocked_extensions(
            os.getenv('BLOCKED_FILE_EXTENSIONS', '.exe,.bat,.cmd,.scr,.com,.pif,.dll,.sys')
        )
        
        logger.info(f"File validation initialized: max_size={self.max_file_size/1024/1024:.1f}MB, "
                   f"allowed_types={len(self.allowed_mime_types)}, "
                   f"blocked_extensions={len(self.blocked_extensions)}")
    
    def _parse_allowed_types(self, types_str: str) -> Set[str]:
        """Parse allowed MIME types from environment variable"""
        types = set()
        for mime_type in types_str.split(','):
            mime_type = mime_type.strip()
            if mime_type:
                types.add(mime_type.lower())
        return types
    
    def _parse_blocked_extensions(self, extensions_str: str) -> Set[str]:
        """Parse blocked file extensions from environment variable"""
        extensions = set()
        for ext in extensions_str.split(','):
            ext = ext.strip().lower()
            if ext and not ext.startswith('.'):
                ext = '.' + ext
            if ext:
                extensions.add(ext)
        return extensions
    
    def validate_file(self, file_path: str, content_type: Optional[str] = None) -> Dict[str, Any]:
        """
        Validate a single file for upload
        
        Args:
            file_path: Path to the file to validate
            content_type: Optional MIME type (will be inferred if not provided)
            
        Returns:
            Dictionary with validation results and file info
            
        Raises:
            FileValidationError: If validation fails
        """
        # Check if file exists
        if not os.path.exists(file_path):
            raise FileValidationError(f"File not found: {file_path}")
        
        if not os.path.isfile(file_path):
            raise FileValidationError(f"Path is not a file: {file_path}")
        
        # Get file info
        file_size = os.path.getsize(file_path)
        file_name = os.path.basename(file_path)
        file_extension = Path(file_path).suffix.lower()
        
        # Validate file size
        if file_size > self.max_file_size:
            raise FileValidationError(
                f"File size ({file_size/1024/1024:.1f}MB) exceeds maximum allowed "
                f"size ({self.max_file_size/1024/1024:.1f}MB): {file_name}"
            )
        
        if file_size == 0:
            raise FileValidationError(f"File is empty: {file_name}")
        
        # Check blocked extensions
        if file_extension in self.blocked_extensions:
            raise FileValidationError(
                f"File extension '{file_extension}' is not allowed for security reasons: {file_name}"
            )
        
        # Determine and validate MIME type
        if content_type is None:
            content_type, _ = mimetypes.guess_type(file_path)
            if content_type is None:
                content_type = 'application/octet-stream'
        
        content_type = content_type.lower()
        
        # Validate MIME type
        if not self._is_mime_type_allowed(content_type):
            raise FileValidationError(
                f"File type '{content_type}' is not allowed. "
                f"Allowed types: {', '.join(sorted(self.allowed_mime_types))}"
            )
        
        return {
            'file_path': file_path,
            'file_name': file_name,
            'file_size': file_size,
            'content_type': content_type,
            'file_extension': file_extension,
            'is_valid': True
        }
    
    def _is_mime_type_allowed(self, content_type: str) -> bool:
        """Check if a MIME type is allowed"""
        # Direct match
        if content_type in self.allowed_mime_types:
            return True
        
        # Wildcard match (e.g., text/* matches text/plain)
        main_type = content_type.split('/')[0] + '/*'
        if main_type in self.allowed_mime_types:
            return True
        
        # Universal wildcard
        if '*/*' in self.allowed_mime_types:
            return True
        
        return False
    
    def validate_batch(self, file_paths: list, content_types: Optional[list] = None) -> Dict[str, Any]:
        """
        Validate multiple files for batch upload
        
        Args:
            file_paths: List of file paths to validate
            content_types: Optional list of MIME types (same length as file_paths)
            
        Returns:
            Dictionary with validation results for all files
        """
        if content_types is None:
            content_types = [None] * len(file_paths)
        
        if len(content_types) != len(file_paths):
            raise FileValidationError("Content types list must match file paths list length")
        
        valid_files = []
        invalid_files = []
        total_size = 0
        
        for i, file_path in enumerate(file_paths):
            try:
                file_info = self.validate_file(file_path, content_types[i])
                valid_files.append(file_info)
                total_size += file_info['file_size']
            except FileValidationError as e:
                invalid_files.append({
                    'file_path': file_path,
                    'error': str(e),
                    'is_valid': False
                })
        
        # Check total batch size
        if total_size > self.max_total_batch_size:
            raise FileValidationError(
                f"Total batch size ({total_size/1024/1024:.1f}MB) exceeds maximum allowed "
                f"batch size ({self.max_total_batch_size/1024/1024:.1f}MB)"
            )
        
        return {
            'valid_files': valid_files,
            'invalid_files': invalid_files,
            'total_files': len(file_paths),
            'valid_count': len(valid_files),
            'invalid_count': len(invalid_files),
            'total_size_bytes': total_size,
            'total_size_mb': round(total_size / 1024 / 1024, 2),
            'is_valid': len(invalid_files) == 0
        }
    
    def get_validation_config(self) -> Dict[str, Any]:
        """Get current validation configuration"""
        return {
            'max_file_size_mb': round(self.max_file_size / 1024 / 1024, 1),
            'max_batch_size_mb': round(self.max_total_batch_size / 1024 / 1024, 1),
            'allowed_mime_types': sorted(list(self.allowed_mime_types)),
            'blocked_extensions': sorted(list(self.blocked_extensions))
        } 