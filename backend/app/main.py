"""
FastAPI application for PDF processing.

This module provides the REST API endpoints for:
- Uploading PDF files for processing
- Checking job status
- Retrieving processing results
- Listing all jobs
"""

import logging
import os
import uuid
from datetime import datetime
from pathlib import Path
from typing import List

from fastapi import FastAPI, File, UploadFile, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles

from .models import (
    ParserType,
    JobStatus,
    UploadResponse,
    JobStatusResponse,
    ProcessingResult,
    JobListResponse
)
from .config import get_settings
from .redis_client import get_redis_client

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Initialize settings and Redis client
settings = get_settings()
redis_client = get_redis_client()

# Create FastAPI app
app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description="Async PDF processing API with multiple parser options"
)

# Add CORS middleware for frontend access
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ========== Startup & Shutdown Events ==========

@app.on_event("startup")
async def startup_event():
    """
    Initialize application on startup.

    - Create upload directory
    - Create Redis consumer group
    - Validate API keys
    """
    logger.info(f"Starting {settings.app_name} v{settings.app_version}")

    # Ensure upload directory exists
    settings.ensure_upload_dir()
    logger.info(f"Upload directory: {settings.upload_dir}")

    # Create Redis consumer group
    try:
        redis_client.create_consumer_group()
    except Exception as e:
        logger.error(f"Failed to create consumer group: {e}")

    # Check API key availability
    api_keys = settings.validate_api_keys()
    logger.info(f"Available parsers: {[k for k, v in api_keys.items() if v]}")
    if not any(api_keys.values()):
        logger.warning("No API keys configured! Only PyPDF basic extraction will work.")


@app.on_event("shutdown")
async def shutdown_event():
    """Clean up resources on shutdown."""
    logger.info("Shutting down application")


# ========== Health Check Endpoint ==========

@app.get("/health")
async def health_check():
    """
    Health check endpoint.

    Returns:
        Status of the application and its dependencies
    """
    redis_healthy = redis_client.health_check()

    return {
        "status": "healthy" if redis_healthy else "degraded",
        "redis": "connected" if redis_healthy else "disconnected",
        "version": settings.app_version
    }


# ========== Upload Endpoint ==========

@app.post("/api/upload", response_model=List[UploadResponse])
async def upload_files(
    files: List[UploadFile] = File(...),
    parser: ParserType = Query(ParserType.PYPDF, description="Parser type to use")
):
    """
    Upload one or more PDF files for processing.

    Args:
        files: List of PDF files to upload
        parser: Parser type (pypdf, gemini, or mistral)

    Returns:
        List of UploadResponse objects with job IDs and status

    Raises:
        HTTPException: If file validation fails
    """
    logger.info(f"Received {len(files)} file(s) for upload with parser: {parser.value}")

    responses = []
    max_size_bytes = settings.get_max_file_size_bytes()

    for file in files:
        try:
            # Validate file
            if not file.filename.endswith('.pdf'):
                raise HTTPException(
                    status_code=400,
                    detail=f"File {file.filename} is not a PDF"
                )

            # Read file content
            content = await file.read()
            file_size_mb = len(content) / (1024 * 1024)

            if len(content) > max_size_bytes:
                raise HTTPException(
                    status_code=400,
                    detail=f"File {file.filename} exceeds maximum size of "
                           f"{settings.max_file_size_mb}MB (actual: {file_size_mb:.2f}MB)"
                )

            # Generate unique job ID
            job_id = str(uuid.uuid4())
            timestamp = datetime.utcnow().isoformat()

            # Save file to upload directory
            file_path = Path(settings.upload_dir) / f"{job_id}.pdf"
            with open(file_path, "wb") as f:
                f.write(content)

            logger.info(
                f"Saved file {file.filename} as {file_path} "
                f"({file_size_mb:.2f}MB)"
            )

            # Create job hash in Redis
            redis_client.create_job_hash(
                job_id=job_id,
                filename=file.filename,
                parser=parser,
                status=JobStatus.PENDING
            )

            # Add job to processing queue (Redis Stream)
            redis_client.add_job_to_stream(
                job_id=job_id,
                filename=file.filename,
                parser=parser
            )

            # Add to response list
            responses.append(UploadResponse(
                job_id=job_id,
                status=JobStatus.PENDING,
                filename=file.filename,
                parser=parser,
                timestamp=timestamp
            ))

            logger.info(f"Job {job_id} created and queued for processing")

        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Failed to process upload for {file.filename}: {e}")
            raise HTTPException(
                status_code=500,
                detail=f"Failed to process {file.filename}: {str(e)}"
            )

    return responses


# ========== Status Check Endpoint ==========

