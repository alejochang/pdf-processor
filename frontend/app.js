// PDF Processing Application - Frontend JavaScript

// Configuration
const API_BASE_URL = 'http://localhost:8000';

// State
let selectedFiles = [];
let jobs = [];
let autoRefreshInterval = null;

// DOM Elements
const uploadArea = document.getElementById('uploadArea');
const fileInput = document.getElementById('fileInput');
const parserSelect = document.getElementById('parserSelect');
const uploadBtn = document.getElementById('uploadBtn');
const uploadMessage = document.getElementById('uploadMessage');
const jobsList = document.getElementById('jobsList');
const refreshBtn = document.getElementById('refreshBtn');
const resultModal = document.getElementById('resultModal');
const closeModal = document.getElementById('closeModal');
const resultContent = document.getElementById('resultContent');

// Initialize
document.addEventListener('DOMContentLoaded', () => {
    setupEventListeners();
    loadJobs();
    startAutoRefresh();
});

// Event Listeners
function setupEventListeners() {
    // Upload area click
    uploadArea.addEventListener('click', () => fileInput.click());

    // File input change
    fileInput.addEventListener('change', handleFileSelect);

    // Drag and drop
    uploadArea.addEventListener('dragover', (e) => {
        e.preventDefault();
        uploadArea.classList.add('dragover');
    });

    uploadArea.addEventListener('dragleave', () => {
        uploadArea.classList.remove('dragover');
    });

    uploadArea.addEventListener('drop', (e) => {
        e.preventDefault();
        uploadArea.classList.remove('dragover');
        const files = Array.from(e.dataTransfer.files).filter(f => f.name.endsWith('.pdf'));
        if (files.length > 0) {
            fileInput.files = createFileList(files);
            handleFileSelect();
        }
    });

    // Upload button
    uploadBtn.addEventListener('click', handleUpload);

    // Refresh button
    refreshBtn.addEventListener('click', loadJobs);

    // Close modal
    closeModal.addEventListener('click', () => {
        resultModal.style.display = 'none';
    });

    // Click outside modal to close
    resultModal.addEventListener('click', (e) => {
        if (e.target === resultModal) {
            resultModal.style.display = 'none';
        }
    });
}

// File Selection
function handleFileSelect() {
    selectedFiles = Array.from(fileInput.files);

    if (selectedFiles.length > 0) {
        uploadBtn.disabled = false;
        const fileNames = selectedFiles.map(f => f.name).join(', ');
        showMessage(`Selected: ${fileNames}`, 'success');
    } else {
        uploadBtn.disabled = true;
    }
}

// Create FileList (helper for drag and drop)
function createFileList(files) {
    const dataTransfer = new DataTransfer();
    files.forEach(file => dataTransfer.items.add(file));
    return dataTransfer.files;
}

// Upload Files
async function handleUpload() {
    if (selectedFiles.length === 0) return;

    uploadBtn.disabled = true;
    showMessage('Uploading files...', 'info');

    try {
        const formData = new FormData();
        selectedFiles.forEach(file => {
            formData.append('files', file);
        });

        const parser = parserSelect.value;
        const response = await fetch(`${API_BASE_URL}/api/upload?parser=${parser}`, {
            method: 'POST',
            body: formData
        });

        if (!response.ok) {
            throw new Error(`Upload failed: ${response.statusText}`);
        }

        const results = await response.json();

        showMessage(
            `Successfully uploaded ${results.length} file(s). Processing started!`,
            'success'
        );

        // Clear selection
        fileInput.value = '';
        selectedFiles = [];
        uploadBtn.disabled = true;

        // Refresh jobs list
        setTimeout(loadJobs, 1000);

    } catch (error) {
        showMessage(`Error: ${error.message}`, 'error');
        uploadBtn.disabled = false;
    }
}

// Load Jobs
async function loadJobs() {
    try {
        const response = await fetch(`${API_BASE_URL}/api/jobs`);

        if (!response.ok) {
            throw new Error('Failed to load jobs');
        }

        const data = await response.json();
        jobs = data.jobs;

        renderJobs();

    } catch (error) {
        jobsList.innerHTML = `
            <div class="error-message">
                Failed to load jobs: ${error.message}
            </div>
        `;
    }
}

