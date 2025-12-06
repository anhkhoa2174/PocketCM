import pytest
from unittest.mock import Mock, patch, AsyncMock
import aiohttp
import asyncio

from src.services.api_client import APIClientService
from src.models.schemas import CustomerRecord, SubscriptionTier
from datetime import date


class TestAPIClientService:
    """Test API client service functionality"""

    @pytest.fixture
    def api_client(self):
        """Create API client instance"""
        with patch('src.services.api_client.settings'):
            return APIClientService()

    @pytest.fixture
    def sample_customers(self):
        """Create sample customer records for testing"""
        return [
            CustomerRecord(
                customer_name="John Doe",
                email="john@example.com",
                subscription_tier=SubscriptionTier.PRO,
                signup_date=date(2024, 1, 15)
            ),
            CustomerRecord(
                customer_name="Jane Smith",
                email="jane@example.com",
                subscription_tier=SubscriptionTier.BASIC,
                signup_date=date(2024, 1, 20)
            )
        ]

    @pytest.mark.asyncio
    async def test_sync_customer_data_success(self, api_client, sample_customers):
        """Test successful customer data synchronization"""
        with patch('aiohttp.ClientSession') as mock_session_class:
            mock_session = AsyncMock()
            mock_response = AsyncMock()
            mock_response.status = 200

            mock_session.post.return_value.__aenter__.return_value = mock_response
            mock_session_class.return_value.__aenter__.return_value = mock_session

            success, error = await api_client.sync_customer_data(sample_customers)

            assert success is True
            assert error is None
            mock_session.post.assert_called()

    @pytest.mark.asyncio
    async def test_sync_customer_data_http_error(self, api_client, sample_customers):
        """Test handling of HTTP errors during sync"""
        with patch('aiohttp.ClientSession') as mock_session_class:
            mock_session = AsyncMock()
            mock_response = AsyncMock()
            mock_response.status = 500
            mock_response.text = AsyncMock(return_value="Internal Server Error")

            mock_session.post.return_value.__aenter__.return_value = mock_response
            mock_session_class.return_value.__aenter__.return_value = mock_session

            success, error = await api_client.sync_customer_data(sample_customers)

            assert success is False
            assert "HTTP 500" in error

    @pytest.mark.asyncio
    async def test_sync_customer_data_with_retries(self, api_client, sample_customers):
        """Test retry mechanism on failures"""
        with patch('aiohttp.ClientSession') as mock_session_class:
            mock_session = AsyncMock()
            mock_response = AsyncMock()

            # First attempt fails, second succeeds
            mock_response.status = 500
            mock_response.text = AsyncMock(return_value="Server Error")
            mock_session.post.return_value.__aenter__.return_value = mock_response
            mock_session_class.return_value.__aenter__.return_value = mock_session

            success, error = await api_client.sync_customer_data(sample_customers)

            # Should fail after retries
            assert success is False
            assert error is not None

    @pytest.mark.asyncio
    async def test_sync_customer_data_empty_list(self, api_client):
        """Test sync with empty customer list"""
        success, error = await api_client.sync_customer_data([])

        assert success is True
        assert error is None

    @pytest.mark.asyncio
    async def test_send_data_individual_records(self, api_client, sample_customers):
        """Test sending records individually"""
        with patch('aiohttp.ClientSession') as mock_session_class:
            mock_session = AsyncMock()
            mock_response = AsyncMock()
            mock_response.status = 201

            mock_session.post.return_value.__aenter__.return_value = mock_response
            mock_session_class.return_value.__aenter__.return_value = mock_session

            payload = {
                "timestamp": "2024-01-01T00:00:00",
                "total_records": 1,
                "customers": [sample_customers[0].model_dump()]
            }

            success, error = await api_client._send_data(
                [sample_customers[0].model_dump_json()],
                payload,
                1
            )

            assert success is True
            assert error is None

    @pytest.mark.asyncio
    async def test_send_data_batch_fallback(self, api_client, sample_customers):
        """Test batch sending when individual sending fails"""
        with patch('aiohttp.ClientSession') as mock_session_class:
            mock_session = AsyncMock()
            mock_response = AsyncMock()

            # Individual sending fails, batch succeeds
            mock_response.status = 500
            mock_response.text = AsyncMock(return_value="Error")
            mock_session.post.return_value.__aenter__.return_value = mock_response
            mock_session_class.return_value.__aenter__.return_value = mock_session

            # Mock batch to succeed
            def mock_post_side_effect(*args, **kwargs):
                if 'batch' in str(args[0]):
                    mock_response.status = 200
                return mock_session.post.return_value

            mock_session.post.side_effect = mock_post_side_effect

            payload = {
                "timestamp": "2024-01-01T00:00:00",
                "total_records": 2,
                "customers": [c.model_dump() for c in sample_customers]
            }

            success, error = await api_client._send_data(
                [c.model_dump_json() for c in sample_customers],
                payload,
                1
            )

            assert success is True

    @pytest.mark.asyncio
    async def test_send_data_timeout_error(self, api_client, sample_customers):
        """Test handling of timeout errors"""
        with patch('aiohttp.ClientSession') as mock_session_class:
            mock_session = AsyncMock()
            mock_session.post.side_effect = asyncio.TimeoutError()
            mock_session_class.return_value.__aenter__.return_value = mock_session

            payload = {
                "timestamp": "2024-01-01T00:00:00",
                "total_records": 1,
                "customers": [sample_customers[0].model_dump()]
            }

            success, error = await api_client._send_data(
                [sample_customers[0].model_dump_json()],
                payload,
                1
            )

            assert success is False
            assert "Request timeout" in error

    @pytest.mark.asyncio
    async def test_test_connection_success(self, api_client):
        """Test successful connection test"""
        with patch('aiohttp.ClientSession') as mock_session_class:
            mock_session = AsyncMock()
            mock_response = AsyncMock()
            mock_response.status = 200

            mock_session.post.return_value.__aenter__.return_value = mock_response
            mock_session_class.return_value.__aenter__.return_value = mock_session

            success, result = await api_client.test_connection()

            assert success is True
            assert "connection successful" in result["message"]

    @pytest.mark.asyncio
    async def test_test_connection_failure(self, api_client):
        """Test connection test failure"""
        with patch('aiohttp.ClientSession') as mock_session_class:
            mock_session = AsyncMock()
            mock_response = AsyncMock()
            mock_response.status = 500
            mock_response.text = AsyncMock(return_value="Connection failed")

            mock_session.post.return_value.__aenter__.return_value = mock_response
            mock_session_class.return_value.__aenter__.return_value = mock_session

            success, result = await api_client.test_connection()

            assert success is False
            assert "Connection test failed" in result["message"]

    @pytest.mark.asyncio
    async def test_test_connection_exception(self, api_client):
        """Test connection test with exception"""
        with patch('aiohttp.ClientSession') as mock_session_class:
            mock_session = AsyncMock()
            mock_session.post.side_effect = Exception("Network error")
            mock_session_class.return_value.__aenter__.return_value = mock_session

            with pytest.raises(Exception, match="Connection test error"):
                await api_client.test_connection()

    @pytest.mark.asyncio
    async def test_send_with_retry_exponential_backoff(self, api_client):
        """Test exponential backoff in retry mechanism"""
        call_count = 0
        call_times = []

        async def mock_send_with_retry(*args, **kwargs):
            nonlocal call_count, call_times
            import time
            call_count += 1
            call_times.append(time.time())

            if call_count < 3:
                return False, "Temporary failure"
            else:
                return True, None

        with patch.object(api_client, '_send_data', side_effect=mock_send_with_retry):
            success, error = await api_client.sync_customer_data([])

        # Should have been called 3 times (initial + 2 retries)
        assert call_count == 3

    @pytest.mark.asyncio
    async def test_send_with_retry_max_attempts_reached(self, api_client, sample_customers):
        """Test retry mechanism reaching max attempts"""
        async def mock_send_with_retry(*args, **kwargs):
            return False, "Persistent failure"

        with patch.object(api_client, '_send_data', side_effect=mock_send_with_retry):
            success, error = await api_client.sync_customer_data(sample_customers)

        assert success is False
        assert "after 4 attempts" in error