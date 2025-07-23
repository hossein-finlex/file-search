# Test Fixtures

This directory contains test files used for validating the file upload and validation functionality of the S3 Vector Service.

## Files Overview

### Valid Test Files
- **`sample_text.txt`** - A valid text file that should pass all validation checks
  - MIME type: `text/plain`
  - Size: Small (under limits)
  - Purpose: Test successful upload scenarios

### Invalid Test Files

#### Empty Files
- **`empty_file.txt`** - An empty file (0 bytes)
  - Should be rejected: "File is empty"

#### Blocked Extensions
- **`fake_executable.exe`** - File with blocked extension
  - Should be rejected: "File extension '.exe' is not allowed for security reasons"
  - Tests security validation

#### Unsupported MIME Types
- **`binary_data.bin`** - File with unsupported MIME type
  - MIME type: `application/octet-stream`
  - Should be rejected: "File type 'application/octet-stream' is not allowed"

### Utility Scripts
- **`create_large_file.sh`** - Script to generate large files for size testing
  - Usage: `./create_large_file.sh [size_in_mb] [filename]`
  - Default: Creates 60MB file (exceeds 50MB limit)
  - Purpose: Test file size validation

## Usage in Tests

These fixtures are used in:
- Unit tests for `FileValidationService`
- Integration tests for upload endpoints
- Manual testing via API calls

## Validation Rules Tested

1. **File Size Limits**
   - Individual file: 50MB (configurable)
   - Batch total: 200MB (configurable)

2. **MIME Type Whitelist**
   - Allowed: `text/*`, `application/pdf`, `image/*`
   - Configurable via `ALLOWED_FILE_TYPES` environment variable

3. **Security Blacklist**
   - Blocked extensions: `.exe`, `.bat`, `.cmd`, `.scr`, `.com`, `.pif`, `.dll`, `.sys`
   - Configurable via `BLOCKED_FILE_EXTENSIONS` environment variable

4. **File Integrity**
   - Rejects empty files (0 bytes)
   - Validates file existence and readability

## Environment Configuration

Test behavior can be modified via environment variables:
```bash
MAX_FILE_SIZE_MB=50
MAX_BATCH_SIZE_MB=200
ALLOWED_FILE_TYPES=text/*,application/pdf,image/*
BLOCKED_FILE_EXTENSIONS=.exe,.bat,.cmd,.scr,.com,.pif,.dll,.sys
``` 