// Render Jobs
function renderJobs() {
    if (jobs.length === 0) {
        jobsList.innerHTML = `
            <div class="loading">
                <p>No jobs yet. Upload a PDF to get started!</p>
            </div>
        `;
        return;
    }

    // Sort by timestamp (newest first)
    const sortedJobs = [...jobs].sort((a, b) =>
        new Date(b.timestamp) - new Date(a.timestamp)
    );

    jobsList.innerHTML = sortedJobs.map(job => `
        <div class="job-card">
            <div class="job-header">
                <div class="job-filename">${escapeHtml(job.filename)}</div>
                <span class="status-badge status-${job.status}">${job.status}</span>
            </div>

            <div class="job-details">
                <div><strong>Job ID:</strong> ${job.job_id.substring(0, 8)}...</div>
                <div><strong>Parser:</strong> ${job.parser.toUpperCase()}</div>
                <div><strong>Created:</strong> ${formatDate(job.timestamp)}</div>
            </div>

            ${job.error ? `
                <div class="error-message" style="margin-top: 10px;">
                    <strong>Error:</strong> ${escapeHtml(job.error)}
                </div>
            ` : ''}

            <div class="job-actions">
                ${job.status === 'completed' ? `
                    <button class="btn-small" onclick="viewResult('${job.job_id}')">
                        View Result
                    </button>
                ` : ''}
                ${job.status === 'pending' || job.status === 'processing' ? `
                    <button class="btn-small" onclick="checkStatus('${job.job_id}')">
                        Check Status
                    </button>
                ` : ''}
                <button class="btn-small btn-danger" onclick="deleteJob('${job.job_id}')">
                    Delete
                </button>
            </div>
        </div>
    `).join('');
}

// View Result
async function viewResult(jobId) {
    try {
        resultContent.innerHTML = `
            <div class="loading">
                <div class="spinner"></div>
                <p>Loading result...</p>
            </div>
        `;
        resultModal.style.display = 'block';

        const response = await fetch(`${API_BASE_URL}/api/result/${jobId}`);

        if (!response.ok) {
            throw new Error('Failed to load result');
        }

        const result = await response.json();

        resultContent.innerHTML = `
            <h2>📄 Processing Result</h2>

            <div class="job-details" style="margin: 20px 0;">
                <div><strong>Filename:</strong> ${escapeHtml(result.filename)}</div>
                <div><strong>Parser:</strong> ${result.parser.toUpperCase()}</div>
                <div><strong>Pages:</strong> ${result.pages.length}</div>
                <div><strong>Processing Time:</strong> ${result.processing_time_seconds}s</div>
            </div>

            ${result.summary ? `
                <div class="summary-section">
                    <h3>📝 Summary</h3>
                    <p>${escapeHtml(result.summary)}</p>
                </div>
            ` : ''}

            <h3 style="margin-top: 30px;">📖 Page Content</h3>
            ${result.pages.map(page => `
                <div class="page-content">
                    <h4>Page ${page.page}</h4>
                    <p>${escapeHtml(page.content).replace(/\n/g, '<br>')}</p>
                </div>
            `).join('')}
        `;

    } catch (error) {
        resultContent.innerHTML = `
            <div class="error-message">
                Failed to load result: ${error.message}
            </div>
        `;
    }
}

// Check Status
async function checkStatus(jobId) {
    try {
        const response = await fetch(`${API_BASE_URL}/api/status/${jobId}`);

        if (!response.ok) {
            throw new Error('Failed to check status');
        }

        const status = await response.json();

        alert(`Job Status: ${status.status}\nFilename: ${status.filename}\nParser: ${status.parser}`);

        // Refresh jobs list
        loadJobs();

    } catch (error) {
        alert(`Error: ${error.message}`);
    }
}

// Delete Job
async function deleteJob(jobId) {
    if (!confirm('Are you sure you want to delete this job?')) {
        return;
    }

    try {
        const response = await fetch(`${API_BASE_URL}/api/jobs/${jobId}`, {
            method: 'DELETE'
        });

        if (!response.ok) {
            throw new Error('Failed to delete job');
        }

        showMessage('Job deleted successfully', 'success');

        // Refresh jobs list
        loadJobs();

    } catch (error) {
        showMessage(`Error: ${error.message}`, 'error');
    }
}

// Auto Refresh
function startAutoRefresh() {
    // Refresh every 5 seconds if there are pending or processing jobs
    autoRefreshInterval = setInterval(() => {
        const hasActiveJobs = jobs.some(job =>
            job.status === 'pending' || job.status === 'processing'
        );

        if (hasActiveJobs) {
            loadJobs();
        }
    }, 5000);
}

// Show Message
function showMessage(text, type) {
    const className = type === 'error' ? 'error-message' : 'success-message';
    uploadMessage.innerHTML = `<div class="${className}">${text}</div>`;

    // Clear after 5 seconds
    setTimeout(() => {
        uploadMessage.innerHTML = '';
    }, 5000);
}

// Utility Functions
function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

function formatDate(dateString) {
    const date = new Date(dateString);
    return date.toLocaleString();
}

// Make functions globally accessible
window.viewResult = viewResult;
window.checkStatus = checkStatus;
window.deleteJob = deleteJob;
