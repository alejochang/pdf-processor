"""
Async worker for processing PDF jobs.

This worker:
1. Consumes jobs from Redis Stream (XREADGROUP)
2. Processes PDFs using the appropriate parser
3. Stores results in Redis
4. Updates job status
5. Acknowledges processed messages
"""

import logging
import time
import signal
import sys
from pathlib import Path
from datetime import datetime

from .models import JobStatus, ParserType, ProcessingResult
from .config import get_settings
from .redis_client import get_redis_client
from .parsers import get_parser, validate_pdf

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Initialize settings and Redis client
settings = get_settings()
redis_client = get_redis_client()

# Global flag for graceful shutdown
shutdown_flag = False


def signal_handler(signum, frame):
    """
    Handle shutdown signals gracefully.

    This allows the worker to finish processing the current job
    before exiting.
    """
    global shutdown_flag
    logger.info(f"Received signal {signum}, initiating graceful shutdown...")
    shutdown_flag = True


# Register signal handlers
signal.signal(signal.SIGTERM, signal_handler)
signal.signal(signal.SIGINT, signal_handler)


def process_job(job_data: dict) -> None:
    """
    Process a single PDF job.

    This is the core processing function that:
    1. Updates status to PROCESSING
    2. Loads the PDF file
    3. Runs the appropriate parser
    4. Stores the result
    5. Updates status to COMPLETED or FAILED

    Args:
        job_data: Job information from Redis Stream
    """
    job_id = job_data["job_id"]
    filename = job_data["filename"]
    parser_type = job_data["parser"]
    message_id = job_data["message_id"]

    logger.info(f"Processing job {job_id} ({filename}) with {parser_type} parser")
    start_time = time.time()

    try:
        # Update status to PROCESSING
        redis_client.update_job_status(job_id, JobStatus.PROCESSING)

        # Construct PDF path
        pdf_path = Path(settings.upload_dir) / f"{job_id}.pdf"

        # Validate PDF exists
        if not validate_pdf(str(pdf_path)):
            raise FileNotFoundError(f"PDF file not found: {pdf_path}")

        # Get appropriate parser
        parser = get_parser(parser_type)

        # Parse PDF
        logger.info(f"Starting {parser_type} parsing for job {job_id}")
        pages, summary = parser.parse(str(pdf_path))

        # Calculate processing time
        processing_time = time.time() - start_time

        # Get job metadata for timestamp
        job_metadata = redis_client.get_job_status(job_id)
        timestamp = job_metadata.get("timestamp", datetime.utcnow().isoformat())

        # Create result object
        result = ProcessingResult(
            job_id=job_id,
            status=JobStatus.COMPLETED,
            filename=filename,
            parser=ParserType(parser_type),
            pages=pages,
            summary=summary,
            error=None,
            timestamp=timestamp,
            processing_time_seconds=round(processing_time, 2)
        )

        # Store result in Redis
        redis_client.store_result(result)

        # Update job status to COMPLETED
        redis_client.update_job_status(job_id, JobStatus.COMPLETED)

        logger.info(
            f"Successfully processed job {job_id} in {processing_time:.2f}s "
            f"({len(pages)} pages)"
        )

        # Optional: Clean up PDF file after successful processing
        # Uncomment to enable automatic cleanup
        # try:
        #     pdf_path.unlink()
        #     logger.info(f"Deleted PDF file for job {job_id}")
        # except Exception as e:
        #     logger.warning(f"Failed to delete PDF file for job {job_id}: {e}")

    except Exception as e:
        # Log the error
        logger.error(f"Failed to process job {job_id}: {e}", exc_info=True)

        # Update job status to FAILED with error message
        error_message = f"{type(e).__name__}: {str(e)}"
        redis_client.update_job_status(
            job_id,
            JobStatus.FAILED,
            error=error_message
        )

        # Create failed result for consistency
        try:
            job_metadata = redis_client.get_job_status(job_id)
            timestamp = job_metadata.get("timestamp", datetime.utcnow().isoformat())

            failed_result = ProcessingResult(
                job_id=job_id,
                status=JobStatus.FAILED,
                filename=filename,
                parser=ParserType(parser_type),
                pages=[],
                summary=None,
                error=error_message,
                timestamp=timestamp,
                processing_time_seconds=round(time.time() - start_time, 2)
            )
            redis_client.store_result(failed_result)
        except Exception as result_error:
            logger.error(f"Failed to store error result for job {job_id}: {result_error}")

    finally:
        # Always acknowledge the message to remove it from pending list
        try:
            redis_client.acknowledge_job(message_id)
            logger.debug(f"Acknowledged message {message_id} for job {job_id}")
        except Exception as ack_error:
            logger.error(f"Failed to acknowledge message {message_id}: {ack_error}")


def run_worker(worker_name: str = None):
    """
    Main worker loop.

    Continuously reads jobs from Redis Stream and processes them.
    Runs until shutdown signal is received.

    Args:
        worker_name: Optional custom worker name (default: from settings)
    """
    worker_name = worker_name or settings.redis_consumer_name
    logger.info(f"Starting worker: {worker_name}")

    # Ensure upload directory exists
    settings.ensure_upload_dir()

    # Create consumer group (idempotent)
    try:
        redis_client.create_consumer_group()
    except Exception as e:
        logger.error(f"Failed to create consumer group: {e}")
        sys.exit(1)

    # Validate API keys
    api_keys = settings.validate_api_keys()
    logger.info(f"Available parsers: {[k for k, v in api_keys.items() if v]}")

    # Main processing loop
    logger.info(f"Worker {worker_name} is ready and waiting for jobs...")

    while not shutdown_flag:
        try:
            # Read jobs from stream (blocking call)
            jobs = redis_client.read_jobs_from_stream(
                consumer_name=worker_name,
                count=1,  # Process one job at a time
                block_ms=settings.worker_block_time_ms
            )

            if not jobs:
                # No jobs available, continue waiting
                logger.debug("No jobs available, continuing to wait...")
                continue

            # Process each job
            for job_data in jobs:
                if shutdown_flag:
                    logger.info("Shutdown flag set, stopping job processing")
                    break

                process_job(job_data)

        except KeyboardInterrupt:
            logger.info("Received keyboard interrupt, shutting down...")
            break
        except Exception as e:
            logger.error(f"Error in worker loop: {e}", exc_info=True)
            # Sleep briefly before retrying to avoid tight error loops
            time.sleep(5)

    logger.info(f"Worker {worker_name} shutting down gracefully")


def main():
    """
    Entry point for the worker process.

    This allows the worker to be run as a standalone script.
    """
    import sys

    # Optional: Accept worker name as command line argument
    worker_name = sys.argv[1] if len(sys.argv) > 1 else None

    try:
        run_worker(worker_name)
    except Exception as e:
        logger.error(f"Worker crashed: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
