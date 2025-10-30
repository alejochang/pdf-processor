'use client'

import { useEffect } from 'react'
import type { ProcessingResult } from '@/types'

interface ResultModalProps {
  result: ProcessingResult | null
  onClose: () => void
}

export default function ResultModal({ result, onClose }: ResultModalProps) {
  // Close modal on Escape key
  useEffect(() => {
    const handleEscape = (e: KeyboardEvent) => {
      if (e.key === 'Escape') onClose()
    }
    window.addEventListener('keydown', handleEscape)
    return () => window.removeEventListener('keydown', handleEscape)
  }, [onClose])

  if (!result) return null

  return (
    <div
      className="fixed inset-0 bg-black bg-opacity-50 z-50 flex items-center justify-center p-4
                 animate-fadeIn"
      onClick={onClose}
    >
      <div
        className="bg-white rounded-xl max-w-4xl w-full max-h-[90vh] overflow-hidden
                   shadow-2xl animate-slideUp"
        onClick={(e) => e.stopPropagation()}
      >
        {/* Header */}
        <div className="bg-gradient-to-r from-primary to-primary-dark text-white p-6">
          <div className="flex justify-between items-start">
            <div>
              <h2 className="text-2xl font-bold mb-2">📄 Processing Result</h2>
              <p className="text-blue-100">{result.filename}</p>
            </div>
            <button
              onClick={onClose}
              className="text-white hover:text-gray-200 text-3xl font-bold
                       transition-colors"
              aria-label="Close"
            >
              ×
            </button>
          </div>
        </div>

        {/* Content */}
        <div className="p-6 overflow-y-auto max-h-[calc(90vh-120px)]">
          {/* Metadata */}
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6 text-sm">
            <div className="bg-gray-50 p-3 rounded-lg">
              <p className="text-gray-600 font-semibold">Parser</p>
              <p className="text-gray-900 uppercase font-bold">{result.parser}</p>
            </div>
            <div className="bg-gray-50 p-3 rounded-lg">
              <p className="text-gray-600 font-semibold">Pages</p>
              <p className="text-gray-900 font-bold">{result.pages.length}</p>
            </div>
            <div className="bg-gray-50 p-3 rounded-lg">
              <p className="text-gray-600 font-semibold">Status</p>
              <p className="text-green-600 font-bold uppercase">{result.status}</p>
            </div>
            {result.processing_time_seconds && (
              <div className="bg-gray-50 p-3 rounded-lg">
                <p className="text-gray-600 font-semibold">Processing Time</p>
                <p className="text-gray-900 font-bold">
                  {result.processing_time_seconds.toFixed(1)}s
                </p>
              </div>
            )}
          </div>

          {/* Summary */}
          {result.summary && (
            <div className="bg-green-50 border-l-4 border-green-500 p-6 rounded-lg mb-6">
              <h3 className="text-lg font-bold text-gray-800 mb-3 flex items-center">
                📝 Summary
              </h3>
              <p className="text-gray-700 leading-relaxed">{result.summary}</p>
            </div>
          )}

          {/* Page Content */}
          <div>
            <h3 className="text-lg font-bold text-gray-800 mb-4 flex items-center">
              📖 Page Content
            </h3>
            <div className="space-y-4">
              {result.pages.map((page) => (
                <div
                  key={page.page}
                  className="bg-gray-50 border-l-4 border-primary p-6 rounded-lg"
                >
                  <h4 className="font-bold text-primary mb-3">Page {page.page}</h4>
                  <div className="text-gray-700 whitespace-pre-wrap leading-relaxed">
                    {page.content}
                  </div>
                </div>
              ))}
            </div>
          </div>

          {/* Error */}
          {result.error && (
            <div className="bg-red-50 border-l-4 border-red-500 p-6 rounded-lg mt-6">
              <h3 className="text-lg font-bold text-red-800 mb-2">Error</h3>
              <p className="text-red-700">{result.error}</p>
            </div>
          )}
        </div>
      </div>
    </div>
  )
}
