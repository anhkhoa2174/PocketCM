import pytest
import asyncio
import sys
import os

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()

@pytest.fixture
def mock_openai_key():
    """Mock OpenAI API key for testing"""
    with pytest.MonkeyPatch().context() as m:
        m.setenv("OPENAI_API_KEY", "test-key-123")
        yield

@pytest.fixture
def temp_upload_dir(tmp_path):
    """Create temporary upload directory"""
    upload_dir = tmp_path / "uploads"
    upload_dir.mkdir()
    return str(upload_dir)

@pytest.fixture
def sample_csv_content():
    """Sample CSV content for testing"""
    return """customer_name,email,subscription_tier,signup_date
John Doe,john@example.com,Professional,2024-01-15
Jane Smith,jane@company.com,Premium,01/20/2024
Bob Wilson,bob@startup.io,Basic,Jan 5th 2024"""

@pytest.fixture
def sample_json_content():
    """Sample JSON content for testing"""
    return """[
    {
        "customer_name": "Alice Cooper",
        "email": "alice@example.com",
        "subscription_tier": "Enterprise",
        "signup_date": "2024-02-01"
    },
    {
        "customer_name": "Charlie Brown",
        "email": "charlie@company.com",
        "subscription_tier": "Pro",
        "signup_date": "2024-01-10"
    }
]"""

@pytest.fixture
def sample_pdf_content():
    """Sample minimal PDF content for testing"""
    return b"%PDF-1.4\n1 0 obj\n<<\n/Type /Catalog\n/Pages 2 0 R\n>>\nendobj\n"

@pytest.fixture
def sample_docx_content():
    """Sample minimal DOCX content for testing"""
    # This is a very minimal DOCX file structure
    return b"PK\x03\x04\x14\x00\x06\x00"