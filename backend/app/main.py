"""
Campus Multilingual Chatbot - Main FastAPI Application
"""

from fastapi import FastAPI, HTTPException, Depends, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer
import uvicorn
import os
from dotenv import load_dotenv

from app.api.routes import chat, auth, admin, webhook, security
from app.core.config import settings
from app.core.database import init_db
from app.core.security import get_current_user
from app.middleware.security_middleware import (
    SecurityHeadersMiddleware,
    RateLimitMiddleware,
    RequestLoggingMiddleware,
    InputValidationMiddleware,
    SecurityAuditMiddleware,
    DataEncryptionMiddleware,
    CSRFProtectionMiddleware,
    SecurityMonitoringMiddleware
)

# Load environment variables
load_dotenv()

# Initialize FastAPI app
app = FastAPI(
    title="LACBOT - Campus Multilingual Chatbot",
    description="A production-ready multilingual chatbot for campus offices",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Add security middleware (order matters!)
app.add_middleware(SecurityMonitoringMiddleware)
app.add_middleware(CSRFProtectionMiddleware)
app.add_middleware(DataEncryptionMiddleware)
app.add_middleware(SecurityAuditMiddleware)
app.add_middleware(InputValidationMiddleware)
app.add_middleware(RequestLoggingMiddleware)
app.add_middleware(RateLimitMiddleware, requests_per_minute=settings.RATE_LIMIT_PER_MINUTE)
app.add_middleware(SecurityHeadersMiddleware)

# Include API routes
app.include_router(auth.router, prefix="/api/auth", tags=["Authentication"])
app.include_router(chat.router, prefix="/api/chat", tags=["Chat"])
app.include_router(admin.router, prefix="/api/admin", tags=["Admin"])
app.include_router(webhook.router, prefix="/api/webhook", tags=["Webhooks"])
app.include_router(security.router, prefix="/api/security", tags=["Security"])

@app.on_event("startup")
async def startup_event():
    """Initialize database and services on startup"""
    await init_db()
    print("🚀 LACBOT API is ready!")

@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown"""
    print("👋 LACBOT API is shutting down")

@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "Welcome to LACBOT - Campus Multilingual Chatbot API",
        "version": "1.0.0",
        "status": "active",
        "docs": "/docs"
    }

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "LACBOT API",
        "timestamp": "2024-01-01T00:00:00Z"
    }

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.DEBUG,
        log_level="info"
    )
