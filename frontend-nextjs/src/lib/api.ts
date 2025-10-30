// src/lib/api.ts
const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

export interface UploadResponse {
  job_id: string;
}

export interface JobStatus {
  job_id: string;
  status: 'pending' | 'processing' | 'completed' | 'failed';
  progress?: number;
  result?: {
    text: string;
    metadata: {
      filename: string;
      page_count: number;
      processing_time: number;
    };
  };
  error?: string;
}

export async function uploadFiles(files: File[], parser?: string): Promise<UploadResponse> {
  const formData = new FormData();
  files.forEach((file) => {
    formData.append('files', file);
  });

  // Add parser as query parameter if provided
  const url = parser 
    ? `${API_BASE_URL}/upload?parser=${parser}` 
    : `${API_BASE_URL}/upload`;

  const response = await fetch(url, {
    method: 'POST',
    body: formData,
  });

  if (!response.ok) {
    throw new Error(`Upload failed: ${response.statusText}`);
  }

  return response.json();
}

export async function getJobStatus(jobId: string): Promise<JobStatus> {
  const response = await fetch(`${API_BASE_URL}/status/${jobId}`);
  
  if (!response.ok) {
    throw new Error(`Failed to fetch status: ${response.statusText}`);
  }
  
  return response.json();
}

export async function getJobResult(jobId: string): Promise<any> {
  const response = await fetch(`${API_BASE_URL}/result/${jobId}`);
  
  if (!response.ok) {
    throw new Error(`Failed to fetch result: ${response.statusText}`);
  }
  
  return response.json();
}

export async function downloadResult(jobId: string): Promise<Blob> {
  const response = await fetch(`${API_BASE_URL}/download/${jobId}`);
  
  if (!response.ok) {
    throw new Error(`Download failed: ${response.statusText}`);
  }
  
  return response.blob();
}

export function getErrorMessage(error: any): string {
  if (error && typeof error === 'object' && 'message' in error) {
    return error.message;
  }
  return String(error);
}

export async function listJobs(): Promise<any> {
  const response = await fetch(`${API_BASE_URL}/jobs`);
  
  if (!response.ok) {
    throw new Error(`Failed to list jobs: ${response.statusText}`);
  }
  
  return response.json();
}

export async function deleteJob(jobId: string): Promise<void> {
  const response = await fetch(`${API_BASE_URL}/jobs/${jobId}`, {
    method: 'DELETE',
  });
  
  if (!response.ok) {
    throw new Error(`Failed to delete job: ${response.statusText}`);
  }
}
