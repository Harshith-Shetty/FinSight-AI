# FinSight AI - Complete Setup Guide

## ✅ Prerequisites Check
- [x] Docker installed (v27.2.0)
- [x] Docker Compose installed (v2.29.2)
- [x] Python installed (3.10.0)
- [x] Virtual environment created

---

## 📋 Step-by-Step Setup

### Step 1: Activate Virtual Environment ✅ **DO THIS FIRST**

**PowerShell:**
```powershell
.\venv\Scripts\Activate.ps1
```

**You should see `(venv)` in your terminal prompt**

---

### Step 2: Install Python Dependencies

```powershell
pip install --upgrade pip
pip install -r requirements.txt
```

This will install:
- FastAPI, Uvicorn
- SQLAlchemy, AsyncPG
- Celery, Redis
- Groq, sentence-transformers
- Qdrant client
- And more...

**Expected time:** 2-3 minutes

---

### Step 3: Get Groq API Key (FREE)

1. Go to: https://console.groq.com
2. Sign up with Google/GitHub (takes 30 seconds)
3. Click "Create API Key"
4. Copy the key (starts with `gsk_...`)

**Keep this key handy for the next step!**

---

### Step 4: Configure Environment

```powershell
# Create .env file from template
Copy-Item .env.example .env

# Open .env in your editor
code .env
# OR
notepad .env
```

**Edit the `.env` file and add your Groq API key:**
```env
# Change this line:
GROQ_API_KEY=your_groq_api_key_here

# To:
GROQ_API_KEY=gsk_your_actual_key_here
```

**Save and close the file.**

---

### Step 5: Start Docker Infrastructure

```powershell
docker-compose up -d
```

This starts:
- PostgreSQL (database)
- Redis (message queue)
- Qdrant (vector database)

**Check if running:**
```powershell
docker-compose ps
```

You should see 3 containers running.

---

### Step 6: Run the Application (2 Terminals)

**Terminal 1 - API Server:**
```powershell
# Make sure venv is activated!
.\venv\Scripts\Activate.ps1

# Run API
python -m uvicorn app.main:app --reload
```

**Wait for:** `Application startup complete`

**Terminal 2 - Celery Worker:**
```powershell
# Make sure venv is activated!
.\venv\Scripts\Activate.ps1

# Run worker
celery -A app.worker.celery_app worker --loglevel=info --pool=solo
```

**Wait for:** `celery@... ready`

---

### Step 7: Test the System! 🎉

**Open a 3rd terminal and test:**

```powershell
# Health check
curl http://localhost:8000/health

# Submit analysis
curl -X POST http://localhost:8000/api/v1/analyze `
  -H "Content-Type: application/json" `
  -d '{\"ticker\": \"AAPL\", \"focus_area\": \"risk_factors\", \"filing_year\": 2024}'
```

**You'll get a response with a `task_id`. Copy it!**

**Check task status:**
```powershell
curl http://localhost:8000/api/v1/tasks/{paste-task-id-here}
```

**View API Docs:**
Open browser: http://localhost:8000/docs

---

## 🎯 Current Step

**YOU ARE HERE:** ✅ Virtual environment created

**NEXT STEP:** Activate venv and install dependencies

---

## 🆘 Troubleshooting

### Virtual Environment Won't Activate
```powershell
# If you get execution policy error:
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

### Docker Containers Won't Start
```powershell
# Check Docker Desktop is running
# Then try:
docker-compose down
docker-compose up -d
```

### Import Errors
```powershell
# Make sure venv is activated (you should see (venv) in prompt)
# Then reinstall:
pip install -r requirements.txt
```

---

## 📝 Quick Commands Reference

```powershell
# Activate venv
.\venv\Scripts\Activate.ps1

# Install dependencies
pip install -r requirements.txt

# Start infrastructure
docker-compose up -d

# Run API (Terminal 1)
python -m uvicorn app.main:app --reload

# Run worker (Terminal 2)
celery -A app.worker.celery_app worker --loglevel=info --pool=solo

# Stop infrastructure
docker-compose down

# Deactivate venv
deactivate
```
