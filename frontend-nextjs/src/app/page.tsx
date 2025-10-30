'use client'

import { useState, useEffect, useCallback, useRef } from 'react'
import UploadSection from '../components/UploadSection'
import JobCard from '../components/JobCard'
import ResultModal from '../components/ResultModal'
import * as api from '../lib/api'
import type { JobStatusResponse, ProcessingResult, ParserType } from '../types'

export default function Home() {
  const [jobs, setJobs] = useState<JobStatusResponse[]>([])
  const [selectedResult, setSelectedResult] = useState<ProcessingResult | null>(null)
  const [isUploading, setIsUploading] = useState(false)
  const [message, setMessage] = useState<{ text: string; type: 'success' | 'error' } | null>(null)
  const [isLoading, setIsLoading] = useState(true)
  const jobsRef = useRef<JobStatusResponse[]>([])

  // Keep jobsRef in sync with jobs state
  useEffect(() => {
    jobsRef.current = jobs
  }, [jobs])

  // Load jobs and set up smart polling
  useEffect(() => {
    loadJobs()

    // Set up polling that checks for active jobs before each poll
    const interval = setInterval(() => {
      const hasActiveJobs = jobsRef.current.some(
        (job) => job.status === 'pending' || job.status === 'processing'
      )

      if (hasActiveJobs) {
        loadJobs()
      }
    }, 5000)

    return () => clearInterval(interval)
  }, []) // Empty deps - runs once on mount

  const loadJobs = async () => {
    try {
      const response = await api.listJobs()
      setJobs(response.jobs.sort((a: JobStatusResponse, b: JobStatusResponse) =>
        new Date(b.timestamp).getTime() - new Date(a.timestamp).getTime()
      ))
    } catch (error) {
      console.error('Failed to load jobs:', error)
    } finally {
      setIsLoading(false)
    }
  }

  const showMessage = (text: string, type: 'success' | 'error') => {
    setMessage({ text, type })
    setTimeout(() => setMessage(null), 5000)
  }

  const handleUpload = async (files: File[], parser: ParserType) => {
    setIsUploading(true)
    try {
      const results = await api.uploadFiles(files, parser)
      showMessage(
        `Successfully uploaded ${results.length} file(s). Processing started!`,
        'success'
      )
      await loadJobs()
    } catch (error) {
      showMessage(`Upload failed: ${api.getErrorMessage(error)}`, 'error')
    } finally {
      setIsUploading(false)
    }
  }

  const handleViewResult = async (jobId: string) => {
    try {
      const result = await api.getJobResult(jobId)
      setSelectedResult(result)
    } catch (error) {
      showMessage(`Failed to load result: ${api.getErrorMessage(error)}`, 'error')
    }
  }

  const handleCheckStatus = async (jobId: string) => {
    try {
      const status = await api.getJobStatus(jobId)
      showMessage(`Job status: ${status.status}`, 'success')
      await loadJobs()
    } catch (error) {
      showMessage(`Failed to check status: ${api.getErrorMessage(error)}`, 'error')
    }
  }

  const handleDelete = async (jobId: string) => {
    if (!confirm('Are you sure you want to delete this job?')) return

    try {
      await api.deleteJob(jobId)
      showMessage('Job deleted successfully', 'success')
      await loadJobs()
    } catch (error) {
      showMessage(`Failed to delete job: ${api.getErrorMessage(error)}`, 'error')
    }
  }

  const handleRefresh = async () => {
    setIsLoading(true)
    await loadJobs()
  }

  return (
    <main className="min-h-screen p-4 md:p-8">
      <div className="max-w-6xl mx-auto">
        {/* Header */}
        <header className="text-center text-white mb-8">
          <h1 className="text-4xl md:text-5xl font-bold mb-3">
            📄 PDF Processing Application
          </h1>
          <p className="text-lg md:text-xl text-blue-100">
            Upload PDFs and process them with AI-powered parsers
          </p>
        </header>

        {/* Message Banner */}
        {message && (
          <div
            className={`
              mb-6 p-4 rounded-lg shadow-lg animate-slideDown
              ${message.type === 'success'
                ? 'bg-green-100 text-green-800 border border-green-300'
                : 'bg-red-100 text-red-800 border border-red-300'
              }
            `}
          >
            {message.text}
          </div>
        )}

        {/* Upload Section */}
        <UploadSection onUpload={handleUpload} isUploading={isUploading} />

        {/* Jobs Section */}
        <div className="bg-white rounded-xl shadow-2xl p-8">
          <div className="flex justify-between items-center mb-6">
            <h2 className="text-2xl font-bold text-gray-800">Processing Jobs</h2>
            <button
              onClick={handleRefresh}
              disabled={isLoading}
              className="px-4 py-2 bg-primary text-white rounded-lg
                       hover:bg-primary-dark transition-colors font-medium
                       disabled:opacity-50 disabled:cursor-not-allowed
                       flex items-center gap-2"
            >
              <svg
                className={`h-5 w-5 ${isLoading ? 'animate-spin' : ''}`}
                fill="none"
                viewBox="0 0 24 24"
                stroke="currentColor"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15"
                />
              </svg>
              Refresh
            </button>
          </div>

          {/* Jobs List */}
          {isLoading && jobs.length === 0 ? (
            <div className="text-center py-12">
              <div className="animate-spin h-12 w-12 border-4 border-primary border-t-transparent
                            rounded-full mx-auto mb-4" />
              <p className="text-gray-600">Loading jobs...</p>
            </div>
          ) : jobs.length === 0 ? (
            <div className="text-center py-12">
              <p className="text-gray-600 text-lg">
                No jobs yet. Upload a PDF to get started!
              </p>
            </div>
          ) : (
            <div className="space-y-4">
              {jobs.map((job) => (
                <JobCard
                  key={job.job_id}
                  job={job}
                  onViewResult={handleViewResult}
                  onDelete={handleDelete}
                  onCheckStatus={handleCheckStatus}
                />
              ))}
            </div>
          )}
        </div>

        {/* Footer */}
        <footer className="text-center text-white mt-8 text-sm">
          <p className="opacity-80">
            Built with Next.js, React, TypeScript, and Tailwind CSS
          </p>
        </footer>
      </div>

      {/* Result Modal */}
      <ResultModal
        result={selectedResult}
        onClose={() => setSelectedResult(null)}
      />
    </main>
  )
}
