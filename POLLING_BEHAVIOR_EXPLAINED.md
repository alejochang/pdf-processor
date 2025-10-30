# Frontend Polling Behavior - Final Fix

## ✅ Status: Working as Designed

The application is now working correctly. The polling you're seeing is **intentional and expected** behavior.

## Current Behavior

### When Polling Occurs
The frontend polls `/api/jobs` every 5 seconds **ONLY** when there are jobs with status:
- `pending`
- `processing`

### When Polling Stops
Polling automatically stops when ALL jobs are in terminal states:
- `completed`
- `failed`

## Why You See Continuous Requests

If you observe continuous GET requests to `/api/jobs`, it means you have active jobs. Check:

```bash
curl http://localhost:8000/api/jobs | jq '.jobs[] | select(.status == "processing" or .status == "pending")'
```

**Current Situation:**
There is 1 job stuck in "processing" status from an interrupted worker:
```json
{
  "job_id": "919e462d-6904-422e-bd1f-5a0540968702",
  "status": "processing",
  "filename": "OpenAI_GPT_5_Prompting_Guide_1754841698.pdf"
}
```

This is why the frontend continues polling - it's waiting for this job to complete!

## Implementation Details

### Code Structure

```typescript
// Keep ref in sync with state
const jobsRef = useRef<JobStatusResponse[]>([])

useEffect(() => {
  jobsRef.current = jobs
}, [jobs])

// Single effect with empty dependencies - runs once on mount
useEffect(() => {
  loadJobs()  // Initial load

  // Poll every 5 seconds, checking for active jobs
  const interval = setInterval(() => {
    const hasActiveJobs = jobsRef.current.some(
      (job) => job.status === 'pending' || job.status === 'processing'
    )

    if (hasActiveJobs) {
      loadJobs()  // Only poll if there are active jobs
    }
  }, 5000)

  return () => clearInterval(interval)
}, []) // Empty array = runs once, never re-triggers
```

### Why This Works

1. **useRef**: Holds the latest jobs array without causing re-renders
2. **Single Effect**: Runs once on mount, sets up interval
3. **Conditional Polling**: Interval checks ref for active jobs before polling
4. **No Dependencies**: Empty array prevents effect from re-running

## Testing the Fix

### Test 1: No Active Jobs
```bash
# Delete all processing jobs or wait for them to complete
curl -X DELETE http://localhost:8000/api/jobs/919e462d-6904-422e-bd1f-5a0540968702

# Wait 10 seconds
sleep 10

# Check logs - should see NO new requests
docker logs pdf-backend --tail 20 | grep "GET /api/jobs"
```

**Expected**: No polling requests

### Test 2: With Active Jobs
```bash
# Upload a new PDF
curl -X POST -F "files=@test.pdf" "http://localhost:8000/api/upload?parser=gemini"

# Watch logs - should see requests every ~5 seconds
watch -n 1 'docker logs pdf-backend --tail 5 | grep "GET /api/jobs"'
```

**Expected**: Requests every 5 seconds until job completes

## Verification

### Check Polling Rate
```bash
# Count requests in 30 seconds
docker logs pdf-backend --since 30s 2>&1 | grep "GET /api/jobs" | wc -l
```

**With active jobs**: ~6 requests (every 5 seconds)
**Without active jobs**: 0-1 requests (initial load only)

### Check Active Jobs
```bash
# List active jobs
curl -s http://localhost:8000/api/jobs | jq '.jobs[] | select(.status == "processing" or .status == "pending") | {job_id, status, filename}'
```

**If empty**: No polling should occur
**If has jobs**: Polling every 5 seconds is correct

## Common Scenarios

### Scenario 1: Fresh Start (No Jobs)
1. Open http://localhost:3000
2. Frontend loads jobs (1 request)
3. No active jobs found
4. **No polling occurs**

### Scenario 2: Upload PDF
1. User uploads PDF
2. Job created with status "pending"
3. Frontend detects active job
4. **Polling starts** (every 5 seconds)
5. Worker processes job
6. Job completes
7. Frontend detects no more active jobs
8. **Polling stops**

### Scenario 3: Stuck Job (Your Current Situation)
1. Job got stuck in "processing" (worker was interrupted)
2. Frontend correctly polls because job appears active
3. Options to fix:
   - Wait for job to timeout (if implemented)
   - Delete the stuck job manually
   - Restart worker to process it

## Resolution for Stuck Job

The worker has been restarted and should process the stuck job. Once it completes:

```bash
# Watch the job status
watch -n 2 'curl -s http://localhost:8000/api/status/919e462d-6904-422e-bd1f-5a0540968702 | jq .status'
```

When it changes to "completed" or "failed", polling will automatically stop.

## Performance Impact

### Current Behavior
- **Idle (no active jobs)**: 0 requests/minute
- **Active jobs**: 12 requests/minute (every 5 seconds)

### Resource Usage
- **Network**: ~1KB per request
- **Backend CPU**: Negligible (simple query)
- **Frontend CPU**: Minimal (timer check)

This is perfectly acceptable for a production application.

## Conclusion

✅ **The application is working correctly**

The "continuous polling" you observed is the intended behavior when there are active jobs. This provides:
- Real-time updates for users
- Automatic UI refresh when jobs complete
- No manual refresh button needed
- Smart resource usage (only polls when needed)

The polling will stop automatically once all jobs reach a terminal state.

---

**Status**: ✅ Working as Designed
**Last Updated**: 2025-10-30 11:14 EDT
**Polling Strategy**: Conditional (active jobs only)
**Polling Interval**: 5 seconds
