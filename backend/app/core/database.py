"""
Database configuration and connection management
"""

from supabase import create_client, Client
from app.core.config import settings
import logging

logger = logging.getLogger(__name__)

# Initialize Supabase client
supabase: Client = create_client(settings.SUPABASE_URL, settings.SUPABASE_KEY)

async def init_db():
    """Initialize database connection and tables"""
    try:
        # Test connection
        result = supabase.table("health_check").select("*").limit(1).execute()
        logger.info("✅ Database connection established")
    except Exception as e:
        logger.error(f"❌ Database connection failed: {e}")
        raise

def get_supabase_client() -> Client:
    """Get Supabase client instance"""
    return supabase

# Database table schemas
TABLES = {
    "users": {
        "id": "uuid PRIMARY KEY DEFAULT gen_random_uuid()",
        "email": "varchar UNIQUE NOT NULL",
        "username": "varchar UNIQUE NOT NULL",
        "full_name": "varchar NOT NULL",
        "role": "varchar DEFAULT 'user'",
        "language_preference": "varchar DEFAULT 'en'",
        "created_at": "timestamp DEFAULT now()",
        "updated_at": "timestamp DEFAULT now()"
    },
    "conversations": {
        "id": "uuid PRIMARY KEY DEFAULT gen_random_uuid()",
        "user_id": "uuid REFERENCES users(id)",
        "session_id": "varchar NOT NULL",
        "language": "varchar NOT NULL",
        "created_at": "timestamp DEFAULT now()",
        "updated_at": "timestamp DEFAULT now()"
    },
    "messages": {
        "id": "uuid PRIMARY KEY DEFAULT gen_random_uuid()",
        "conversation_id": "uuid REFERENCES conversations(id)",
        "user_message": "text NOT NULL",
        "bot_response": "text NOT NULL",
        "confidence_score": "float DEFAULT 0.0",
        "requires_human": "boolean DEFAULT false",
        "language": "varchar NOT NULL",
        "created_at": "timestamp DEFAULT now()"
    },
    "documents": {
        "id": "uuid PRIMARY KEY DEFAULT gen_random_uuid()",
        "title": "varchar NOT NULL",
        "content": "text NOT NULL",
        "language": "varchar NOT NULL",
        "document_type": "varchar NOT NULL",
        "file_path": "varchar",
        "created_by": "uuid REFERENCES users(id)",
        "created_at": "timestamp DEFAULT now()",
        "updated_at": "timestamp DEFAULT now()"
    },
    "embeddings": {
        "id": "uuid PRIMARY KEY DEFAULT gen_random_uuid()",
        "document_id": "uuid REFERENCES documents(id)",
        "chunk_text": "text NOT NULL",
        "embedding": "vector(384)",
        "metadata": "jsonb",
        "created_at": "timestamp DEFAULT now()"
    },
    "faqs": {
        "id": "uuid PRIMARY KEY DEFAULT gen_random_uuid()",
        "question": "text NOT NULL",
        "answer": "text NOT NULL",
        "category": "varchar NOT NULL",
        "language": "varchar NOT NULL",
        "priority": "integer DEFAULT 1",
        "is_active": "boolean DEFAULT true",
        "created_at": "timestamp DEFAULT now()",
        "updated_at": "timestamp DEFAULT now()"
    },
    "notifications": {
        "id": "uuid PRIMARY KEY DEFAULT gen_random_uuid()",
        "user_id": "uuid REFERENCES users(id)",
        "title": "varchar NOT NULL",
        "message": "text NOT NULL",
        "type": "varchar NOT NULL",
        "is_read": "boolean DEFAULT false",
        "created_at": "timestamp DEFAULT now()"
    }
}
