"""
Pydantic models for the PDF processing application.

This module defines all data models used throughout the application,
including enums for parser types and job statuses, and response models
for API endpoints.
"""

from enum import Enum
from pydantic import BaseModel, Field
from typing import List, Optional, Dict
from datetime import datetime


class ParserType(str, Enum):
    """
    Supported PDF parser types.

    - PYPDF: Fast text extraction using PyPDF library, with Gemini summary
    - GEMINI: AI-powered extraction with structured output and summary
    - MISTRAL: OCR-based extraction using Mistral AI for scanned documents
    """
    PYPDF = "pypdf"
    GEMINI = "gemini"
    MISTRAL = "mistral"


class JobStatus(str, Enum):
    """
    Job processing status lifecycle.

    - PENDING: Job created and queued, awaiting worker pickup
    - PROCESSING: Worker is actively processing the document
    - COMPLETED: Processing finished successfully
    - FAILED: Processing encountered an error
    """
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


class UploadResponse(BaseModel):
    """
    Response model for file upload endpoint.

    Returned immediately after a file is uploaded and queued for processing.
    """
    job_id: str = Field(..., description="Unique identifier for this processing job")
    status: JobStatus = Field(..., description="Current status (typically 'pending' on upload)")
    filename: str = Field(..., description="Original filename of the uploaded PDF")
    parser: ParserType = Field(..., description="Parser type selected for this job")
    timestamp: str = Field(..., description="ISO 8601 timestamp of job creation")

    class Config:
        json_schema_extra = {
            "example": {
                "job_id": "550e8400-e29b-41d4-a716-446655440000",
                "status": "pending",
                "filename": "contract.pdf",
                "parser": "gemini",
                "timestamp": "2024-01-15T10:30:00Z"
            }
        }


class JobStatusResponse(BaseModel):
    """
    Response model for job status check endpoint.

    Provides current status and metadata for a specific job.
    """
    job_id: str = Field(..., description="Unique identifier for this processing job")
    status: JobStatus = Field(..., description="Current processing status")
    filename: str = Field(..., description="Original filename of the uploaded PDF")
    parser: ParserType = Field(..., description="Parser type used for this job")
    timestamp: str = Field(..., description="ISO 8601 timestamp of job creation")
    error: Optional[str] = Field(None, description="Error message if status is 'failed'")

    class Config:
        json_schema_extra = {
            "example": {
                "job_id": "550e8400-e29b-41d4-a716-446655440000",
                "status": "processing",
                "filename": "contract.pdf",
                "parser": "gemini",
                "timestamp": "2024-01-15T10:30:00Z",
                "error": None
            }
        }


class ProcessingResult(BaseModel):
    """
    Complete result of PDF processing.

    Contains extracted content organized by page, along with an AI-generated
    summary of the entire document. Only available when job status is 'completed'.
    """
    job_id: str = Field(..., description="Unique identifier for this processing job")
    status: JobStatus = Field(..., description="Final processing status")
    filename: str = Field(..., description="Original filename of the uploaded PDF")
    parser: ParserType = Field(..., description="Parser type used for this job")
    pages: List[Dict[str, str]] = Field(
        ...,
        description="List of page objects with 'page' number and 'content' text"
    )
    summary: Optional[str] = Field(
        None,
        description="AI-generated summary of the entire document"
    )
    error: Optional[str] = Field(
        None,
        description="Error message if processing failed"
    )
    timestamp: str = Field(..., description="ISO 8601 timestamp of job creation")
    processing_time_seconds: Optional[float] = Field(
        None,
        description="Total time taken to process the document"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "job_id": "550e8400-e29b-41d4-a716-446655440000",
                "status": "completed",
                "filename": "contract.pdf",
                "parser": "gemini",
                "pages": [
                    {"page": "1", "content": "This is a sample contract..."},
                    {"page": "2", "content": "Terms and conditions..."}
                ],
                "summary": "This document outlines a service agreement between two parties...",
                "error": None,
                "timestamp": "2024-01-15T10:30:00Z",
                "processing_time_seconds": 12.5
            }
        }


class JobListResponse(BaseModel):
    """
    Response model for listing all jobs.

    Provides a paginated list of all jobs in the system.
    """
    jobs: List[JobStatusResponse] = Field(..., description="List of job status objects")
    total: int = Field(..., description="Total number of jobs in the system")

    class Config:
        json_schema_extra = {
            "example": {
                "jobs": [
                    {
                        "job_id": "550e8400-e29b-41d4-a716-446655440000",
                        "status": "completed",
                        "filename": "contract.pdf",
                        "parser": "gemini",
                        "timestamp": "2024-01-15T10:30:00Z",
                        "error": None
                    }
                ],
                "total": 1
            }
        }
