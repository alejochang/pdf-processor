'use client'

import { useState, useCallback } from 'react'
import type { ParserType } from '../types'

interface UploadSectionProps {
  onUpload: (files: File[], parser: ParserType) => Promise<void>
  isUploading: boolean
}

export default function UploadSection({ onUpload, isUploading }: UploadSectionProps) {
  const [selectedFiles, setSelectedFiles] = useState<File[]>([])
  const [parser, setParser] = useState<ParserType>('gemini')
  const [isDragOver, setIsDragOver] = useState(false)

  const handleFileSelect = (files: FileList | null) => {
    if (!files) return
    const pdfFiles = Array.from(files).filter(
      (file) => file.type === 'application/pdf' || file.name.endsWith('.pdf')
    )
    setSelectedFiles(pdfFiles)
  }

  const handleDragOver = useCallback((e: React.DragEvent) => {
    e.preventDefault()
    setIsDragOver(true)
  }, [])

  const handleDragLeave = useCallback((e: React.DragEvent) => {
    e.preventDefault()
    setIsDragOver(false)
  }, [])

  const handleDrop = useCallback((e: React.DragEvent) => {
    e.preventDefault()
    setIsDragOver(false)
    handleFileSelect(e.dataTransfer.files)
  }, [])

  const handleUploadClick = async () => {
    if (selectedFiles.length === 0) return
    await onUpload(selectedFiles, parser)
    setSelectedFiles([])
  }

  return (
    <div className="bg-white rounded-xl shadow-2xl p-8 mb-6">
      <h2 className="text-2xl font-bold text-gray-800 mb-6">Upload PDF Files</h2>

      {/* Upload Area */}
      <div
        className={`
          border-3 border-dashed rounded-lg p-12 text-center cursor-pointer
          transition-all duration-200
          ${isDragOver
            ? 'border-primary bg-blue-50'
            : 'border-gray-300 hover:border-primary hover:bg-gray-50'
          }
        `}
        onDragOver={handleDragOver}
        onDragLeave={handleDragLeave}
        onDrop={handleDrop}
        onClick={() => document.getElementById('fileInput')?.click()}
      >
        <svg
          className="mx-auto h-16 w-16 text-primary mb-4"
          fill="none"
          viewBox="0 0 24 24"
          stroke="currentColor"
        >
          <path
            strokeLinecap="round"
            strokeLinejoin="round"
            strokeWidth={2}
            d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12"
          />
        </svg>
        <p className="text-lg font-semibold text-gray-700 mb-2">
          {selectedFiles.length > 0
            ? `${selectedFiles.length} file(s) selected`
            : 'Click to select or drag and drop PDF files here'}
        </p>
        <p className="text-sm text-gray-500">
          {selectedFiles.length > 0
            ? selectedFiles.map((f) => f.name).join(', ')
            : 'PDF files only'}
        </p>
        <input
          id="fileInput"
          type="file"
          accept=".pdf,application/pdf"
          multiple
          className="hidden"
          onChange={(e) => handleFileSelect(e.target.files)}
        />
      </div>

      {/* Parser Selection */}
      <div className="mt-6">
        <label className="block text-sm font-semibold text-gray-700 mb-2">
          Select Parser:
        </label>
        <select
          value={parser}
          onChange={(e) => setParser(e.target.value as ParserType)}
          className="w-full px-4 py-3 border-2 border-gray-300 rounded-lg
                   focus:outline-none focus:border-primary transition-colors
                   text-gray-700 font-medium"
        >
          <option value="pypdf">PyPDF (Fast Text Extraction)</option>
          <option value="gemini">Gemini (AI-Powered - Recommended)</option>
          <option value="mistral">Mistral (OCR for Scanned Documents)</option>
        </select>
      </div>

      {/* Upload Button */}
      <button
        onClick={handleUploadClick}
        disabled={selectedFiles.length === 0 || isUploading}
        className="w-full mt-6 px-6 py-4 bg-gradient-to-r from-primary to-primary-dark
                 text-white font-bold rounded-lg shadow-lg
                 hover:shadow-xl hover:scale-[1.02] active:scale-[0.98]
                 disabled:opacity-50 disabled:cursor-not-allowed disabled:transform-none
                 transition-all duration-200"
      >
        {isUploading ? (
          <span className="flex items-center justify-center">
            <svg className="animate-spin h-5 w-5 mr-3" viewBox="0 0 24 24">
              <circle
                className="opacity-25"
                cx="12"
                cy="12"
                r="10"
                stroke="currentColor"
                strokeWidth="4"
                fill="none"
              />
              <path
                className="opacity-75"
                fill="currentColor"
                d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
              />
            </svg>
            Uploading...
          </span>
        ) : (
          'Upload and Process'
        )}
      </button>
    </div>
  )
}
