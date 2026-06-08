# GitHub Actions Setup Guide

This guide walks you through setting up automated weekly execution of the WeeklyPulse pipeline using GitHub Actions.

---

## 📋 **What We Just Created:**

✅ `.github/workflows/weekly-pulse.yml` - Automated workflow

**What it does:**
- ⏰ Runs every **Sunday at 6:00 AM UTC**
- 🔄 Triggers your Render API pipeline
- ⏳ Waits for completion
- 📊 Provides execution summary
- ❌ Notifies on failure

---

## 🔐 **Step 1: Add GitHub Secrets**

Go to your repository on GitHub → **Settings** → **Secrets and variables** → **Actions** → **New repository secret**

### **Required Secrets:**

| Secret Name | Value | Purpose |
|-------------|-------|---------|
| `GROQ_API_KEY` | Your Groq API key | LLM access for analysis |
| `RENDER_API_KEY` | *(optional)* API key for authentication | Secure API access |

**To add secrets:**
1. Go to: https://github.com/arj009/WeeklyPulse/settings/secrets/actions
2. Click **"New repository secret"**
3. Add each secret with its value

---

## ⏰ **Step 2: Schedule Configuration**

**Current schedule:** Every Sunday at 6:00 AM UTC

**To change the schedule:**
Edit `.github/workflows/weekly-pulse.yml` line 6:

```yaml
schedule:
  - cron: '0 6 * * 0'  # Sunday 6 AM UTC
```

**Cron format:** `minute hour day-of-month month day-of-week`

**Examples:**
- `0 6 * * 0` - Sunday 6 AM UTC
- `0 8 * * 1` - Monday 8 AM UTC
- `0 12 * * *` - Every day at noon UTC

---

## 🚀 **Step 3: Push to GitHub**

```powershell
cd d:\NextLeap\WeeklyPulse
git add .
git commit -m "Add GitHub Actions workflow for automated weekly execution"
git push origin main
```

---

## 🧪 **Step 4: Test Manual Trigger**

1. Go to: https://github.com/arj009/WeeklyPulse/actions
2. Click **"WeeklyPulse Pipeline"** workflow
3. Click **"Run workflow"** button (top right)
4. Select branch: `main`
5. (Optional) Enter week label or leave as "auto"
6. Click **"Run workflow"**

**Expected behavior:**
- ✅ Workflow starts
- ✅ Triggers Render API
- ✅ Waits for completion
- ✅ Shows summary

---

## 📊 **Step 5: Monitor Execution**

### **View Run History:**
- GitHub → Actions → WeeklyPulse Pipeline

### **View Logs:**
- Click any run → See detailed logs

### **Check Render Logs:**
- https://dashboard.render.com → Your service → Logs

---

## 🔧 **How It Works:**

```
┌─────────────────────────────────────────────────────┐
│  GitHub Actions (Every Sunday 6 AM UTC)             │
│                                                     │
│  1. Calculate current week (e.g., 2026-W22)         │
│  2. POST to Render API: /trigger                    │
│  3. Wait 10 minutes for pipeline to complete        │
│  4. Show execution summary                          │
└──────────────────────┬──────────────────────────────┘
                       │
                       ↓
┌─────────────────────────────────────────────────────┐
│  Render API (weeklypulse.onrender.com)              │
│                                                     │
│  1. Receives POST /trigger                          │
│  2. Runs weeklypulse run command                    │
│  3. Pipeline executes:                              │
│     - Ingest reviews                                │
│     - Process & analyze (Groq LLM)                  │
│     - Create Google Doc (MCP)                       │
│     - Create Gmail draft (MCP)                      │
│     - Update manifest                               │
└─────────────────────────────────────────────────────┘
```

---

## ⚠️ **Important Notes:**

### **Free Tier Limits:**
- ✅ GitHub Actions: 2,000 minutes/month (plenty for weekly runs)
- ✅ Render: 750 hours/month free

### **Render Spin-Down:**
- Render spins down after 15 minutes of inactivity
- First request after spin-down takes 30-60 seconds to wake up
- **Solution:** The workflow waits 10 minutes for pipeline completion

### **Manual Override:**
You can manually trigger the workflow anytime from GitHub Actions UI.

---

## 🎯 **Weekly Workflow:**

### **Automated (What happens every Sunday):**
1. ⏰ GitHub Actions triggers at 6 AM UTC
2. 🔄 Calls Render API
3. 📥 Pipeline runs (5-15 minutes)
4. ✅ Google Doc created
5. ✅ Gmail draft created
6. 📧 You review and send the draft manually

### **Your Role:**
- ✅ Check Gmail Drafts on Sunday/Monday
- ✅ Review the draft email
- ✅ Review the Google Doc
- ✅ Click **Send** on the draft

---

## 🛠️ **Troubleshooting:**

### **Issue: Workflow fails to trigger Render**
**Check:**
- Render service is running (not deleted)
- RENDER_API_URL is correct in workflow
- Render logs show any errors

### **Issue: Pipeline runs but fails**
**Check:**
- Render logs for detailed errors
- GROQ_API_KEY secret is set
- GOOGLE_CREDENTIALS_JSON and GOOGLE_TOKEN_JSON are valid
- Google APIs are enabled

### **Issue: Workflow doesn't run on schedule**
**Check:**
- Repository has recent commits (GitHub disables schedules for inactive repos)
- Schedule syntax is correct
- Timezone is UTC

---

## 📝 **Next Steps:**

1. ✅ Add GitHub secrets
2. ✅ Push workflow to GitHub
3. ✅ Test manual trigger
4. ✅ Wait for first automated run (next Sunday)
5. ✅ Monitor and verify results

---

**You're all set for automated weekly execution!** 🎉
