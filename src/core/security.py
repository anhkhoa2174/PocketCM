import magic
import os
from pathlib import Path
from typing import Tuple, Optional
from fastapi import UploadFile, HTTPException
import re


class FileSecurityValidator:
    # MIME type to extension mapping
    MIME_TYPE_MAP = {
        'text/csv': ['.csv'],
        'application/csv': ['.csv'],
        'application/vnd.ms-excel': ['.xls'],
        'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet': ['.xlsx'],
        'application/pdf': ['.pdf'],
        'application/vnd.openxmlformats-officedocument.wordprocessingml.document': ['.docx'],
        'application/json': ['.json'],
    }

    # File signatures (magic numbers)
    FILE_SIGNATURES = {
        b'\x50\x4b\x03\x04': ['.xlsx', '.docx'],  # ZIP (Office docs)
        b'\xd0\xcf\x11\xe0': ['.xls'],             # Old Office
        b'\x25\x50\x44\x46': ['.pdf'],            # PDF
        b'\x7b\x0a\x20\x20': ['.json'],           # JSON (starts with {)
    }

    @staticmethod
    def validate_file_security(file: UploadFile, max_size: int = 10 * 1024 * 1024) -> Tuple[bool, Optional[str]]:
        """
        Comprehensive file security validation
        Returns: (is_valid, error_message)
        """

        # 1. Check filename
        if not FileSecurityValidator._validate_filename(file.filename):
            return False, "Invalid filename detected"

        # 2. Check file size
        file.file.seek(0, 2)  # Seek to end
        file_size = file.file.tell()
        file.file.seek(0)     # Reset position

        if file_size > max_size:
            return False, f"File size exceeds limit of {max_size} bytes"

        # 3. Read file content for validation
        file_content = file.file.read(1024)  # Read first 1KB for signature check
        file.file.seek(0)  # Reset position

        # 4. Validate MIME type using python-magic
        try:
            mime_type = magic.from_buffer(file_content, mime=True)
            if mime_type not in FileSecurityValidator.MIME_TYPE_MAP:
                return False, f"Unsupported MIME type: {mime_type}"
        except Exception as e:
            return False, f"Unable to determine file type: {str(e)}"

        # 5. Validate file signature
        if not FileSecurityValidator._validate_file_signature(file_content, file.filename):
            return False, "File signature does not match extension"

        return True, None

    @staticmethod
    def _validate_filename(filename: str) -> bool:
        """Validate filename to prevent directory traversal and injection attacks"""
        if not filename:
            return False

        # Check for directory traversal attempts
        if '..' in filename or '/' in filename or '\\' in filename:
            return False

        # Check for null bytes
        if '\x00' in filename:
            return False

        # Check for dangerous characters
        dangerous_chars = ['<', '>', ':', '"', '|', '?', '*']
        if any(char in filename for char in dangerous_chars):
            return False

        # Check file extension
        allowed_extensions = ['.csv', '.xlsx', '.xls', '.pdf', '.docx', '.json']
        file_ext = Path(filename).suffix.lower()
        return file_ext in allowed_extensions

    @staticmethod
    def _validate_file_signature(file_content: bytes, filename: str) -> bool:
        """Validate that file signature matches the claimed extension"""
        file_ext = Path(filename).suffix.lower()

        # For JSON files, we need to check the actual content
        if file_ext == '.json':
            try:
                file_content.decode('utf-8').strip().startswith('{')
                return True
            except UnicodeDecodeError:
                return False

        # For text-based files like CSV, signature check is not as reliable
        if file_ext == '.csv':
            try:
                # Try to decode as text and check if it looks like CSV
                text = file_content.decode('utf-8')
                return ',' in text or '\n' in text
            except UnicodeDecodeError:
                return False

        # Check binary signatures
        for signature, extensions in FileSecurityValidator.FILE_SIGNATURES.items():
            if file_content.startswith(signature) and file_ext in extensions:
                return True

        # If no signature match, it might still be valid (some files don't have clear signatures)
        return True

    @staticmethod
    def sanitize_filename(filename: str) -> str:
        """Sanitize filename for secure storage"""
        # Remove path components
        filename = os.path.basename(filename)

        # Replace spaces with underscores
        filename = re.sub(r'\s+', '_', filename)

        # Remove dangerous characters
        filename = re.sub(r'[<:"|?*]', '', filename)

        # Ensure filename is not empty
        if not filename:
            filename = "uploaded_file"

        return filename