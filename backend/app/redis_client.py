"""
Redis client and data structure operations.

This module provides a clean interface to Redis, implementing the three
core data structures used in the application:
- Stream: Job queue (pdf-jobs)
- Hash: Job metadata and status (job:{job_id})
- String: Processing results (result:{job_id})
"""

import json
import logging
from typing import Optional, Dict, List, Any
from datetime import datetime
import redis
from redis.exceptions import RedisError, ResponseError

from .models import JobStatus, ParserType, ProcessingResult
from .config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()


class RedisClient:
    """
    Redis client wrapper providing high-level operations for PDF processing.

    This class encapsulates all Redis operations needed for the job queue,
    status tracking, and result storage, following the data model:
    - Stream: pdf-jobs (job queue)
    - Hash: job:{job_id} (job metadata)
    - String: result:{job_id} (processing results)
    """

    def __init__(self):
        """
        Initialize Redis connection.

        Raises:
            RedisError: If connection to Redis fails.
        """
        try:
            self.client = redis.from_url(
                settings.redis_url,
                decode_responses=True,
                socket_connect_timeout=5
            )
            # Test connection
            self.client.ping()
            logger.info(f"Connected to Redis at {settings.redis_url}")
        except RedisError as e:
            logger.error(f"Failed to connect to Redis: {e}")
            raise

    # ========== Stream Operations (Job Queue) ==========

    def add_job_to_stream(self, job_id: str, filename: str, parser: ParserType) -> str:
        """
        Add a new job to the processing queue (Redis Stream).

        Args:
            job_id: Unique identifier for the job
            filename: Name of the uploaded PDF file
            parser: Parser type to use for processing

        Returns:
            Stream message ID

        Raises:
            RedisError: If stream operation fails
        """
        try:
            message_id = self.client.xadd(
                settings.redis_stream_name,
                {
                    "job_id": job_id,
                    "filename": filename,
                    "parser": parser.value
                }
            )
            logger.info(f"Added job {job_id} to stream with message ID {message_id}")
            return message_id
        except RedisError as e:
            logger.error(f"Failed to add job {job_id} to stream: {e}")
            raise

    def create_consumer_group(self) -> None:
        """
        Create consumer group for the worker pool.

        This should be called once on application startup. If the group
        already exists, the error is silently ignored.
        """
        try:
            self.client.xgroup_create(
                settings.redis_stream_name,
                settings.redis_consumer_group,
                id='0',
                mkstream=True
            )
            logger.info(f"Created consumer group '{settings.redis_consumer_group}'")
        except ResponseError as e:
            if "BUSYGROUP" in str(e):
                logger.info(f"Consumer group '{settings.redis_consumer_group}' already exists")
            else:
                raise

    def read_jobs_from_stream(
        self,
        consumer_name: str,
        count: int = 1,
        block_ms: int = 5000
    ) -> List[Dict[str, Any]]:
        """
        Read jobs from stream using consumer group (blocking).

        This is the main method used by workers to consume jobs from the queue.
        It blocks until jobs are available or timeout is reached.

        Args:
            consumer_name: Unique name for this consumer
            count: Number of messages to read at once
            block_ms: Time to block waiting for messages (milliseconds)

        Returns:
            List of job dictionaries with 'message_id', 'job_id', 'filename', 'parser'

        Raises:
            RedisError: If stream read operation fails
        """
        try:
            # XREADGROUP: Read from stream as part of consumer group
            # Format: {stream_name: [(message_id, {field: value, ...}), ...]}
            streams = self.client.xreadgroup(
                groupname=settings.redis_consumer_group,
                consumername=consumer_name,
                streams={settings.redis_stream_name: '>'},
                count=count,
                block=block_ms
            )

            if not streams:
                return []

            # Parse stream response
            jobs = []
            for stream_name, messages in streams:
                for message_id, data in messages:
                    jobs.append({
                        "message_id": message_id,
                        "job_id": data.get("job_id"),
                        "filename": data.get("filename"),
                        "parser": data.get("parser")
                    })

            logger.debug(f"Read {len(jobs)} job(s) from stream")
            return jobs

        except RedisError as e:
            logger.error(f"Failed to read from stream: {e}")
            raise

    def acknowledge_job(self, message_id: str) -> None:
        """
        Acknowledge job completion (XACK).

        This removes the message from the consumer's pending list after
        successful processing.

        Args:
            message_id: Stream message ID to acknowledge

        Raises:
            RedisError: If acknowledgment fails
        """
        try:
            self.client.xack(
                settings.redis_stream_name,
                settings.redis_consumer_group,
                message_id
            )
            logger.debug(f"Acknowledged message {message_id}")
        except RedisError as e:
            logger.error(f"Failed to acknowledge message {message_id}: {e}")
            raise

    # ========== Hash Operations (Job Metadata) ==========

    def create_job_hash(
        self,
        job_id: str,
        filename: str,
        parser: ParserType,
        status: JobStatus = JobStatus.PENDING
    ) -> None:
        """
        Create job metadata hash (job:{job_id}).

        This is the single source of truth for job status and metadata.

        Args:
            job_id: Unique identifier for the job
            filename: Name of the uploaded PDF file
            parser: Parser type to use
            status: Initial job status (default: PENDING)

        Raises:
            RedisError: If hash creation fails
        """
        try:
            key = f"job:{job_id}"
            self.client.hset(
                key,
                mapping={
                    "status": status.value,
                    "filename": filename,
                    "parser": parser.value,
                    "timestamp": datetime.utcnow().isoformat(),
                    "error": ""
                }
            )
            logger.info(f"Created job hash for {job_id}")
        except RedisError as e:
            logger.error(f"Failed to create job hash for {job_id}: {e}")
            raise

    def get_job_status(self, job_id: str) -> Optional[Dict[str, str]]:
        """
        Get job metadata from hash.

        Args:
            job_id: Unique identifier for the job

        Returns:
            Dictionary with job metadata, or None if job doesn't exist

        Raises:
            RedisError: If hash read fails
        """
        try:
            key = f"job:{job_id}"
            data = self.client.hgetall(key)

            if not data:
                logger.warning(f"Job {job_id} not found")
                return None

            return data
        except RedisError as e:
            logger.error(f"Failed to get job status for {job_id}: {e}")
            raise

    def update_job_status(
        self,
        job_id: str,
        status: JobStatus,
        error: Optional[str] = None
    ) -> None:
        """
        Update job status in hash.

        Args:
            job_id: Unique identifier for the job
            status: New job status
            error: Optional error message (for FAILED status)

        Raises:
            RedisError: If hash update fails
        """
        try:
            key = f"job:{job_id}"
            updates = {"status": status.value}

            if error:
                updates["error"] = error

            self.client.hset(key, mapping=updates)
            logger.info(f"Updated job {job_id} status to {status.value}")
        except RedisError as e:
            logger.error(f"Failed to update job status for {job_id}: {e}")
            raise

    def get_all_jobs(self) -> List[Dict[str, str]]:
        """
        Get all job metadata from Redis.

        Scans for all job:* keys and retrieves their metadata.

        Returns:
            List of job metadata dictionaries

        Raises:
            RedisError: If scan operation fails
        """
        try:
            jobs = []
            # Use SCAN to iterate through keys safely
            for key in self.client.scan_iter(match="job:*", count=100):
                job_data = self.client.hgetall(key)
                if job_data:
                    job_id = key.split(":", 1)[1]
                    job_data["job_id"] = job_id
                    jobs.append(job_data)

            logger.debug(f"Retrieved {len(jobs)} jobs")
            return jobs
        except RedisError as e:
            logger.error(f"Failed to get all jobs: {e}")
            raise

    # ========== String Operations (Processing Results) ==========

    def store_result(self, result: ProcessingResult) -> None:
        """
        Store processing result (result:{job_id}).

        The result is stored as a JSON string with a TTL to prevent
        unbounded growth of result data.

        Args:
            result: Complete processing result

        Raises:
            RedisError: If result storage fails
        """
        try:
            key = f"result:{result.job_id}"
            result_json = result.model_dump_json()

            # Store with TTL
            self.client.setex(
                key,
                settings.redis_result_ttl_seconds,
                result_json
            )
            logger.info(
                f"Stored result for job {result.job_id} "
                f"(TTL: {settings.redis_result_ttl_seconds}s)"
            )
        except RedisError as e:
            logger.error(f"Failed to store result for {result.job_id}: {e}")
            raise

    def get_result(self, job_id: str) -> Optional[ProcessingResult]:
        """
        Get processing result from Redis.

        Args:
            job_id: Unique identifier for the job

        Returns:
            ProcessingResult object, or None if result doesn't exist or expired

        Raises:
            RedisError: If result retrieval fails
        """
        try:
            key = f"result:{job_id}"
            result_json = self.client.get(key)

            if not result_json:
                logger.warning(f"Result for job {job_id} not found or expired")
                return None

            return ProcessingResult.model_validate_json(result_json)
        except RedisError as e:
            logger.error(f"Failed to get result for {job_id}: {e}")
            raise
        except Exception as e:
            logger.error(f"Failed to parse result for {job_id}: {e}")
            raise

    # ========== Utility Methods ==========

    def delete_job(self, job_id: str) -> None:
        """
        Delete job metadata and result from Redis.

        This is useful for cleanup operations.

        Args:
            job_id: Unique identifier for the job

        Raises:
            RedisError: If deletion fails
        """
        try:
            self.client.delete(f"job:{job_id}", f"result:{job_id}")
            logger.info(f"Deleted job {job_id} and its result")
        except RedisError as e:
            logger.error(f"Failed to delete job {job_id}: {e}")
            raise

    def health_check(self) -> bool:
        """
        Check Redis connection health.

        Returns:
            True if Redis is healthy, False otherwise
        """
        try:
            return self.client.ping()
        except RedisError:
            return False


# Global Redis client instance
_redis_client: Optional[RedisClient] = None


def get_redis_client() -> RedisClient:
    """
    Get global Redis client instance.

    This ensures a single Redis connection is reused across the application.

    Returns:
        RedisClient instance
    """
    global _redis_client
    if _redis_client is None:
        _redis_client = RedisClient()
    return _redis_client
