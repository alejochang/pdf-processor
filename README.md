# PDF Processing Application

An async PDF processing system with multiple AI-powered parser options, built with FastAPI, Redis Streams, and modern web technologies.

## 🌟 Features

- **Multiple Parser Options**:
  - **PyPDF**: Fast text extraction with AI-generated summaries
  - **Gemini**: Full AI-powered extraction with structured output
  - **Mistral**: OCR-based extraction (experimental)

- **Async Processing**: Jobs are queued and processed asynchronously using Redis Streams
- **Real-time Status**: Track job status from pending → processing → completed
- **Web UI**: Simple, intuitive interface for uploading and monitoring jobs
- **REST API**: Complete API for programmatic access
- **Docker-based**: Easy deployment with Docker Compose

## 🏗️ Architecture

```
┌─────────────┐      ┌─────────────┐      ┌─────────────┐
│   Frontend  │─────▶│   Backend   │─────▶│    Redis    │
│  (Nginx)    │      │  (FastAPI)  │      │  (Streams)  │
└─────────────┘      └─────────────┘      └─────────────┘
                            │                      │
                            │                      ▼
                            │              ┌─────────────┐
                            └─────────────▶│   Worker    │
                                           │  (Python)   │
                                           └─────────────┘
```

### Data Structures

1. **Redis Stream** (`pdf-jobs`): Job queue with consumer groups
2. **Redis Hash** (`job:{job_id}`): Job metadata and status
3. **Redis String** (`result:{job_id}`): Processing results (with TTL)

## 📋 Prerequisites

- Docker & Docker Compose
- Google Gemini API key
- (Optional) Mistral API key

## 🚀 Quick Start

### 1. Clone and Setup

```bash
cd pdf-processor
```

### 2. Configure Environment

The `.env` file is already configured with your Gemini API key. If you need to modify settings:

```bash
# Edit .env file
GOOGLE_API_KEY=AIzaSyDxQWdpHhxe0SckdBArq19pStScZc7iMK0
MISTRAL_API_KEY=your_mistral_key_here  # Optional
MAX_FILE_SIZE_MB=25
```

### 3. Start Services

```bash
# Start all services (Redis, Backend, Worker, Frontend)
docker-compose up --build

# Or run in detached mode
docker-compose up -d --build
```

### 4. Access the Application

- **Web UI**: http://localhost:8080
- **API Documentation**: http://localhost:8000/docs
- **API Base URL**: http://localhost:8000

## 🧪 Testing

### Option 1: Web UI (Recommended)

1. Open http://localhost:8080 in your browser
2. Drag and drop PDF files or click to select
3. Choose a parser (PyPDF, Gemini, or Mistral)
4. Click "Upload and Process"
5. Monitor job status and view results

### Option 2: cURL Commands

#### Upload Files

```bash
# Upload single file with PyPDF parser
curl -X POST -F "files=@sample.pdf" \
     "http://localhost:8000/api/upload?parser=pypdf"

# Upload multiple files with Gemini parser
curl -X POST -F "files=@sample1.pdf" -F "files=@sample2.pdf" \
     "http://localhost:8000/api/upload?parser=gemini"
```

Response:
```json
[
  {
    "job_id": "550e8400-e29b-41d4-a716-446655440000",
    "status": "pending",
    "filename": "sample.pdf",
    "parser": "gemini",
    "timestamp": "2024-01-15T10:30:00Z"
  }
]
```

#### Check Job Status

```bash
curl "http://localhost:8000/api/status/{job_id}"
```

Response:
```json
{
  "job_id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "processing",
  "filename": "sample.pdf",
  "parser": "gemini",
  "timestamp": "2024-01-15T10:30:00Z",
  "error": null
}
```

#### Get Processing Result

```bash
curl "http://localhost:8000/api/result/{job_id}"
```

Response:
```json
{
  "job_id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "completed",
  "filename": "sample.pdf",
  "parser": "gemini",
  "pages": [
    {
      "page": "1",
      "content": "This is the content of page 1..."
    },
    {
      "page": "2",
      "content": "This is the content of page 2..."
    }
  ],
  "summary": "This document discusses...",
  "error": null,
  "timestamp": "2024-01-15T10:30:00Z",
  "processing_time_seconds": 12.5
}
```

#### List All Jobs

```bash
curl "http://localhost:8000/api/jobs"
```

#### Delete Job

```bash
curl -X DELETE "http://localhost:8000/api/jobs/{job_id}"
```

## 📁 Project Structure

