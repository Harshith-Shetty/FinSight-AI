# Quick Start Guide

## 🚀 Quick Start (5 minutes)

### 1. Setup Environment
```powershell
# Copy environment template
.\setup.ps1

# Edit .env and add your Groq API key
# Get free key at: https://console.groq.com
```

### 2. Start Infrastructure
```powershell
.\start-infra.ps1
```

This starts PostgreSQL, Redis, and Qdrant in Docker.

### 3. Install Dependencies
```powershell
pip install -r requirements.txt
```

### 4. Run Application (2 terminals)

**Terminal 1 - API Server:**
```powershell
.\run-api.ps1
```

**Terminal 2 - Celery Worker:**
```powershell
.\run-worker.ps1
```

### 5. Test the API

**Submit Analysis:**
```powershell
curl -X POST http://localhost:8000/api/v1/analyze `
  -H "Content-Type: application/json" `
  -d '{\"ticker\": \"AAPL\", \"focus_area\": \"risk_factors\", \"filing_year\": 2024}'
```

**Check Status:**
```powershell
curl http://localhost:8000/api/v1/tasks/{task_id}
```

**View Docs:**
Open http://localhost:8000/docs

---

## 🔄 Switch LLM Provider

**Development (Groq - Fast & Free):**
```env
LLM_PROVIDER=groq
GROQ_API_KEY=gsk_xxxxx
```

**Production (Ollama on AWS):**
```env
LLM_PROVIDER=ollama
OLLAMA_BASE_URL=http://your-ec2-ip:11434
```

Restart worker to apply changes.

---

## 🧪 Run Tests

```powershell
pytest tests/ -v
```

---

## 🛑 Stop Services

```powershell
docker-compose down
```
