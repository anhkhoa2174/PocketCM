import pytest
import pandas as pd
import json
import io
from unittest.mock import Mock, patch, AsyncMock

from src.services.extraction import DataExtractionService
from src.models.schemas import CustomerRecord, SubscriptionTier


class TestDataExtractionService:
    """Test data extraction from various file formats"""

    @pytest.fixture
    def extraction_service(self):
        """Create extraction service instance"""
        with patch('src.services.extraction.settings'):
            return DataExtractionService()

    @pytest.mark.asyncio
    async def test_extract_from_csv_success(self, extraction_service):
        """Test successful CSV extraction"""
        csv_content = """customer_name,email,subscription_tier,signup_date
John Doe,john@example.com,Professional,2024-01-15
Jane Smith,jane@company.com,Premium,01/20/2024
Bob Wilson,bob@startup.io,Basic,Jan 5th 2024"""

        customers = await extraction_service._extract_from_csv(csv_content.encode())

        assert len(customers) == 3
        assert customers[0].customer_name == "John Doe"
        assert customers[0].email == "john@example.com"
        assert customers[0].subscription_tier == SubscriptionTier.PRO
        assert customers[0].signup_date.year == 2024

    @pytest.mark.asyncio
    async def test_extract_from_csv_column_mapping(self, extraction_service):
        """Test CSV extraction with various column names"""
        csv_content = """Name,Email,Plan,Join Date
Alice Cooper,alice@example.com,Enterprise,2024-02-01"""

        customers = await extraction_service._extract_from_csv(csv_content.encode())

        assert len(customers) == 1
        assert customers[0].customer_name == "Alice Cooper"
        assert customers[0].email == "alice@example.com"
        assert customers[0].subscription_tier == SubscriptionTier.ENTERPRISE

    @pytest.mark.asyncio
    async def test_extract_from_json_success(self, extraction_service):
        """Test successful JSON extraction"""
        json_data = [
            {
                "customer_name": "John Doe",
                "email": "john@example.com",
                "subscription_tier": "Professional",
                "signup_date": "2024-01-15"
            }
        ]

        customers = await extraction_service._extract_from_json(json.dumps(json_data).encode())

        assert len(customers) == 1
        assert customers[0].customer_name == "John Doe"
        assert customers[0].subscription_tier == SubscriptionTier.PRO

    @pytest.mark.asyncio
    async def test_extract_from_json_nested(self, extraction_service):
        """Test JSON extraction with nested structure"""
        json_data = {
            "data": [
                {
                    "customer_name": "Alice Smith",
                    "email": "alice@example.com",
                    "subscription_tier": "Premium",
                    "signup_date": "2024-01-20"
                }
            ]
        }

        customers = await extraction_service._extract_from_json(json.dumps(json_data).encode())

        assert len(customers) == 1
        assert customers[0].customer_name == "Alice Smith"
        assert customers[0].subscription_tier == SubscriptionTier.PRO

    @pytest.mark.asyncio
    async def test_extract_from_json_single_record(self, extraction_service):
        """Test JSON extraction with single record"""
        json_data = {
            "customer_name": "Bob Wilson",
            "email": "bob@example.com",
            "subscription_tier": "Basic",
            "signup_date": "2024-01-10"
        }

        customers = await extraction_service._extract_from_json(json.dumps(json_data).encode())

        assert len(customers) == 1
        assert customers[0].customer_name == "Bob Wilson"

    @pytest.mark.asyncio
    async def test_extract_from_excel_success(self, extraction_service):
        """Test successful Excel extraction"""
        # Create a simple Excel file in memory
        df = pd.DataFrame([
            {
                "customer_name": "John Doe",
                "email": "john@example.com",
                "subscription_tier": "Professional",
                "signup_date": "2024-01-15"
            }
        ])

        excel_buffer = io.BytesIO()
        df.to_excel(excel_buffer, index=False)
        excel_content = excel_buffer.getvalue()

        customers = await extraction_service._extract_from_excel(excel_content)

        assert len(customers) == 1
        assert customers[0].customer_name == "John Doe"
        assert customers[0].subscription_tier == SubscriptionTier.PRO

    @pytest.mark.asyncio
    async def test_extract_with_ai_fallback_to_regex(self, extraction_service):
        """Test AI extraction with regex fallback"""
        text_content = """
        Customer Information:
        Name: John Doe
        Email: john.doe@example.com
        Plan: Professional
        Member since: January 15, 2024

        Another customer:
        Name: Jane Smith
        Email: jane.smith@company.com
        Plan: Premium
        Joined: 01/20/2024
        """

        customers = await extraction_service._extract_from_text_with_regex(text_content)

        # Should find emails in the text
        assert len(customers) >= 2
        emails = [customer.email for customer in customers]
        assert "john.doe@example.com" in emails
        assert "jane.smith@company.com" in emails

    @pytest.mark.asyncio
    async def test_dataframe_to_records_clean_data(self, extraction_service):
        """Test converting clean DataFrame to records"""
        df = pd.DataFrame([
            {
                "customer_name": "John Doe",
                "email": "john@example.com",
                "subscription_tier": "Pro",
                "signup_date": "2024-01-15"
            },
            {
                "customer_name": "Jane Smith",
                "email": "jane@example.com",
                "subscription_tier": "Basic",
                "signup_date": "2024-01-20"
            }
        ])

        customers = extraction_service._dataframe_to_records(df)

        assert len(customers) == 2
        assert customers[0].customer_name == "John Doe"
        assert customers[1].customer_name == "Jane Smith"
        assert all(isinstance(customer, CustomerRecord) for customer in customers)

    @pytest.mark.asyncio
    async def test_dataframe_to_records_missing_columns(self, extraction_service):
        """Test DataFrame with missing required columns"""
        df = pd.DataFrame([
            {
                "name": "John Doe",  # Wrong column name
                "email_address": "john@example.com"  # Wrong column name
                # Missing subscription_tier and signup_date
            }
        ])

        with pytest.raises(ValueError, match="must contain customer name and email columns"):
            extraction_service._dataframe_to_records(df)

    @pytest.mark.asyncio
    async def test_dataframe_to_records_defaults(self, extraction_service):
        """Test DataFrame with missing optional fields"""
        df = pd.DataFrame([
            {
                "customer_name": "John Doe",
                "email": "john@example.com"
                # Missing subscription_tier and signup_date - should get defaults
            }
        ])

        customers = extraction_service._dataframe_to_records(df)

        assert len(customers) == 1
        assert customers[0].customer_name == "John Doe"
        assert customers[0].subscription_tier == SubscriptionTier.BASIC
        # signup_date should be today's date

    @pytest.mark.asyncio
    async def test_extract_data_from_file_unsupported_format(self, extraction_service):
        """Test extraction from unsupported file format"""
        with pytest.raises(ValueError, match="Unsupported file format"):
            await extraction_service.extract_data_from_file(b"content", "test.txt")

    @pytest.mark.asyncio
    async def test_extract_data_from_file_invalid_json(self, extraction_service):
        """Test extraction from invalid JSON"""
        invalid_json = b"{'invalid': json content"

        with pytest.raises(ValueError, match="Invalid JSON format"):
            await extraction_service.extract_data_from_file(invalid_json, "test.json")

    @pytest.mark.asyncio
    async def test_extract_data_from_file_invalid_csv(self, extraction_service):
        """Test extraction from malformed CSV"""
        malformed_csv = b"not,a,valid,csv,file"

        with pytest.raises(ValueError, match="Failed to parse CSV"):
            await extraction_service._extract_from_csv(malformed_csv)