@app.get("/api/status/{job_id}", response_model=JobStatusResponse)
async def get_job_status(job_id: str):
    """
    Get the current status of a processing job.

    Args:
        job_id: Unique job identifier

    Returns:
        JobStatusResponse with current status and metadata

    Raises:
        HTTPException: If job is not found
    """
    logger.debug(f"Checking status for job {job_id}")

    try:
        job_data = redis_client.get_job_status(job_id)

        if not job_data:
            raise HTTPException(
                status_code=404,
                detail=f"Job {job_id} not found"
            )

        return JobStatusResponse(
            job_id=job_id,
            status=JobStatus(job_data["status"]),
            filename=job_data["filename"],
            parser=ParserType(job_data["parser"]),
            timestamp=job_data["timestamp"],
            error=job_data.get("error") or None
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get status for job {job_id}: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get job status: {str(e)}"
        )


# ========== Result Retrieval Endpoint ==========

@app.get("/api/result/{job_id}", response_model=ProcessingResult)
async def get_job_result(job_id: str):
    """
    Get the processing result for a completed job.

    Args:
        job_id: Unique job identifier

    Returns:
        ProcessingResult with extracted pages and summary

    Raises:
        HTTPException: If job is not found or not completed
    """
    logger.debug(f"Retrieving result for job {job_id}")

    try:
        # First check job status
        job_data = redis_client.get_job_status(job_id)

        if not job_data:
            raise HTTPException(
                status_code=404,
                detail=f"Job {job_id} not found"
            )

        status = JobStatus(job_data["status"])

        # Check if job is completed
        if status == JobStatus.PENDING:
            raise HTTPException(
                status_code=202,
                detail="Job is pending processing"
            )
        elif status == JobStatus.PROCESSING:
            raise HTTPException(
                status_code=202,
                detail="Job is currently being processed"
            )
        elif status == JobStatus.FAILED:
            raise HTTPException(
                status_code=500,
                detail=f"Job failed: {job_data.get('error', 'Unknown error')}"
            )

        # Get result from Redis
        result = redis_client.get_result(job_id)

        if not result:
            raise HTTPException(
                status_code=404,
                detail="Job result not found or expired"
            )

        logger.info(f"Retrieved result for job {job_id}")
        return result

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get result for job {job_id}: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get job result: {str(e)}"
        )


# ========== Job List Endpoint ==========

@app.get("/api/jobs", response_model=JobListResponse)
async def list_all_jobs():
    """
    List all jobs in the system.

    Returns:
        JobListResponse with list of all jobs and total count
    """
    logger.debug("Listing all jobs")

    try:
        jobs_data = redis_client.get_all_jobs()

        jobs = [
            JobStatusResponse(
                job_id=job["job_id"],
                status=JobStatus(job["status"]),
                filename=job["filename"],
                parser=ParserType(job["parser"]),
                timestamp=job["timestamp"],
                error=job.get("error") or None
            )
            for job in jobs_data
        ]

        return JobListResponse(
            jobs=jobs,
            total=len(jobs)
        )

    except Exception as e:
        logger.error(f"Failed to list jobs: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to list jobs: {str(e)}"
        )


# ========== Delete Job Endpoint (Utility) ==========

@app.delete("/api/jobs/{job_id}")
async def delete_job(job_id: str):
    """
    Delete a job and its result from the system.

    This is useful for cleanup operations.

    Args:
        job_id: Unique job identifier

    Returns:
        Success message
    """
    logger.info(f"Deleting job {job_id}")

    try:
        # Check if job exists
        job_data = redis_client.get_job_status(job_id)

        if not job_data:
            raise HTTPException(
                status_code=404,
                detail=f"Job {job_id} not found"
            )

        # Delete from Redis
        redis_client.delete_job(job_id)

        # Delete PDF file if it exists
        file_path = Path(settings.upload_dir) / f"{job_id}.pdf"
        if file_path.exists():
            file_path.unlink()
            logger.info(f"Deleted PDF file for job {job_id}")

        return {"message": f"Job {job_id} deleted successfully"}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to delete job {job_id}: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to delete job: {str(e)}"
        )


# ========== Root Endpoint ==========

@app.get("/")
async def root():
    """
    Root endpoint with API information.

    Returns:
        API information and available endpoints
    """
    return {
        "name": settings.app_name,
        "version": settings.app_version,
        "endpoints": {
            "health": "/health",
            "upload": "POST /api/upload",
            "status": "GET /api/status/{job_id}",
            "result": "GET /api/result/{job_id}",
            "jobs": "GET /api/jobs",
            "delete": "DELETE /api/jobs/{job_id}"
        },
        "parsers": ["pypdf", "gemini", "mistral"]
    }


# ========== Exception Handlers ==========

@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    """
    Global exception handler for unhandled errors.

    This ensures all errors are logged and returned in a consistent format.
    """
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error"}
    )
