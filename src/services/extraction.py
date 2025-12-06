import pandas as pd
import pdfplumber
import json
from docx import Document
from typing import List, Dict, Any, Optional
import openai
import instructor
from openai import OpenAI
from pathlib import Path
import io
import logging

from ..models.schemas import CustomerRecord
from ..core.config import settings

logger = logging.getLogger(__name__)


class DataExtractionService:
    def __init__(self):
        # Initialize OpenAI client with instructor for structured output
        if settings.openai_api_key:
            self.client = instructor.from_openai(OpenAI(api_key=settings.openai_api_key))
        else:
            self.client = None
            logger.warning("OpenAI API key not configured. AI extraction will be limited.")

    async def extract_data_from_file(self, file_content: bytes, filename: str) -> List[CustomerRecord]:
        """
        Extract structured customer data from various file formats
        """
        file_ext = Path(filename).suffix.lower()

        try:
            if file_ext == '.csv':
                return await self._extract_from_csv(file_content)
            elif file_ext == '.xlsx':
                return await self._extract_from_excel(file_content)
            elif file_ext == '.json':
                return await self._extract_from_json(file_content)
            elif file_ext == '.pdf':
                return await self._extract_from_pdf(file_content)
            elif file_ext == '.docx':
                return await self._extract_from_docx(file_content)
            else:
                raise ValueError(f"Unsupported file format: {file_ext}")
        except Exception as e:
            logger.error(f"Error extracting data from {filename}: {str(e)}")
            raise

    async def _extract_from_csv(self, file_content: bytes) -> List[CustomerRecord]:
        """Extract data from CSV files"""
        try:
            df = pd.read_csv(io.BytesIO(file_content))
            return self._dataframe_to_records(df)
        except Exception as e:
            raise ValueError(f"Failed to parse CSV: {str(e)}")

    async def _extract_from_excel(self, file_content: bytes) -> List[CustomerRecord]:
        """Extract data from Excel files"""
        try:
            df = pd.read_excel(io.BytesIO(file_content))
            return self._dataframe_to_records(df)
        except Exception as e:
            raise ValueError(f"Failed to parse Excel: {str(e)}")

    async def _extract_from_json(self, file_content: bytes) -> List[CustomerRecord]:
        """Extract data from JSON files"""
        try:
            data = json.loads(file_content.decode('utf-8'))

            # Handle different JSON structures
            if isinstance(data, list):
                records_data = data
            elif isinstance(data, dict):
                if 'customers' in data:
                    records_data = data['customers']
                elif 'data' in data:
                    records_data = data['data']
                else:
                    records_data = [data]  # Single record
            else:
                raise ValueError("Invalid JSON structure")

            return [CustomerRecord(**record) for record in records_data]
        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON format: {str(e)}")

    async def _extract_from_pdf(self, file_content: bytes) -> List[CustomerRecord]:
        """Extract data from PDF files using AI"""
        text_content = ""
        try:
            # Extract text from PDF
            with pdfplumber.open(io.BytesIO(file_content)) as pdf:
                for page in pdf.pages:
                    page_text = page.extract_text()
                    if page_text:
                        text_content += page_text + "\n"

            if not text_content.strip():
                raise ValueError("No text content found in PDF")

            return await self._extract_with_ai(text_content)
        except Exception as e:
            logger.error(f"PDF extraction failed, falling back to regex: {str(e)}")
            return self._extract_from_text_with_regex(text_content)

    async def _extract_from_docx(self, file_content: bytes) -> List[CustomerRecord]:
        """Extract data from DOCX files using AI"""
        text_content = ""
        try:
            doc = Document(io.BytesIO(file_content))

            for paragraph in doc.paragraphs:
                text_content += paragraph.text + "\n"

            if not text_content.strip():
                raise ValueError("No text content found in DOCX")

            return await self._extract_with_ai(text_content)
        except Exception as e:
            logger.error(f"DOCX extraction failed, falling back to regex: {str(e)}")
            return self._extract_from_text_with_regex(text_content)

    async def _extract_with_ai(self, text_content: str) -> List[CustomerRecord]:
        """
        Use AI to extract structured data from unstructured text
        """
        if not self.client:
            # Fallback to regex extraction
            return self._extract_from_text_with_regex(text_content)

        try:
            # Define the prompt for AI extraction
            prompt = f"""
            Extract customer information from the following text.
            Look for patterns like:
            - Customer names
            - Email addresses
            - Subscription tiers (Basic, Pro, Enterprise, Professional, Premium, etc.)
            - Signup dates

            Text content:
            {text_content}

            Return as a list of customers with these fields:
            - customer_name (string)
            - email (string)
            - subscription_tier (string: Basic, Pro, Enterprise, Professional, Premium, etc.)
            - signup_date (date in any format)
            """

            # Use instructor to get structured output
            customers = self.client.chat.completions.create(
                model=settings.openai_model,
                response_model=List[CustomerRecord],
                messages=[{"role": "user", "content": prompt}],
                temperature=0.1,
            )

            return customers
        except Exception as e:
            logger.error(f"AI extraction failed: {str(e)}")
            # Fallback to regex extraction
            return self._extract_from_text_with_regex(text_content)

    def _extract_from_text_with_regex(self, text_content: str) -> List[CustomerRecord]:
        """
        Plan B: fall back to regex when no AI; grab emails first
        """
        import re
        from datetime import datetime

        customers = []

        # Manual approach: catch emails first, then look back for a name
        email_pattern = r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}'
        emails = re.findall(email_pattern, text_content)

        for email in emails:
            try:
                # Lần tìm đoạn tên ngay trước email trên cùng một dòng
                lines = text_content.split('\n')
                name = "Unknown"  # Default name

                for line in lines:
                    if email in line:
                        # Look for potential name before email
                        words_before = line.split(email)[0].strip()
                        if words_before and len(words_before.split()) <= 3:
                            name = words_before.title()
                        break

                # Create a basic customer record
                customer_data = {
                    'customer_name': name,
                    'email': email,
                    'subscription_tier': 'Basic',  # Default
                    'signup_date': datetime.now().strftime('%Y-%m-%d')  # Default to today
                }

                customers.append(CustomerRecord(**customer_data))
            except Exception as e:
                logger.warning(f"Failed to create customer record for email {email}: {str(e)}")
                continue

        return customers if customers else []

    def _dataframe_to_records(self, df: pd.DataFrame) -> List[CustomerRecord]:
        """
        Convert pandas DataFrame to CustomerRecord objects
        Handles various column naming conventions
        """
        customers = []

        # Column mapping for common variations
        column_mapping = {
            'customer_name': ['name', 'customer', 'client_name', 'customer_name', 'fullname'],
            'email': ['email', 'email_address', 'mail', 'contact_email'],
            'subscription_tier': ['tier', 'subscription', 'plan', 'subscription_tier', 'level'],
            'signup_date': ['date', 'signup_date', 'join_date', 'created', 'registration_date']
        }

        # Find actual column names
        actual_columns = {}
        for field, possible_names in column_mapping.items():
            for col in df.columns:
                if col.lower() in [name.lower() for name in possible_names]:
                    actual_columns[field] = col
                    break

        # Check if we have minimum required columns
        if 'customer_name' not in actual_columns or 'email' not in actual_columns:
            raise ValueError("CSV must contain customer name and email columns")

        for _, row in df.iterrows():
            try:
                customer_data = {}

                for field in ['customer_name', 'email', 'subscription_tier', 'signup_date']:
                    if field in actual_columns:
                        customer_data[field] = row[actual_columns[field]]
                    else:
                        # Set defaults for missing fields
                        if field == 'subscription_tier':
                            customer_data[field] = 'Basic'
                        elif field == 'signup_date':
                            customer_data[field] = pd.Timestamp.now().strftime('%Y-%m-%d')

                customers.append(CustomerRecord(**customer_data))
            except Exception as e:
                logger.warning(f"Failed to process row: {row.to_dict()}, Error: {str(e)}")
                continue

        return customers
