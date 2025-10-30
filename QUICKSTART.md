# Quick Start Guide

Get the PDF Processing Application running in 5 minutes!

## Prerequisites

- Docker & Docker Compose installed
- Internet connection (for pulling Docker images)

## Steps

### 1. Navigate to Project Directory

```bash
cd pdf-processor
```

### 2. Start the Application

```bash
docker-compose up --build
```

Wait for all services to start. You should see:
```
pdf-redis     | Ready to accept connections
pdf-backend   | Uvicorn running on http://0.0.0.0:8000
pdf-worker    | Worker worker-1 is ready and waiting for jobs...
pdf-frontend  | start worker processes
```

### 3. Open the Web Interface

Open your browser and go to: **http://localhost:8080**

### 4. Upload a PDF

1. **Drag and drop** a PDF file onto the upload area, or **click** to select
2. Choose a parser:
   - **PyPDF** (recommended for text PDFs)
   - **Gemini** (best accuracy, uses AI)
   - **Mistral** (for OCR - experimental)
3. Click **"Upload and Process"**

### 5. Monitor Progress

- Jobs appear in the "Processing Jobs" section below
- Status updates automatically: `pending` → `processing` → `completed`
- Click **"View Result"** when completed to see:
  - Extracted text (organized by page)
  - AI-generated summary

## Alternative: Test with cURL

### Upload a file:
```bash
curl -X POST -F "files=@sample.pdf" \
     "http://localhost:8000/api/upload?parser=gemini"
```

Save the `job_id` from the response.

### Check status:
```bash
curl "http://localhost:8000/api/status/{job_id}"
```

### Get result:
```bash
curl "http://localhost:8000/api/result/{job_id}"
```

## Run Test Script

```bash
# Place a PDF in sample_pdfs/ directory
cp ~/Documents/sample.pdf sample_pdfs/

# Run automated test
./test_api.sh
```

## Access Points

- 🌐 **Web UI**: http://localhost:8080
- 📚 **API Docs**: http://localhost:8000/docs
- 🔧 **API Base**: http://localhost:8000

## Troubleshooting

### Services not starting?

```bash
# Check service status
docker-compose ps

# View logs
docker-compose logs
```

### API key issues?

The `.env` file is already configured with your Gemini API key. If you need to change it:

```bash
# Edit .env
nano .env

# Restart services
docker-compose restart
```

### Port conflicts?

If ports 8000, 8080, or 6379 are already in use, edit `docker-compose.yml`:

```yaml
# Change port mappings
ports:
  - "9000:8000"  # Backend on port 9000
  - "9080:80"    # Frontend on port 9080
```

## Stop the Application

```bash
# Stop services (keep data)
docker-compose stop

# Stop and remove containers (clean slate)
docker-compose down

# Stop and remove everything including volumes
docker-compose down -v
```

## What's Next?

- Read the full [README.md](README.md) for detailed documentation
- Explore the [API documentation](http://localhost:8000/docs)
- Try different parsers to compare results
- Check the [Architecture](README.md#-architecture) section to understand the system

## Need Help?

- Check logs: `docker-compose logs -f`
- Verify Redis: `docker-compose exec redis redis-cli ping`
- Test API: `curl http://localhost:8000/health`

---

**Happy Processing! 🚀**
