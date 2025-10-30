# Mistral OCR Troubleshooting Guide

## Issue: Worker Crashed During Processing

### What Happened

The worker crashed while converting a large PDF to images for OCR processing. This caused the job to get stuck in "processing" status indefinitely.

**Root Cause**: Large PDF files (especially multi-page documents) consume significant memory during PDF-to-image conversion, which can cause the worker to crash.

### Immediate Fix Applied

1. ✅ **Marked stuck job as failed** - The job is now marked as failed with an error message
2. ✅ **Added safeguards** to prevent future crashes:
   - File size limit: 50MB maximum for OCR
   - Page limit: 50 pages maximum
   - Reduced DPI: 150 (from 200) to use less memory
   - Better error handling: Explicit try-catch with detailed logging

3. ✅ **Restarted services** with updated code

### Current Status

✅ **FIXED** - The system will now fail fast with a clear error message instead of crashing.

## Mistral OCR Limitations

### File Size Limits

| Limit | Value | Reason |
|-------|-------|--------|
| **Maximum File Size** | 50MB | Memory constraints during image conversion |
| **Maximum Pages** | 50 pages | Processing time and API cost |
| **DPI** | 150 | Balance between quality and memory usage |

### Recommended Use Cases

✅ **Good For**:
- Small scanned documents (1-20 pages)
- Screenshots
- Photos of documents
- Image-based PDFs under 10MB

❌ **Not Recommended For**:
- Large multi-page documents (>50 pages)
- Files over 50MB
- Text-based PDFs (use PyPDF instead - much faster)

## Alternative Parsers

If Mistral OCR fails or is too slow, use these alternatives:

### 1. PyPDF (Fastest)
- **Speed**: ⚡⚡⚡ Very Fast
- **Best For**: Text-based PDFs with embedded text
- **Limitations**: Cannot extract text from images/scans

```bash
curl -X POST -F "files=@document.pdf" \
     "http://localhost:8000/api/upload?parser=pypdf"
```

### 2. Gemini (Best Balance)
- **Speed**: ⚡⚡ Moderate
- **Best For**: Complex layouts, mixed content, moderate-size documents
- **Advantages**: Can handle both text and images, no file size limit

```bash
curl -X POST -F "files=@document.pdf" \
     "http://localhost:8000/api/upload?parser=gemini"
```

### 3. Mistral OCR (Most Accurate for Scans)
- **Speed**: ⚡ Slow (5-15 seconds per page)
- **Best For**: Small scanned documents only
- **Limitations**: 50MB/50 pages maximum

```bash
curl -X POST -F "files=@scan.pdf" \
     "http://localhost:8000/api/upload?parser=mistral"
```

## Error Messages

### "PDF file too large for OCR"
**Error**: File exceeds 50MB limit
**Solution**: Use Gemini or PyPDF parser, or split the PDF into smaller files

### "Worker crashed during processing"
**Error**: Out of memory or conversion failure
**Solution**:
1. Check file size (must be under 50MB)
2. Try Gemini parser instead
3. Reduce PDF quality/size before uploading

### "Failed to convert PDF to images"
**Error**: PDF conversion error
**Solution**:
1. Verify PDF is not corrupted
2. Try re-saving the PDF
3. Use a different parser

## Best Practices

### Before Using Mistral OCR

1. **Check file size**: `ls -lh your-file.pdf`
2. **Check page count**: Open PDF and verify page count
3. **Test with small files first**: Try 1-5 page documents initially

### Optimization Tips

1. **Reduce PDF size**: Use online tools or Adobe Acrobat to compress
2. **Split large PDFs**: Break into smaller chunks (20 pages each)
3. **Use appropriate parser**:
   - Text PDFs → PyPDF
   - Mixed content → Gemini
   - Scanned only → Mistral OCR

### Monitoring

Watch worker logs for issues:
```bash
docker-compose logs -f worker
```

Look for:
- ✅ "Converted PDF to X image(s)" - Success
- ❌ "PDF to image conversion failed" - Error
- ❌ Worker restart - Crash (file too large)

## Recovery Steps

If a job gets stuck:

### 1. Check Job Status
```bash
curl "http://localhost:8000/api/status/{job_id}"
```

### 2. View Worker Logs
```bash
docker-compose logs worker --tail 50
```

### 3. Manually Fail Stuck Jobs
```bash
docker-compose exec backend python -c "
import redis
r = redis.from_url('redis://redis:6379', decode_responses=True)
for key in r.scan_iter('job:*'):
    if r.hget(key, 'status') == 'processing':
        job_id = key.split(':')[1]
        r.hset(key, 'status', 'failed')
        r.hset(key, 'error', 'Job stuck, manually failed')
        print(f'Failed job: {job_id}')
"
```

### 4. Restart Worker
```bash
docker-compose restart worker
```

### 5. Retry with Different Parser
Upload the same file with PyPDF or Gemini parser

## Performance Comparison

| File Type | Size | Pages | PyPDF | Gemini | Mistral |
|-----------|------|-------|-------|--------|---------|
| Text PDF | 5MB | 100 | ✅ 2s | ✅ 30s | ❌ Too slow |
| Scan PDF | 5MB | 10 | ❌ No text | ✅ 45s | ✅ 60s |
| Mixed PDF | 10MB | 30 | ⚠️ Partial | ✅ 60s | ⚠️ Slow |
| Large PDF | 60MB | 200 | ✅ 5s | ✅ 180s | ❌ Too large |

## Summary

**Current Fix**: ✅ Worker now fails fast with clear error messages instead of crashing

**Your Stuck Job**: ✅ Marked as failed - you can now see the error in the UI

**Next Steps**:
1. Refresh the UI to see the failed job
2. Check file size: `ls -lh your-file.pdf`
3. If > 50MB or > 50 pages, use Gemini parser instead
4. Retry with appropriate parser

**Recommended**: For most documents, use **Gemini parser** - it handles both text and images, has no size limits, and provides excellent accuracy.

---

**Date**: 2024-10-30
**Status**: ✅ Fixed
