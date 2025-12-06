import pytest
import os
from unittest.mock import patch

from src.core.config import Settings


class TestSettings:
    """Test application configuration settings"""

    def test_default_settings(self):
        """Test default configuration values"""
        settings = Settings()

        assert settings.app_name == "Pocket CM AI Onboarding Agent"
        assert settings.app_version == "1.0.0"
        assert settings.debug is False
        assert settings.api_host == "0.0.0.0"
        assert settings.api_port == 8000
        assert settings.max_file_size == 10 * 1024 * 1024  # 10MB
        assert settings.rate_limit_requests == 5
        assert settings.rate_limit_window == 60

    def test_max_file_size_conversion(self):
        """Test max file size is correctly set in bytes"""
        settings = Settings()
        expected_size = 10 * 1024 * 1024  # 10MB in bytes
        assert settings.max_file_size == expected_size

    def test_allowed_mime_types(self):
        """Test allowed MIME types for file uploads"""
        settings = Settings()
        expected_mimes = [
            "application/csv",
            "text/csv",
            "application/vnd.ms-excel",
            "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            "application/pdf",
            "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            "application/json"
        ]
        assert settings.allowed_mime_types == expected_mimes

    def test_openai_default_settings(self):
        """Test default OpenAI settings"""
        settings = Settings()
        assert settings.openai_api_key is None
        assert settings.openai_model == "gpt-3.5-turbo"

    def test_api_client_default_settings(self):
        """Test default API client settings"""
        settings = Settings()
        assert "webhook.site" in settings.destination_api_url
        assert settings.max_retries == 3
        assert settings.retry_delay == 1.0

    def test_rate_limiting_defaults(self):
        """Test rate limiting default values"""
        settings = Settings()
        assert settings.rate_limit_requests == 5
        assert settings.rate_limit_window == 60

    @patch.dict(os.environ, {
        'DEBUG': 'true',
        'API_HOST': '127.0.0.1',
        'API_PORT': '9000',
        'OPENAI_API_KEY': 'test-key-123',
        'OPENAI_MODEL': 'gpt-4',
        'RATE_LIMIT_REQUESTS': '10',
        'DESTINATION_API_URL': 'https://api.example.com/webhook'
    })
    def test_settings_from_environment(self):
        """Test loading settings from environment variables"""
        settings = Settings()

        assert settings.debug is True
        assert settings.api_host == "127.0.0.1"
        assert settings.api_port == 9000
        assert settings.openai_api_key == "test-key-123"
        assert settings.openai_model == "gpt-4"
        assert settings.rate_limit_requests == 10
        assert "api.example.com" in settings.destination_api_url

    @patch.dict(os.environ, {
        'MAX_FILE_SIZE': '5242880'  # 5MB in bytes
    })
    def test_max_file_size_from_env(self):
        """Test max file size from environment"""
        settings = Settings()
        assert settings.max_file_size == 5242880

    @patch.dict(os.environ, {
        'MAX_RETRIES': '5',
        'RETRY_DELAY': '2.5'
    })
    def test_retry_settings_from_env(self):
        """Test retry settings from environment"""
        settings = Settings()
        assert settings.max_retries == 5
        assert settings.retry_delay == 2.5

    def test_case_insensitive_env_vars(self):
        """Test that environment variables are case insensitive"""
        with patch.dict(os.environ, {'debug': 'true'}):
            settings = Settings()
            assert settings.debug is True

    def test_upload_directory_default(self):
        """Test default upload directory"""
        settings = Settings()
        assert settings.upload_dir == "uploads"

    @patch.dict(os.environ, {
        'UPLOAD_DIR': '/tmp/uploads'
    })
    def test_upload_directory_from_env(self):
        """Test upload directory from environment"""
        settings = Settings()
        assert settings.upload_dir == "/tmp/uploads"

    def test_app_name_from_env(self):
        """Test app name from environment"""
        with patch.dict(os.environ, {'APP_NAME': 'Custom App Name'}):
            settings = Settings()
            assert settings.app_name == "Custom App Name"

    def test_app_version_from_env(self):
        """Test app version from environment"""
        with patch.dict(os.environ, {'APP_VERSION': '2.0.0'}):
            settings = Settings()
            assert settings.app_version == "2.0.0"

    def test_required_fields_not_none(self):
        """Test that required fields are not None"""
        settings = Settings()

        # These fields should never be None
        assert settings.app_name is not None
        assert settings.app_version is not None
        assert settings.api_host is not None
        assert settings.api_port is not None
        assert settings.allowed_mime_types is not None
        assert settings.rate_limit_requests is not None
        assert settings.rate_limit_window is not None

    def test_numeric_values_are_positive(self):
        """Test that numeric values are positive"""
        settings = Settings()

        assert settings.api_port > 0
        assert settings.max_file_size > 0
        assert settings.max_retries >= 0
        assert settings.retry_delay >= 0
        assert settings.rate_limit_requests > 0
        assert settings.rate_limit_window > 0

    def test_mime_types_are_strings(self):
        """Test that MIME types are valid strings"""
        settings = Settings()

        for mime_type in settings.allowed_mime_types:
            assert isinstance(mime_type, str)
            assert '/' in mime_type  # MIME types should contain a slash

    def test_urls_are_valid_format(self):
        """Test that URL settings have valid format"""
        settings = Settings()

        # Destination API URL should be a valid URL format
        assert 'http' in settings.destination_api_url