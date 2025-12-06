from fastapi import APIRouter, UploadFile, File, HTTPException, Request, Depends, status
from slowapi import Limiter
from slowapi.util import get_remote_address
import logging
import os
from pathlib import Path
from typing import List

from ..models.schemas import CustomerRecord, FileUploadResponse, ErrorResponse
from ..services.extraction import DataExtractionService
from ..services.api_client import APIClientService
from ..core.security import FileSecurityValidator
from ..core.config import settings
from ..core.rate_limit import limiter

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1", tags=["upload"])

# Initialize services
extraction_service = DataExtractionService()
api_client = APIClientService()


@router.post("/upload", response_model=FileUploadResponse)
@limiter.limit(f"{settings.rate_limit_requests}/{settings.rate_limit_window}m")
async def upload_file(
    request: Request,
    file: UploadFile = File(..., description="Upload file (CSV, XLSX, PDF, DOCX, JSON)")
):
    """
    Upload and process customer data file

    - **file**: File to process (CSV, XLSX, PDF, DOCX, JSON formats supported)
    - **Max size**: 10MB
    - **Rate limit**: 5 requests per minute per IP
    """

    # Get client IP for logging
    client_ip = get_remote_address(request)
    logger.info(f"File upload request from IP: {client_ip}, filename: {file.filename}")

    # Validate file security
    is_valid, error_message = FileSecurityValidator.validate_file_security(
        file,
        max_size=settings.max_file_size
    )

    if not is_valid:
        logger.warning(f"Security validation failed for IP: {client_ip}, error: {error_message}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=ErrorResponse(
                error="Security validation failed",
                detail=error_message
            ).dict()
        )

    try:
        # Read file content
        file_content = await file.read()

        # Extract data from file
        logger.info(f"Extracting data from file: {file.filename}")
        customers = await extraction_service.extract_data_from_file(file_content, file.filename)

        if not customers:
            logger.warning(f"No customer records found in file: {file.filename}")
            return FileUploadResponse(
                success=False,
                message="No valid customer records found in the file",
                processed_records=0
            )

        # Sync data to external API
        logger.info(f"Syncing {len(customers)} customer records to external API")
        sync_success, sync_error = await api_client.sync_customer_data(customers)

        if sync_success:
            logger.info(f"Successfully processed file: {file.filename}, records: {len(customers)}")
            return FileUploadResponse(
                success=True,
                message=f"Successfully processed {len(customers)} customer records",
                processed_records=len(customers)
            )
        else:
            logger.error(f"Failed to sync data for file: {file.filename}, error: {sync_error}")
            # Data was extracted but sync failed
            return FileUploadResponse(
                success=False,
                message=f"Extracted {len(customers)} records but failed to sync to external API",
                processed_records=len(customers),
                errors=[sync_error] if sync_error else None
            )

    except ValueError as e:
        logger.error(f"Validation error for file {file.filename}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=ErrorResponse(
                error="Data validation failed",
                detail=str(e)
            ).dict()
        )
    except Exception as e:
        logger.error(f"Unexpected error processing file {file.filename}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=ErrorResponse(
                error="Internal server error",
                detail="An unexpected error occurred while processing the file"
            ).dict()
        )


@router.get("/upload/health")
async def health_check():
    """
    Health check endpoint for the upload service
    """
    return {
        "status": "healthy",
        "service": "Pocket CM AI Onboarding Agent",
        "version": settings.app_version
    }


@router.get("/upload/test-connection")
async def test_api_connection():
    """
    Test connection to external API
    """
    try:
        success, error = await api_client.test_connection()
        if success:
            return {
                "status": "success",
                "message": "External API connection successful"
            }
        else:
            return {
                "status": "error",
                "message": "External API connection failed",
                "error": error
            }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=ErrorResponse(
                error="Connection test failed",
                detail=str(e)
            ).dict()
        )