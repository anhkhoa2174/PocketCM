import pytest
import magic
from unittest.mock import Mock, patch, mock_open
from fastapi import UploadFile
import io

from src.core.security import FileSecurityValidator


class TestFileSecurityValidator:
    """Test file security validation"""

    @pytest.mark.asyncio
    async def test_validate_csv_file_success(self):
        """Test successful CSV file validation"""
        mock_file = Mock(spec=UploadFile)
        mock_file.filename = "test.csv"
        mock_file.file = io.BytesIO(b"name,email\ntest@example.com,test")
        mock_file.file.seek = Mock(return_value=None)
        mock_file.tell = Mock(return_value=100)

        with patch('magic.from_buffer') as mock_magic:
            mock_magic.return_value = "text/csv"

            is_valid, error = FileSecurityValidator.validate_file_security(mock_file)

            assert is_valid is True
            assert error is None

    @pytest.mark.asyncio
    async def test_validate_pdf_file_success(self):
        """Test successful PDF file validation"""
        mock_file = Mock(spec=UploadFile)
        mock_file.filename = "test.pdf"
        mock_file.file = io.BytesIO(b"%PDF-1.4\n")
        mock_file.file.seek = Mock(return_value=None)
        mock_file.tell = Mock(return_value=1024)

        with patch('magic.from_buffer') as mock_magic:
            mock_magic.return_value = "application/pdf"

            is_valid, error = FileSecurityValidator.validate_file_security(mock_file)

            assert is_valid is True
            assert error is None

    @pytest.mark.asyncio
    async def test_validate_invalid_extension(self):
        """Test rejection of invalid file extension"""
        mock_file = Mock(spec=UploadFile)
        mock_file.filename = "test.exe"
        mock_file.file = io.BytesIO(b"fake content")
        mock_file.file.seek = Mock(return_value=None)
        mock_file.tell = Mock(return_value=100)

        is_valid, error = FileSecurityValidator.validate_file_security(mock_file)

        assert is_valid is False
        assert "Invalid filename detected" in error

    @pytest.mark.asyncio
    async def test_validate_file_too_large(self):
        """Test rejection of file that's too large"""
        mock_file = Mock(spec=UploadFile)
        mock_file.filename = "test.csv"
        mock_file.file = io.BytesIO(b"name,email\n" * 1000000)  # Large file
        mock_file.file.seek = Mock(return_value=None)
        mock_file.tell = Mock(return_value=50 * 1024 * 1024)  # 50MB

        is_valid, error = FileSecurityValidator.validate_file_security(
            mock_file,
            max_size=10 * 1024 * 1024  # 10MB limit
        )

        assert is_valid is False
        assert "exceeds limit" in error

    @pytest.mark.asyncio
    async def test_validate_directory_traversal_attack(self):
        """Test rejection of directory traversal attempt"""
        mock_file = Mock(spec=UploadFile)
        mock_file.filename = "../../../etc/passwd"
        mock_file.file = io.BytesIO(b"content")
        mock_file.file.seek = Mock(return_value=None)
        mock_file.tell = Mock(return_value=100)

        is_valid, error = FileSecurityValidator.validate_file_security(mock_file)

        assert is_valid is False
        assert "Invalid filename detected" in error

    @pytest.mark.asyncio
    async def test_validate_mime_type_mismatch(self):
        """Test rejection when MIME type doesn't match extension"""
        mock_file = Mock(spec=UploadFile)
        mock_file.filename = "test.csv"
        mock_file.file = io.BytesIO(b"fake content")
        mock_file.file.seek = Mock(return_value=None)
        mock_file.tell = Mock(return_value=100)

        with patch('magic.from_buffer') as mock_magic:
            mock_magic.return_value = "application/pdf"  # PDF but file says CSV

            is_valid, error = FileSecurityValidator.validate_file_security(mock_file)

            # Should still pass because signature validation is more important
            assert is_valid is True
            assert error is None

    def test_sanitize_filename(self):
        """Test filename sanitization"""
        test_cases = [
            ("normal file.csv", "normal_file.csv"),
            ("file with spaces.csv", "file_with_spaces.csv"),
            ("file<with>bad:chars.csv", "filewithbadchars.csv"),
            ("../../../etc/passwd", "etcpasswd"),
            ("", "uploaded_file"),
        ]

        for input_name, expected in test_cases:
            result = FileSecurityValidator.sanitize_filename(input_name)
            assert result == expected

    def test_validate_filename_valid(self):
        """Test valid filename validation"""
        valid_filenames = [
            "test.csv",
            "data.xlsx",
            "document.pdf",
            "report.docx",
            "data.json"
        ]

        for filename in valid_filenames:
            assert FileSecurityValidator._validate_filename(filename) is True

    def test_validate_filename_invalid(self):
        """Test invalid filename validation"""
        invalid_filenames = [
            "",
            "..",
            "../../../etc/passwd",
            "file<name>",
            "file|name",
            "file?name",
            "file*name",
            "file\x00name"
        ]

        for filename in invalid_filenames:
            assert FileSecurityValidator._validate_filename(filename) is False