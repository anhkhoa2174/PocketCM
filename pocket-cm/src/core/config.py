from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    app_name: str = "Pocket CM AI Onboarding Agent"
    app_version: str = "1.0.0"
    debug: bool = False

    # API Settings
    api_host: str = "0.0.0.0"
    api_port: int = 8000

    # File Upload Settings
    max_file_size: int = 10 * 1024 * 1024  # 10MB
    allowed_mime_types: list[str] = [
        "application/csv",
        "text/csv",
        "application/vnd.ms-excel",
        "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        "application/pdf",
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        "application/json"
    ]
    upload_dir: str = "uploads"

    # OpenAI Settings (for AI extraction)
    openai_api_key: Optional[str] = None
    openai_model: str = "gpt-3.5-turbo"

    # External API Settings
    destination_api_url: str = "https://webhook.site/your-webhook-url"
    max_retries: int = 3
    retry_delay: float = 1.0

    # Rate Limiting
    rate_limit_requests: int = 5
    rate_limit_window: int = 60  # seconds

    class Config:
        env_file = ".env"
        case_sensitive = False


settings = Settings()