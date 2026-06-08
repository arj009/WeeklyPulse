# Deploy WeeklyPulse MCP Server to Render

This guide walks you through deploying the WeeklyPulse MCP server on Render.

---

## 🎯 **Why Render?**

- ✅ **Free tier available** - No cost for development/testing
- ✅ **Auto-deploy from GitHub** - Push to deploy
- ✅ **Built-in HTTPS** - Secure connections
- ✅ **Easy secret management** - Environment variables UI
- ✅ **Health checks** - Automatic monitoring
- ✅ **Better than Railway** - Simpler setup, generous free tier

---

## 📋 **Prerequisites**

1. ✅ GitHub account
2. ✅ Render account (sign up at https://render.com)
3. ✅ Google Cloud Console project with APIs enabled
4. ✅ `Credential.json` (OAuth credentials)
5. ✅ `token.json` (OAuth token from local testing)

---

## 🚀 **Deployment Steps**

### **Step 1: Push Code to GitHub**

```powershell
# Add and commit changes
git add .
git commit -m "Add Render deployment configuration"

# Push to GitHub
git push origin main
```

**⚠️ IMPORTANT:** Make sure `.gitignore` excludes:
- `Credential.json`
- `token.json`
- `.env`

---

### **Step 2: Create Render Service**

1. Go to: https://dashboard.render.com
2. Click **"New +"** → **"Web Service"**
3. Connect your GitHub repository
4. Configure service:

**Service Configuration:**
- **Name:** `weeklypulse-mcp-server`
- **Region:** Oregon (closest to you)
- **Branch:** `main`
- **Root Directory:** Leave blank
- **Runtime:** Python 3
- **Build Command:** `pip install -e .`
- **Start Command:** `python -m weeklypulse.delivery.mcp_google_server`
- **Plan:** Free

---

### **Step 3: Add Environment Variables**

In Render dashboard, go to **Environment** tab and add:

| Variable | Value | Notes |
|----------|-------|-------|
| `PYTHON_VERSION` | `3.10.0` | Python version |
| `GROQ_API_KEY` | `your_groq_key` | From `.env` file |
| `WEEKLYPULSE_DRAFT_TO` | `aunkarranjan@gmail.com` | Your email |
| `APP_NAME` | `Groww` | App name |

**⚠️ DO NOT ADD:**
- `Credential.json` content
- `token.json` content
- Any local file paths

---

### **Step 4: Upload OAuth Credentials**

Render needs your Google OAuth files as environment variables.

#### **Convert JSON to Single Line:**

**PowerShell:**
```powershell
# Convert Credential.json
Get-Content Credential.json | ConvertFrom-Json | ConvertTo-Json -Compress | Set-Clipboard

# Convert token.json
Get-Content token.json | ConvertFrom-Json | ConvertTo-Json -Compress | Set-Clipboard
```

**Linux/Mac:**
```bash
# Convert Credential.json
cat Credential.json | jq -c . | pbcopy

# Convert token.json
cat token.json | jq -c . | pbcopy
```

#### **Add to Render:**

1. Go to your service in Render dashboard
2. Click **"Environment"** tab
3. Add these environment variables:

| Variable | Value |
|----------|-------|
| `GOOGLE_CREDENTIALS_JSON` | `<paste Credential.json single line>` |
| `GOOGLE_TOKEN_JSON` | `<paste token.json single line>` |

---

### **Step 5: Deploy!**

1. Click **"Create Web Service"**
2. Render will:
   - Clone your repo
   - Install dependencies
   - Start the MCP server
3. Wait for deployment (2-3 minutes)
4. You'll see: **"Your service is live 🎉"**

---

## ✅ **Verify Deployment**

### **Check Health:**

Visit: `https://weeklypulse-mcp-server.onrender.com/health`

Should return:
```json
{"status": "ok", "service": "WeeklyPulse"}
```

### **Check Logs:**

In Render dashboard → **Logs** tab

You should see:
```
INFO: Loading credentials from environment variables (cloud mode)
INFO: Starting WeeklyPulse MCP Server...
```

---

## 🔧 **How It Works**

### **Local Development (Your Machine):**
```python
# Reads from files
Credential.json  → OAuth credentials
token.json       → OAuth token
```

### **Cloud Deployment (Render):**
```python
# Reads from environment variables
GOOGLE_CREDENTIALS_JSON  → OAuth credentials
GOOGLE_TOKEN_JSON        → OAuth token
```

**The code automatically detects which mode to use!**

---

## 📊 **Render Dashboard**

Your service URL: `https://weeklypulse-mcp-server.onrender.com`

**Features:**
- ✅ Auto-deploy on git push
- ✅ Automatic HTTPS
- ✅ Health checks every 5 minutes
- ✅ Logs in real-time
- ✅ Environment variable management
- ✅ Free tier: 750 hours/month

---

## ⚠️ **Important Notes**

### **Free Tier Limitations:**
- ⚠️ **Spins down after 15 minutes** of inactivity
- ⚠️ **Takes 30-60 seconds** to wake up on next request
- ⚠️ **Not suitable for production** (use paid plan for that)

### **Solutions:**
1. **Keep-alive script:** Ping endpoint every 10 minutes
2. **Upgrade to paid plan:** $7/month (no spin-down)
3. **Use for development only:** Free tier is perfect for testing

---

## 🔄 **Updating Deployment**

Every time you push to `main` branch:
1. Render auto-detects changes
2. Rebuilds and redeploys
3. Zero downtime (blue-green deployment)

**To manually trigger redeploy:**
- Render dashboard → **"Manual Deploy"** → **"Deploy latest commit"**

---

## 🛠️ **Troubleshooting**

### **Issue: Build fails**
**Check:**
- `pyproject.toml` has all dependencies
- Build logs show `pip install -e .` succeeded

### **Issue: Service won't start**
**Check:**
- Environment variables are set correctly
- `GOOGLE_CREDENTIALS_JSON` and `GOOGLE_TOKEN_JSON` are valid JSON
- Logs show "cloud mode" or "local mode"

### **Issue: 403 Forbidden from Google APIs**
**Check:**
- Google Cloud Console APIs are enabled
- OAuth consent screen configured
- Test user added (your email)

### **Issue: Token expired**
**Solution:**
1. Generate new `token.json` locally
2. Convert to single line
3. Update `GOOGLE_TOKEN_JSON` in Render
4. Redeploy

---

## 📝 **Next Steps After Deployment**

1. ✅ **Test MCP server** - Connect Cursor/Qoder agent
2. ✅ **Set up GitHub Actions** - Automated weekly runs
3. ✅ **Monitor logs** - Check for errors
4. ✅ **Upgrade plan** (optional) - Remove spin-down

---

## 🎉 **You're Live!**

Your MCP server is now running on Render and ready for AI agents to connect!

**Service URL:** `https://weeklypulse-mcp-server.onrender.com`
