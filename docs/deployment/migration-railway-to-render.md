# Migration: Railway → Render

**Date:** 2026-05-29  
**Reason:** Changed deployment platform from Railway to Render

---

## ✅ **What Changed**

### **Files Created:**
- ✅ `render.yaml` - Render service configuration
- ✅ `docs/deployment/render-deployment.md` - Complete deployment guide

### **Files Modified:**
- ✅ `src/weeklypulse/delivery/mcp_google_server.py` - Added environment variable support for cloud deployment
- ✅ `README.md` - Updated Phase 6 section to reference Render instead of Railway

### **Files Kept (for reference):**
- 📁 `railway.json` - Still in repo (can delete if not needed)
- 📁 `src/weeklypulse/main_api.py` - FastAPI backend (still useful for GitHub Actions)

---

## 🔑 **Key Differences: Railway vs Render**

| Feature | Railway | Render |
|---------|---------|--------|
| **Free Tier** | 500 hours/month | 750 hours/month ✅ |
| **Spin-down** | After inactivity | After 15 min inactivity |
| **Setup** | Simple | Simple ✅ |
| **Environment Variables** | Dashboard | Dashboard ✅ |
| **Auto-deploy** | GitHub integration | GitHub integration ✅ |
| **Health Checks** | Built-in | Built-in ✅ |
| **Pricing** | $5/month+ | $7/month+ |

---

## 🚀 **Render Deployment Benefits**

1. ✅ **More free hours** - 750 vs 500
2. ✅ **Simpler config** - `render.yaml` is straightforward
3. ✅ **Better docs** - Comprehensive deployment guide
4. ✅ **Same features** - Auto-deploy, env vars, health checks
5. ✅ **Environment variable support** - MCP server now reads from env vars

---

## 📝 **How to Deploy to Render**

### **Quick Steps:**

1. **Push to GitHub:**
   ```bash
   git add .
   git commit -m "Add Render deployment configuration"
   git push origin main
   ```

2. **Create Render Service:**
   - Go to: https://dashboard.render.com
   - New + → Web Service
   - Connect GitHub repo
   - Use config from `render.yaml`

3. **Add Environment Variables:**
   - `GOOGLE_CREDENTIALS_JSON` - Your OAuth credentials (single line JSON)
   - `GOOGLE_TOKEN_JSON` - Your OAuth token (single line JSON)
   - `GROQ_API_KEY` - Your Groq API key
   - `WEEKLYPULSE_DRAFT_TO` - Your email
   - `APP_NAME` - Groww

4. **Deploy!**
   - Click "Create Web Service"
   - Wait 2-3 minutes
   - Service is live!

### **Full Guide:**
See: [docs/deployment/render-deployment.md](./docs/deployment/render-deployment.md)

---

## 🔧 **Code Changes Made**

### **MCP Server - Environment Variable Support**

**Before (Local Only):**
```python
def get_credentials():
    token_path = get_token_path()  # Reads from file
    creds = Credentials.from_authorized_user_file(str(token_path), SCOPES)
```

**After (Local + Cloud):**
```python
def get_credentials():
    # Check for cloud deployment
    creds_json = os.environ.get("GOOGLE_CREDENTIALS_JSON")
    token_json = os.environ.get("GOOGLE_TOKEN_JSON")
    
    if creds_json and token_json:
        # Cloud mode - use environment variables
        logger.info("Loading credentials from environment variables (cloud mode)")
        # ... writes to temp files, loads credentials
    else:
        # Local mode - use files
        logger.info("Loading credentials from files (local mode)")
        # ... reads from Credential.json and token.json
```

**Benefits:**
- ✅ Works locally (file-based)
- ✅ Works on Render (env var-based)
- ✅ Automatic detection
- ✅ No code changes needed for deployment

---

## 📊 **Environment Variables Comparison**

### **Railway (Old):**
```
GROQ_API_KEY
WEEKLYPULSE_DRAFT_TO
APP_NAME
GOOGLE_SERVICE_ACCOUNT_JSON  ← Different name
```

### **Render (New):**
```
GROQ_API_KEY
WEEKLYPULSE_DRAFT_TO
APP_NAME
GOOGLE_CREDENTIALS_JSON  ← Credential.json as env var
GOOGLE_TOKEN_JSON        ← token.json as env var
PYTHON_VERSION           ← Explicit Python version
```

---

## ⚠️ **Important Notes**

### **Render Free Tier Limitations:**
- ⚠️ Spins down after 15 minutes of inactivity
- ⚠️ Takes 30-60 seconds to wake up
- ⚠️ Not suitable for production (use paid plan: $7/month)

### **Solutions:**
1. Keep-alive script (ping every 10 min)
2. Upgrade to paid plan
3. Use for development/testing only

---

## ✅ **Migration Checklist**

- [x] Create `render.yaml` configuration
- [x] Update MCP server for environment variable support
- [x] Create comprehensive deployment guide
- [x] Update README.md references
- [x] Test environment variable logic
- [ ] Deploy to Render (user action)
- [ ] Verify MCP server works on Render
- [ ] Update GitHub Actions secrets (if using)

---

## 🎯 **Next Steps**

1. **Deploy to Render** - Follow [render-deployment.md](./docs/deployment/render-deployment.md)
2. **Test MCP server** - Verify it works on Render
3. **Set up GitHub Actions** - Automated weekly runs (Phase 6)
4. **Monitor logs** - Check for errors in Render dashboard

---

**Migration complete! Ready to deploy to Render.** 🚀
