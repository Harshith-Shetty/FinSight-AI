"""
FastAPI application entry point.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from app.core.config import settings
from app.core.database import init_db, close_db
from app.api.routes import analyze, tasks, auth, documents, chats, messages, public_documents, admin, users


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Lifespan context manager for startup and shutdown events.
    """
    # Startup
    print(f"Starting {settings.APP_NAME} v{settings.APP_VERSION}")
    print(f"LLM Provider: {settings.LLM_PROVIDER.upper()}")
    
    # Initialize database connection
    await init_db()
    print("Database initialized")
    
    # Run migrations automatically
    from app.services.migrations import run_migrations, verify_database
    await run_migrations()
    await verify_database()
    
    yield
    
    # Shutdown
    print("Shutting down...")
    await close_db()
    print("Database connections closed")


# Create FastAPI app
app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="Asynchronous Financial Intelligence Microservice using RAG",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(auth.router)
app.include_router(documents.router)
app.include_router(chats.router, prefix="/api/v1", tags=["Chats"])
app.include_router(messages.router, prefix="/api/v1", tags=["Messages"])
app.include_router(analyze.router, prefix="/api/v1", tags=["Analysis"])
app.include_router(tasks.router, prefix="/api/v1", tags=["Tasks"])
app.include_router(public_documents.router)  # /api/v1/public-documents
app.include_router(admin.router)             # /api/v1/admin
app.include_router(users.router)             # /api/v1/users




@app.get("/")
async def root():
    """Root endpoint - health check."""
    return {
        "name": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "status": "running",
        "llm_provider": settings.LLM_PROVIDER
    }


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.DEBUG
    )
