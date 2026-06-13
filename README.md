# FinSight AI

**FinSight AI** is a full-stack, event-driven financial analysis microservice that leverages Retrieval-Augmented Generation (RAG) to provide deep, contextual insights into financial documents like SEC filings. 

The application features a modern Next.js frontend and a high-performance FastAPI backend, processing AI inference asynchronously via Celery and Redis to ensure a fast, non-blocking user experience.

---

## 🎯 Key Features

- **Semantic Search**: Upload documents and instantly chat with them using Qdrant vector search and `sentence-transformers` embeddings.
- **Asynchronous Processing**: Non-blocking API leveraging Celery and Redis for heavy AI and data ingestion workloads.
- **Provider Agnostic LLM**: Effortlessly switch between Groq API (for fast development) and self-hosted AWS Ollama models using a single environment variable.
- **Modern Tech Stack**: Built with Next.js 16, React 19, Tailwind CSS v4, FastAPI, SQLAlchemy 2.0 Async, and PostgreSQL.
- **Automated Deployments**: CI/CD pipelines via GitHub Actions for seamless AWS EC2 deployment.

---

## 🔧 Tech Stack

- **Frontend**: Next.js 16 (App Router), React 19, Tailwind CSS v4, shadcn/ui
- **Backend**: FastAPI, Python 3.12, Celery
- **Database**: PostgreSQL (via SQLAlchemy 2.0 asyncpg)
- **Vector Store**: Qdrant
- **Message Broker**: Redis
- **AI/ML**: `sentence-transformers`, Groq / Ollama

---

## 🚀 Quick Start Guide

### Prerequisites
- Docker & Docker Compose
- Python 3.11+
- Node.js 18+ & npm
- A Groq API Key (Free from [console.groq.com](https://console.groq.com))

### 1. Setup Environment
Clone the repository and set up your environment variables:
```bash
git clone https://github.com/Harshith-Shetty/FinSight-AI.git
cd FinSight-AI

# Create your .env file
cp .env.example .env
```
Edit `.env` and add your `GROQ_API_KEY`.

### 2. Start Infrastructure
Run the necessary databases (PostgreSQL, Redis, Qdrant) via Docker:
```bash
docker-compose up -d
```

### 3. Backend Setup
Set up the Python virtual environment and install dependencies:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

Start the FastAPI Server (Terminal 1):
```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Start the Celery Worker (Terminal 2):
```bash
# On Mac/Linux:
celery -A app.worker.celery_app worker --loglevel=info

# On Windows:
celery -A app.worker.celery_app worker --loglevel=info --pool=solo
```

### 4. Frontend Setup
Install dependencies and run the Next.js development server (Terminal 3):
```bash
cd finsight-frontend
npm install
npm run dev
```

The application will be available at [http://localhost:3000](http://localhost:3000). 
The Backend API Swagger Docs are available at [http://localhost:8000/docs](http://localhost:8000/docs).

---

## 🔄 Switching LLM Providers

The application uses a Factory Pattern to effortlessly switch LLMs without code changes.

**To use Groq (Development)**:
```env
LLM_PROVIDER=groq
GROQ_API_KEY=gsk_your_api_key_here
```

**To use Ollama (Production/Self-Hosted)**:
```env
LLM_PROVIDER=ollama
OLLAMA_BASE_URL=http://your-ollama-server-ip:11434
```