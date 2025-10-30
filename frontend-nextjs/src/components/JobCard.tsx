'use client'

import type { JobStatusResponse } from '../types'

interface JobCardProps {
  job: JobStatusResponse
  onViewResult: (jobId: string) => void
  onDelete: (jobId: string) => void
  onCheckStatus: (jobId: string) => void
}

const statusColors = {
  pending: 'bg-yellow-100 text-yellow-800',
  processing: 'bg-blue-100 text-blue-800',
  completed: 'bg-green-100 text-green-800',
  failed: 'bg-red-100 text-red-800',
}

const statusIcons = {
  pending: '⏳',
  processing: '⚙️',
  completed: '✓',
  failed: '✗',
}

export default function JobCard({
  job,
  onViewResult,
  onDelete,
  onCheckStatus,
}: JobCardProps) {
  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleString()
  }

  return (
    <div className="bg-gray-50 border-l-4 border-primary rounded-lg p-6
                    hover:shadow-md transition-all duration-200">
      {/* Header */}
      <div className="flex justify-between items-start mb-4">
        <h3 className="font-bold text-gray-800 text-lg flex-1 pr-4">
          {job.filename}
        </h3>
        <span
          className={`
            px-3 py-1 rounded-full text-xs font-bold uppercase
            ${statusColors[job.status]}
          `}
        >
          {statusIcons[job.status]} {job.status}
        </span>
      </div>

      {/* Details */}
      <div className="grid grid-cols-2 gap-3 text-sm text-gray-600 mb-4">
        <div>
          <span className="font-semibold">Job ID:</span>{' '}
          <span className="font-mono">{job.job_id.substring(0, 8)}...</span>
        </div>
        <div>
          <span className="font-semibold">Parser:</span>{' '}
          <span className="uppercase font-medium">{job.parser}</span>
        </div>
        <div className="col-span-2">
          <span className="font-semibold">Created:</span> {formatDate(job.timestamp)}
        </div>
      </div>

      {/* Error Message */}
      {job.error && (
        <div className="bg-red-50 border border-red-200 rounded-lg p-3 mb-4">
          <p className="text-sm text-red-800">
            <span className="font-semibold">Error:</span> {job.error}
          </p>
        </div>
      )}

      {/* Actions */}
      <div className="flex gap-2 flex-wrap">
        {job.status === 'completed' && (
          <button
            onClick={() => onViewResult(job.job_id)}
            className="px-4 py-2 bg-primary text-white rounded-lg
                     hover:bg-primary-dark transition-colors font-medium text-sm"
          >
            View Result
          </button>
        )}
        {(job.status === 'pending' || job.status === 'processing') && (
          <button
            onClick={() => onCheckStatus(job.job_id)}
            className="px-4 py-2 bg-blue-500 text-white rounded-lg
                     hover:bg-blue-600 transition-colors font-medium text-sm"
          >
            Check Status
          </button>
        )}
        <button
          onClick={() => onDelete(job.job_id)}
          className="px-4 py-2 bg-red-500 text-white rounded-lg
                   hover:bg-red-600 transition-colors font-medium text-sm"
        >
          Delete
        </button>
      </div>
    </div>
  )
}
