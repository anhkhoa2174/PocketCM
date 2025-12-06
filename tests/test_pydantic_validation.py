import pytest
from datetime import date, datetime
from pydantic import ValidationError

from src.models.schemas import CustomerRecord, SubscriptionTier


class TestCustomerRecord:
    """Test Pydantic validation for CustomerRecord model"""

    def test_valid_customer_record(self):
        """Test creating a valid customer record"""
        customer = CustomerRecord(
            customer_name="John Doe",
            email="john.doe@example.com",
            subscription_tier="Pro",
            signup_date="2024-01-15"
        )

        assert customer.customer_name == "John Doe"
        assert customer.email == "john.doe@example.com"
        assert customer.subscription_tier == SubscriptionTier.PRO
        assert customer.signup_date == date(2024, 1, 15)

    def test_email_validation_valid_formats(self):
        """Test various valid email formats"""
        valid_emails = [
            "user@example.com",
            "user.name@example.com",
            "user+tag@example.com",
            "user123@example-domain.com",
            "USER@EXAMPLE.COM",  # Should be normalized to lowercase
            "  user@example.com  "  # Should be stripped
        ]

        for email in valid_emails:
            customer = CustomerRecord(
                customer_name="Test User",
                email=email,
                subscription_tier="Basic",
                signup_date="2024-01-01"
            )
            assert customer.email == email.strip().lower()

    def test_email_validation_invalid_formats(self):
        """Test invalid email formats raise errors"""
        invalid_emails = [
            "user@",  # Missing domain
            "@example.com",  # Missing user
            "user.example.com",  # Missing @
            "user@.com",  # Invalid domain
            "user@example",  # Missing TLD
            "",  # Empty string
            "not-an-email"
        ]

        for email in invalid_emails:
            with pytest.raises(ValidationError, match="Invalid email format"):
                CustomerRecord(
                    customer_name="Test User",
                    email=email,
                    subscription_tier="Basic",
                    signup_date="2024-01-01"
                )

    def test_subscription_tier_normalization(self):
        """Test subscription tier normalization"""
        test_cases = [
            ("Professional", SubscriptionTier.PRO),
            ("prem", SubscriptionTier.PRO),
            ("PREMIUM", SubscriptionTier.PRO),
            ("basic", SubscriptionTier.BASIC),
            ("Basic", SubscriptionTier.BASIC),
            ("Enterprise", SubscriptionTier.ENTERPRISE),
            ("CORP", SubscriptionTier.ENTERPRISE),
            ("Unknown Tier", SubscriptionTier.BASIC),  # Defaults to Basic
            (SubscriptionTier.PRO, SubscriptionTier.PRO),  # Already enum
        ]

        for input_tier, expected_tier in test_cases:
            customer = CustomerRecord(
                customer_name="Test User",
                email="test@example.com",
                subscription_tier=input_tier,
                signup_date="2024-01-01"
            )
            assert customer.subscription_tier == expected_tier

    def test_date_parsing_various_formats(self):
        """Test date parsing with various formats"""
        test_cases = [
            ("2024-01-15", date(2024, 1, 15)),
            ("01/15/2024", date(2024, 1, 15)),
            ("15/01/2024", date(2024, 1, 15)),
            ("January 15, 2024", date(2024, 1, 15)),
            ("Jan 15, 2024", date(2024, 1, 15)),
            ("15 Jan 2024", date(2024, 1, 15)),
            ("2024/01/15", date(2024, 1, 15)),
            ("01-15-2024", date(2024, 1, 15)),
            ("1st Jan 2024", date(2024, 1, 1)),  # Ordinal suffix
            ("2nd Jan 2024", date(2024, 1, 2)),
            ("3rd Jan 2024", date(2024, 1, 3)),
            ("4th Jan 2024", date(2024, 1, 4)),
            (date(2024, 5, 20), date(2024, 5, 20)),  # Already date object
        ]

        for input_date, expected_date in test_cases:
            customer = CustomerRecord(
                customer_name="Test User",
                email="test@example.com",
                subscription_tier="Basic",
                signup_date=input_date
            )
            assert customer.signup_date == expected_date

    def test_date_parsing_invalid_formats(self):
        """Test invalid date formats raise errors"""
        invalid_dates = [
            "not-a-date",
            "32/01/2024",  # Invalid day
            "01/13/2024",  # Invalid month
            "2024-13-01",  # Invalid month
            "",  # Empty string
        ]

        for invalid_date in invalid_dates:
            with pytest.raises(ValidationError, match="Unable to parse date"):
                CustomerRecord(
                    customer_name="Test User",
                    email="test@example.com",
                    subscription_tier="Basic",
                    signup_date=invalid_date
                )

    def test_customer_name_validation(self):
        """Test customer name validation and cleaning"""
        test_cases = [
            ("John Doe", "John Doe"),
            ("  John Doe  ", "John Doe"),  # Whitespace trimmed
            ("John   Doe", "John Doe"),  # Multiple spaces collapsed
            ("JOHN DOE", "JOHN DOE"),  # Case preserved
        ]

        for input_name, expected_name in test_cases:
            customer = CustomerRecord(
                customer_name=input_name,
                email="test@example.com",
                subscription_tier="Basic",
                signup_date="2024-01-01"
            )
            assert customer.customer_name == expected_name

    def test_customer_name_invalid(self):
        """Test invalid customer names"""
        invalid_names = [
            "",  # Empty string
            "   ",  # Only whitespace
            None,  # None value
        ]

        for invalid_name in invalid_names:
            with pytest.raises(ValidationError):
                CustomerRecord(
                    customer_name=invalid_name,
                    email="test@example.com",
                    subscription_tier="Basic",
                    signup_date="2024-01-01"
                )

    def test_missing_required_fields(self):
        """Test missing required fields raise errors"""
        with pytest.raises(ValidationError, match="Missing required fields"):
            CustomerRecord(
                customer_name="John Doe",
                # Missing email, subscription_tier, signup_date
            )

    def test_model_serialization(self):
        """Test model serialization to JSON"""
        customer = CustomerRecord(
            customer_name="John Doe",
            email="john.doe@example.com",
            subscription_tier="Pro",
            signup_date="2024-01-15"
        )

        # Test model_dump
        data = customer.model_dump()
        assert data["customer_name"] == "John Doe"
        assert data["email"] == "john.doe@example.com"
        assert data["subscription_tier"] == "Pro"
        assert data["signup_date"] == "2024-01-15"

        # Test model_dump_json
        json_str = customer.model_dump_json()
        assert "john.doe@example.com" in json_str
        assert "Pro" in json_str

    def test_complex_real_world_examples(self):
        """Test with messy real-world data examples"""
        real_world_examples = [
            {
                "customer_name": "  Alice   Smith  ",
                "email": "ALICE.SMITH@COMPANY.COM",
                "subscription_tier": "Professional",
                "signup_date": "Jan 1st, 2024"
            },
            {
                "customer_name": "Bob Johnson",
                "email": "bob.johnson@startup.io",
                "subscription_tier": "PREMIUM",
                "signup_date": "01/15/2024"
            },
            {
                "customer_name": "Carol Williams",
                "email": "carol@enterprise.org",
                "subscription_tier": "Corp",
                "signup_date": "2024-02-29"  # Leap year
            }
        ]

        expected_results = [
            {
                "customer_name": "Alice Smith",
                "email": "alice.smith@company.com",
                "subscription_tier": SubscriptionTier.PRO,
                "signup_date": date(2024, 1, 1)
            },
            {
                "customer_name": "Bob Johnson",
                "email": "bob.johnson@startup.io",
                "subscription_tier": SubscriptionTier.PRO,
                "signup_date": date(2024, 1, 15)
            },
            {
                "customer_name": "Carol Williams",
                "email": "carol@enterprise.org",
                "subscription_tier": SubscriptionTier.ENTERPRISE,
                "signup_date": date(2024, 2, 29)
            }
        ]

        for i, example in enumerate(real_world_examples):
            customer = CustomerRecord(**example)
            expected = expected_results[i]

            assert customer.customer_name == expected["customer_name"]
            assert customer.email == expected["email"]
            assert customer.subscription_tier == expected["subscription_tier"]
            assert customer.signup_date == expected["signup_date"]