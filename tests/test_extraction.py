from datetime import date

from src.services.extraction import DataExtractionService
from src.models.schemas import CustomerRecord


def test_regex_extraction_fallback_produces_record():
    service = DataExtractionService()
    text = "Alice Johnson alice@example.com signed up on Jan 1st, 2024 with enterprise plan."

    customers = service._extract_from_text_with_regex(text)

    assert len(customers) == 1
    customer = customers[0]
    assert isinstance(customer, CustomerRecord)
    assert customer.customer_name == "Alice Johnson"
    assert customer.email == "alice@example.com"
    # Regex fallback defaults tier to Basic and date to today if not parsed
    assert customer.subscription_tier == customer.subscription_tier.BASIC
    assert customer.signup_date == date.today()