```
pdf-processor/
├── backend/
│   ├── app/
│   │   ├── __init__.py
│   │   ├── main.py          # FastAPI application
│   │   ├── models.py        # Pydantic models
│   │   ├── parsers.py       # PDF parser implementations
│   │   ├── redis_client.py  # Redis operations
│   │   ├── worker.py        # Background worker
│   │   └── config.py        # Configuration management
│   ├── requirements.txt
│   └── Dockerfile
├── frontend/
│   ├── index.html          # Web UI
│   └── app.js              # Frontend JavaScript
├── sample_pdfs/            # Place test PDFs here
├── docker-compose.yml
├── .env                    # Environment variables
├── .env.example           # Template
└── README.md
```

## 🔧 Configuration

All configuration is managed through environment variables in `.env`:

| Variable | Description | Default |
|----------|-------------|---------|
| `REDIS_URL` | Redis connection string | `redis://redis:6379` |
| `GOOGLE_API_KEY` | Google Gemini API key | *Required* |
| `MISTRAL_API_KEY` | Mistral API key | *Optional* |
| `MAX_FILE_SIZE_MB` | Maximum PDF size | `25` |
| `UPLOAD_DIR` | File upload directory | `/app/uploads` |
| `REDIS_RESULT_TTL_SECONDS` | Result expiration time | `3600` (1 hour) |

## 🛠️ Development

### Run Backend Locally

```bash
cd backend

# Install dependencies
pip install -r requirements.txt

# Start Redis (in separate terminal)
docker run -p 6379:6379 redis:7-alpine

# Start FastAPI
uvicorn app.main:app --reload

# Start worker (in separate terminal)
python -m app.worker
```

### Run Frontend Locally

```bash
cd frontend

# Serve with any HTTP server
python -m http.server 8080
# or
npx serve .
```

## 📊 API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/` | API information |
| `GET` | `/health` | Health check |
| `POST` | `/api/upload` | Upload PDF files |
| `GET` | `/api/status/{job_id}` | Get job status |
| `GET` | `/api/result/{job_id}` | Get processing result |
| `GET` | `/api/jobs` | List all jobs |
| `DELETE` | `/api/jobs/{job_id}` | Delete job |

Full API documentation: http://localhost:8000/docs

## 🐛 Troubleshooting

### Redis Connection Issues

```bash
# Check Redis is running
docker-compose ps

# View Redis logs
docker-compose logs redis
```

### Worker Not Processing Jobs

```bash
# Check worker logs
docker-compose logs worker

# Restart worker
docker-compose restart worker
```

### API Key Issues

```bash
# Verify API key is set
docker-compose exec backend env | grep GOOGLE_API_KEY

# Update .env and restart
docker-compose restart backend worker
```

### View Application Logs

```bash
# All services
docker-compose logs -f

# Specific service
docker-compose logs -f backend
docker-compose logs -f worker
```

## 📝 Notes

### Parser Comparison

| Parser | Speed | Accuracy | Use Case | API Required |
|--------|-------|----------|----------|--------------|
| **PyPDF** | ⚡ Fast | Good | Text-based PDFs | Gemini (summary only) |
| **Gemini** | ⚙️ Moderate | Excellent | Complex layouts | Gemini |
| **Mistral** | 🐌 Slow | Excellent | Scanned/Image PDFs | Mistral |

### Mistral OCR Implementation

The Mistral OCR parser is **fully implemented** and includes:
1. ✅ PDF-to-image conversion using `pdf2image`
2. ✅ Base64 image encoding
3. ✅ Mistral Vision API integration (Pixtral model)
4. ✅ Page-by-page OCR processing
5. ✅ AI-generated summary using Mistral

**Best for**: Scanned documents, images, or PDFs without embedded text.

**Note**: OCR processing is slower than text extraction but provides excellent accuracy for visual content.

### Result Expiration

Processing results are stored in Redis with a **1-hour TTL** (configurable via `REDIS_RESULT_TTL_SECONDS`). After expiration, you'll need to reprocess the PDF.

## 🔒 Security Considerations

- API keys are stored in environment variables
- File uploads are validated for size and type
- Results expire automatically to prevent data accumulation
- No authentication implemented (add for production use)

## 🚢 Production Deployment

For production, consider:

1. **Add Authentication**: Implement JWT or OAuth2
2. **Use Managed Redis**: AWS ElastiCache, Redis Cloud, etc.
3. **Add HTTPS**: Use Nginx reverse proxy with SSL
4. **Scale Workers**: Increase worker count in `docker-compose.yml`
5. **Persistent Storage**: Use S3 or similar for PDF files
6. **Monitoring**: Add Prometheus, Grafana, or similar
7. **Rate Limiting**: Prevent abuse with rate limits

## 📄 License

MIT License - see LICENSE file for details

## 🙏 Acknowledgments

- FastAPI for the excellent web framework
- Google Gemini for AI-powered PDF processing
- Redis for reliable job queuing
