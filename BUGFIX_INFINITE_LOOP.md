# Bug Fix: Infinite Polling Loop in Next.js Frontend

## Issue Description

The Next.js frontend was making continuous GET requests to `/api/jobs` endpoint in an endless loop, causing:
- Excessive backend load
- Unnecessary network traffic
- Poor user experience
- Logs flooding with repeated requests

```
pdf-backend | INFO: 172.217.165.10:43576 - "GET /api/jobs HTTP/1.1" 200 OK
pdf-backend | INFO: 172.217.165.10:43576 - "GET /api/jobs HTTP/1.1" 200 OK
pdf-backend | INFO: 172.217.165.10:43576 - "GET /api/jobs HTTP/1.1" 200 OK
... (repeated indefinitely)
```

## Root Cause

In `frontend-nextjs/src/app/page.tsx`, the `useEffect` hook had `jobs` in its dependency array, creating an infinite loop:

**Problematic Code:**
```typescript
useEffect(() => {
  loadJobs()

  const interval = setInterval(() => {
    const hasActiveJobs = jobs.some(
      (job) => job.status === 'pending' || job.status === 'processing'
    )
    if (hasActiveJobs) {
      loadJobs()
    }
  }, 5000)

  return () => clearInterval(interval)
}, [jobs]) // <-- This causes the infinite loop!
```

**Why This Caused the Loop:**
1. Component mounts → `useEffect` runs → calls `loadJobs()`
2. `loadJobs()` updates `jobs` state
3. `jobs` update triggers `useEffect` again (because `jobs` is in dependency array)
4. Interval is set up, calls `loadJobs()` → updates `jobs`
5. `jobs` update triggers `useEffect` again → new interval created
6. Back to step 2, infinite loop

## Solution

Split the effect into two separate effects with proper dependencies:

**Fixed Code:**
```typescript
// Load jobs on mount
useEffect(() => {
  loadJobs()
}, []) // Empty deps = runs only once on mount

// Set up auto-refresh for active jobs
useEffect(() => {
  const hasActiveJobs = jobs.some(
    (job) => job.status === 'pending' || job.status === 'processing'
  )

  if (!hasActiveJobs) return

  const interval = setInterval(() => {
    loadJobs()
  }, 5000)

  return () => clearInterval(interval)
}, [jobs.length, jobs.filter(j => j.status === 'pending' || j.status === 'processing').length])
```

**How This Fixes It:**
1. **First effect**: Runs only once on mount, loads initial jobs
2. **Second effect**:
   - Only runs when number of jobs changes OR number of active jobs changes
   - Only sets up interval if there ARE active jobs
   - Cleans up interval properly when active jobs count changes
   - No longer creates infinite loop because it depends on derived values, not full `jobs` array

## Files Modified

**File**: `frontend-nextjs/src/app/page.tsx`
**Lines**: 17-35
**Changes**:
- Split single `useEffect` into two separate effects
- Changed dependencies from `[jobs]` to `[]` and derived values
- Added early return if no active jobs

## Testing

### Before Fix:
```bash
$ docker logs pdf-backend --tail 100 | grep "GET /api/jobs" | wc -l
# Returns: 100+ (continuous requests)
```

### After Fix:
```bash
$ docker logs pdf-backend --tail 100 | grep "GET /api/jobs" | wc -l
# Returns: 0 (no polling when no active jobs)
```

### Behavior After Fix:
1. **On page load**: Single request to load jobs
2. **No active jobs**: No polling
3. **Upload PDF**: Polling starts at 5-second intervals
4. **Job completes**: Polling stops

## Deployment

```bash
# Stop containers
docker-compose down

# Rebuild frontend with fix
docker-compose up --build -d

# Verify fix
docker logs pdf-backend --tail 20
# Should show no repeated requests
```

## Related Components

This bug affected:
- Frontend polling logic (`page.tsx`)
- Backend `/api/jobs` endpoint (unnecessary load)
- Docker container resources (CPU/network)
- User experience (potential browser performance issues)

## Prevention

To prevent similar issues in the future:

1. **Be careful with useEffect dependencies**: Including state that gets updated within the effect creates loops
2. **Separate concerns**: Split effects that handle different responsibilities
3. **Use derived values**: Depend on computed values (like counts) rather than full arrays
4. **Add early returns**: Exit early if conditions aren't met
5. **Test polling behavior**: Always verify polling starts/stops as expected

## Impact

**Before**: Continuous polling regardless of job status
**After**: Smart polling only when jobs are active

**Benefits**:
- ✅ Reduced backend load
- ✅ Lower network traffic
- ✅ Better battery life on mobile
- ✅ Cleaner logs
- ✅ Improved user experience

---

**Fixed**: 2025-10-30 11:03 EDT
**Build Time**: ~13s
**Status**: ✅ Verified Working
