# Vercel Deployment Troubleshooting Guide

## 🔥 Common Vercel Deployment Issues & Solutions

---

### Issue 1: Build Fails with "standalone" Output Error

**Error Message:**
```
Error: Output "standalone" not supported in Vercel deployments
```

**Cause:**
Next.js `standalone` output is for Docker/self-hosted deployments, not Vercel.

**Solution:**
Fixed in latest commit. The `next.config.js` now conditionally sets output:
```javascript
output: process.env.DOCKER_BUILD === 'true' ? 'standalone' : undefined
```

---

### Issue 2: Build Fails - Wrong Root Directory

**Error Message:**
```
Error: Cannot find module 'next' or package.json not found
```

**Solution:**
1. In Vercel dashboard → Settings
2. Set **Root Directory** to: `frontend-nextjs`
3. Redeploy

---

### Issue 3: API Requests Fail - CORS Error

**Error in Browser Console:**
```
Access to fetch at 'https://railway-backend.up.railway.app' from origin
'https://your-app.vercel.app' has been blocked by CORS policy
```

**Solution:**

1. Update `backend/app/main.py`:
```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://localhost:8080",
        "https://your-app.vercel.app",  # Add your Vercel URL
        "https://your-app-*.vercel.app",  # For preview deployments
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

2. Commit and push - Railway will auto-redeploy

---

### Issue 4: Environment Variable Not Working

**Symptom:**
Frontend tries to connect to `http://localhost:8000` instead of Railway backend

**Solution:**

1. **In Vercel Dashboard:**
   - Go to Settings → Environment Variables
   - Add: `NEXT_PUBLIC_API_URL`
   - Value: `https://your-railway-backend.up.railway.app`
   - **Important**: NO trailing slash!

2. **Redeploy:**
   - Deployments → Three dots → Redeploy

3. **Verify in Browser Console:**
   ```javascript
   console.log(process.env.NEXT_PUBLIC_API_URL)
   // Should show your Railway URL
   ```

---

### Issue 5: Build Succeeds but Page is Blank

**Possible Causes & Solutions:**

1. **Missing Environment Variable:**
   - Check NEXT_PUBLIC_API_URL is set
   - Redeploy after adding

2. **Build Cache Issue:**
   - Settings → General → Clear Build Cache
   - Redeploy

3. **Check Browser Console:**
   - Open DevTools (F12)
   - Look for errors in Console tab

---

### Issue 6: "Module not found" During Build

**Common Missing Modules:**
```
Module not found: Can't resolve 'axios'
Module not found: Can't resolve 'tailwindcss'
```

**Solution:**

Check `package.json` has all dependencies:
```json
{
  "dependencies": {
    "react": "^18.2.0",
    "react-dom": "^18.2.0",
    "next": "^14.0.4",
    "axios": "^1.6.2"
  },
  "devDependencies": {
    "@types/node": "^20.10.5",
    "@types/react": "^18.2.45",
    "@types/react-dom": "^18.2.18",
    "typescript": "^5.3.3",
    "tailwindcss": "^3.3.6",
    "postcss": "^8.4.32",
    "autoprefixer": "^10.4.16",
    "eslint": "^8.56.0",
    "eslint-config-next": "^14.0.4"
  }
}
```

If missing, add them and push to GitHub.

---

## 🛠️ Vercel Configuration Checklist

### Project Settings (Vercel Dashboard)

✅ **Framework Preset:** Next.js
✅ **Root Directory:** `frontend-nextjs`
✅ **Build Command:** `npm run build` (or leave default)
✅ **Output Directory:** `.next` (or leave default)
✅ **Install Command:** `npm install` (or leave default)

### Environment Variables

✅ **NEXT_PUBLIC_API_URL:** Your Railway backend URL (no trailing slash)

Example:
```
NEXT_PUBLIC_API_URL=https://pdf-processor-production-c5ad.up.railway.app
```

---

## 📝 Step-by-Step Fresh Deployment

If nothing works, try a fresh deployment:

1. **Delete Current Project in Vercel**
   - Settings → Delete Project

2. **Remove vercel.json (if exists)**
   ```bash
   git rm vercel.json
   git commit -m "Remove vercel.json for auto-detection"
   git push origin main
   ```

3. **Create New Project in Vercel**
   - New Project → Import `alejochang/pdf-processor`
   - Set Root Directory: `frontend-nextjs`
   - Add Environment Variable: `NEXT_PUBLIC_API_URL`
   - Deploy

4. **Update Backend CORS**
   - Add new Vercel URL to `backend/app/main.py`
   - Push to GitHub
   - Railway auto-redeploys

---

## 🔍 Debugging Commands

### Check Build Logs
In Vercel Dashboard → Deployments → Click deployment → View Build Logs

### Test API Connection
In browser console (F12):
```javascript
// Test if env var is set
console.log(process.env.NEXT_PUBLIC_API_URL)

// Test API connection
fetch(`${process.env.NEXT_PUBLIC_API_URL}/health`)
  .then(r => r.json())
  .then(console.log)
  .catch(console.error)
```

### Clear All Caches
1. Vercel: Settings → Clear Build Cache
2. Browser: Ctrl+Shift+R (hard refresh)
3. Try incognito/private window

---

## 💡 Pro Tips

1. **Preview Deployments:**
   - Every PR gets a preview URL
   - Test changes before merging to main

2. **Environment Variables per Branch:**
   - Can set different vars for preview/production
   - Useful for staging environments

3. **Vercel CLI:**
   ```bash
   npm i -g vercel
   vercel login
   vercel --prod  # Deploy from command line
   ```

4. **Function Logs:**
   - Vercel Dashboard → Functions → Logs
   - See runtime errors

---

## 🆘 Still Having Issues?

### Quick Fixes to Try:

1. **Clear Everything:**
   ```bash
   # Clear Vercel build cache
   Settings → Clear Build Cache → Redeploy

   # Clear browser cache
   Ctrl + Shift + R
   ```

2. **Verify Git is Updated:**
   ```bash
   git pull origin main
   git status  # Should be clean
   ```

3. **Check Railway Backend:**
   ```bash
   curl https://your-railway-url.railway.app/health
   # Should return {"status": "healthy", ...}
   ```

4. **Try Local Build:**
   ```bash
   cd frontend-nextjs
   npm install
   npm run build
   # If this fails, fix errors before pushing
   ```

### Contact Support:

- **Vercel Support:** https://vercel.com/support
- **Vercel Discord:** https://vercel.com/discord
- **GitHub Issues:** https://github.com/alejochang/pdf-processor/issues

---

## ✅ Working Configuration (Verified)

This configuration is confirmed working:

**Repository Structure:**
```
pdf-processor/
├── backend/           # Railway deployment
├── frontend-nextjs/   # Vercel deployment (Root Directory)
│   ├── src/
│   ├── public/
│   ├── package.json
│   ├── next.config.js # No 'standalone' output for Vercel
│   └── ...
└── docker-compose.yml
```

**Vercel Settings:**
- Root Directory: `frontend-nextjs`
- Framework: Next.js (auto-detected)
- No vercel.json needed (uses auto-detection)

**Environment:**
- `NEXT_PUBLIC_API_URL=https://your-backend.railway.app`

**Backend CORS includes:**
- Your Vercel production URL
- Your Vercel preview URLs (*.vercel.app)

---

Last Updated: After fixing standalone output issue