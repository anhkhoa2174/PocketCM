import pytest
from datetime import date

from src.models.schemas import CustomerRecord, SubscriptionTier


def test_subscription_tier_normalization_and_email_lowercasing():
    record = CustomerRecord(
        customer_name="John Doe",
        email="JOHN.DOE@Example.com",
        subscription_tier="Professional",
        signup_date="2024-01-05",
    )

    assert record.subscription_tier == SubscriptionTier.PRO
    assert record.email == "john.doe@example.com"


def test_unknown_subscription_tier_defaults_to_basic():
    record = CustomerRecord(
        customer_name="Jane",
        email="jane@example.com",
        subscription_tier="UnknownTier",
        signup_date="01/06/2024",
    )

    assert record.subscription_tier == SubscriptionTier.BASIC


def test_signup_date_parses_ordinal_suffix():
    record = CustomerRecord(
        customer_name="Alice",
        email="alice@example.com",
        subscription_tier="Pro",
        signup_date="Jan 1st, 2024",
    )

    assert record.signup_date == date(2024, 1, 1)


def test_missing_required_field_raises_error():
    with pytest.raises(ValueError):
        CustomerRecord(
            email="no-name@example.com",
            subscription_tier="Basic",
            signup_date="2024-01-01",
        )
