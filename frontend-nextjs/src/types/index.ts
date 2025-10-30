/**
 * Type definitions for PDF Processing Application
 * Mirrors backend Pydantic models for type safety
 */

export type ParserType = 'pypdf' | 'gemini' | 'mistral'

export type JobStatus = 'pending' | 'processing' | 'completed' | 'failed'

export interface UploadResponse {
  job_id: string
  status: JobStatus
  filename: string
  parser: ParserType
  timestamp: string
}

export interface JobStatusResponse {
  job_id: string
  status: JobStatus
  filename: string
  parser: ParserType
  timestamp: string
  error?: string | null
}

export interface ProcessingResult {
  job_id: string
  status: JobStatus
  filename: string
  parser: ParserType
  pages: Array<{
    page: string
    content: string
  }>
  summary?: string | null
  error?: string | null
  timestamp: string
  processing_time_seconds?: number | null
}

export interface JobListResponse {
  jobs: JobStatusResponse[]
  total: number
}

export interface ApiError {
  detail: string
}
