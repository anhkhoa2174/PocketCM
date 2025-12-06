import aiohttp
import asyncio
import logging
from typing import List, Optional
from datetime import datetime

from ..models.schemas import CustomerRecord
from ..core.config import settings

logger = logging.getLogger(__name__)


class APIClientService:
    def __init__(self):
        self.destination_url = settings.destination_api_url
        self.max_retries = settings.max_retries
        self.retry_delay = settings.retry_delay

    async def sync_customer_data(self, customers: List[CustomerRecord]) -> tuple[bool, Optional[str]]:
        """
        Sync customer data to external API with retry mechanism
        Returns: (success, error_message)
        """
        if not customers:
            logger.warning("No customers to sync")
            return True, None

        # Convert customers to JSON
        try:
            payload = {
                "timestamp": datetime.utcnow().isoformat(),
                "total_records": len(customers),
                "customers": [customer.model_dump() for customer in customers]
            }
            json_data = [customer.model_dump_json() for customer in customers]
        except Exception as e:
            error_msg = f"Failed to serialize customer data: {str(e)}"
            logger.error(error_msg)
            return False, error_msg

        # Attempt to sync with retries
        return await self._send_with_retry(json_data, payload)

    async def _send_with_retry(self, json_data: List[str], payload: dict) -> tuple[bool, Optional[str]]:
        """
        Send data with exponential backoff retry mechanism
        """
        last_error = None

        for attempt in range(self.max_retries + 1):  # +1 for initial attempt
            try:
                if attempt > 0:
                    delay = self.retry_delay * (2 ** (attempt - 1))  # Exponential backoff
                    logger.info(f"Retrying in {delay} seconds (attempt {attempt + 1}/{self.max_retries + 1})")
                    await asyncio.sleep(delay)

                success, error = await self._send_data(json_data, payload, attempt + 1)
                if success:
                    return True, None

            except Exception as e:
                last_error = str(e)
                logger.warning(f"Attempt {attempt + 1} failed: {last_error}")

        # All retries failed
        error_msg = f"Failed to sync data after {self.max_retries + 1} attempts. Last error: {last_error}"
        logger.error(error_msg)
        return False, error_msg

    async def _send_data(self, json_data: List[str], payload: dict, attempt: int) -> tuple[bool, Optional[str]]:
        """
        Send data to external API
        """
        timeout = aiohttp.ClientTimeout(total=30)  # 30 second timeout

        try:
            async with aiohttp.ClientSession(timeout=timeout) as session:
                # Create headers
                headers = {
                    'Content-Type': 'application/json',
                    'User-Agent': f'{settings.app_name}/{settings.app_version}',
                    'X-Attempt-Number': str(attempt),
                    'X-Total-Records': str(len(json_data))
                }

                # Try to send as individual records first
                if len(json_data) == 1:
                    # Single record
                    success, error = await self._send_single_record(session, json_data[0], headers)
                    if success:
                        return True, None
                else:
                    # Multiple records - try both individual and batch
                    batch_success = True
                    for record_json in json_data:
                        success, error = await self._send_single_record(session, record_json, headers)
                        if not success:
                            batch_success = False
                            break

                    if batch_success:
                        return True, None

                # Fallback: send as batch
                return await self._send_batch(session, payload, headers)

        except asyncio.TimeoutError:
            return False, "Request timeout"
        except aiohttp.ClientError as e:
            return False, f"HTTP client error: {str(e)}"
        except Exception as e:
            return False, f"Unexpected error: {str(e)}"

    async def _send_single_record(self, session: aiohttp.ClientSession, record_json: str, headers: dict) -> tuple[bool, Optional[str]]:
        """
        Send a single customer record
        """
        try:
            async with session.post(self.destination_url, data=record_json, headers=headers) as response:
                if response.status in [200, 201, 202]:
                    logger.info(f"Successfully synced single record. Status: {response.status}")
                    return True, None
                else:
                    error_text = await response.text()
                    logger.warning(f"Failed to sync record. Status: {response.status}, Error: {error_text}")
                    return False, f"HTTP {response.status}: {error_text}"
        except Exception as e:
            return False, str(e)

    async def _send_batch(self, session: aiohttp.ClientSession, payload: dict, headers: dict) -> tuple[bool, Optional[str]]:
        """
        Send batch payload
        """
        try:
            import json
            batch_json = json.dumps(payload)

            async with session.post(self.destination_url, data=batch_json, headers=headers) as response:
                if response.status in [200, 201, 202]:
                    logger.info(f"Successfully synced batch data. Status: {response.status}")
                    return True, None
                else:
                    error_text = await response.text()
                    logger.warning(f"Failed to sync batch. Status: {response.status}, Error: {error_text}")
                    return False, f"HTTP {response.status}: {error_text}"
        except Exception as e:
            return False, str(e)

    async def test_connection(self) -> tuple[bool, Optional[str]]:
        """
        Test connection to external API
        """
        try:
            timeout = aiohttp.ClientTimeout(total=10)
            async with aiohttp.ClientSession(timeout=timeout) as session:
                test_payload = {
                    "test": True,
                    "timestamp": datetime.utcnow().isoformat(),
                    "message": "Connection test from Pocket CM AI Agent"
                }

                headers = {
                    'Content-Type': 'application/json',
                    'User-Agent': f'{settings.app_name}/{settings.app_version}'
                }

                import json
                async with session.post(self.destination_url, data=json.dumps(test_payload), headers=headers) as response:
                    if response.status in [200, 201, 202]:
                        logger.info("API connection test successful")
                        return True, None
                    else:
                        error_text = await response.text()
                        return False, f"Connection test failed. Status: {response.status}, Error: {error_text}"

        except Exception as e:
            return False, f"Connection test error: {str(e)}"