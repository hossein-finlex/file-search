#!/bin/bash

# Script to create large files for testing file size validation
# Usage: ./create_large_file.sh [size_in_mb] [filename]

SIZE_MB=${1:-60}  # Default 60MB (exceeds 50MB limit)
FILENAME=${2:-large_test_file.txt}

echo "Creating ${SIZE_MB}MB test file: ${FILENAME}"
dd if=/dev/zero of="${FILENAME}" bs=1M count=${SIZE_MB}

echo "File created successfully:"
ls -lh "${FILENAME}"
echo "This file should exceed the default 50MB size limit and be rejected by validation." 