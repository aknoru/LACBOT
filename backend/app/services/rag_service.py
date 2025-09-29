"""
RAG (Retrieval-Augmented Generation) Service for Multilingual Chatbot
"""

import os
import logging
from typing import List, Dict, Any, Optional, Tuple
from sentence_transformers import SentenceTransformer
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.vectorstores import Chroma
from langchain.embeddings import HuggingFaceEmbeddings
from langchain.llms import HuggingFacePipeline
from langchain.chains import RetrievalQA
from langchain.prompts import PromptTemplate
import torch
from transformers import AutoTokenizer, AutoModelForCausalLM, pipeline
from app.core.config import settings, MODEL_CONFIG
from app.core.database import get_supabase_client

logger = logging.getLogger(__name__)

class RAGService:
    """RAG service for multilingual chatbot"""
    
    def __init__(self):
        self.embedding_model = None
        self.llm_model = None
        self.translation_model = None
        self.vector_store = None
        self.retriever = None
        self.qa_chain = None
        self.supabase = get_supabase_client()
        
        # Initialize models
        self._initialize_models()
        self._initialize_vector_store()
        self._initialize_qa_chain()
    
    def _initialize_models(self):
        """Initialize AI models"""
        try:
            logger.info("🤖 Initializing AI models...")
            
            # Initialize embedding model
            self.embedding_model = HuggingFaceEmbeddings(
                model_name=MODEL_CONFIG["embedding_model"],
                model_kwargs={'device': 'cpu'}  # Use CPU for cost efficiency
            )
            
            # Initialize translation model
            self.translation_model = pipeline(
                "translation",
                model=MODEL_CONFIG["translation_model"],
                device=0 if torch.cuda.is_available() else -1
            )
            
            logger.info("✅ Models initialized successfully")
            
        except Exception as e:
            logger.error(f"❌ Model initialization failed: {e}")
            raise
    
    def _initialize_vector_store(self):
        """Initialize vector store for document retrieval"""
        try:
            logger.info("📚 Initializing vector store...")
            
            # Create vector store directory
            persist_directory = "./data/chroma_db"
            os.makedirs(persist_directory, exist_ok=True)
            
            # Initialize ChromaDB
            self.vector_store = Chroma(
                persist_directory=persist_directory,
                embedding_function=self.embedding_model
            )
            
            logger.info("✅ Vector store initialized")
            
        except Exception as e:
            logger.error(f"❌ Vector store initialization failed: {e}")
            raise
    
    def _initialize_qa_chain(self):
        """Initialize QA chain for question answering"""
        try:
            logger.info("🔗 Initializing QA chain...")
            
            # Create retriever
            self.retriever = self.vector_store.as_retriever(
                search_kwargs={"k": 5}  # Retrieve top 5 relevant documents
            )
            
            # Create prompt template
            prompt_template = """
            You are a helpful multilingual assistant for a college campus. 
            Answer the student's question based on the provided context.
            
            Context: {context}
            
            Question: {question}
            
            Instructions:
            1. Answer in the same language as the question
            2. Be accurate and helpful
            3. If you don't know the answer, say so
            4. Provide relevant contact information if needed
            
            Answer: """
            
            PROMPT = PromptTemplate(
                template=prompt_template,
                input_variables=["context", "question"]
            )
            
            # Initialize QA chain
            self.qa_chain = RetrievalQA.from_chain_type(
                llm=self._get_llm(),
                chain_type="stuff",
                retriever=self.retriever,
                chain_type_kwargs={"prompt": PROMPT},
                return_source_documents=True
            )
            
            logger.info("✅ QA chain initialized")
            
        except Exception as e:
            logger.error(f"❌ QA chain initialization failed: {e}")
            raise
    
    def _get_llm(self):
        """Get LLM for text generation"""
        try:
            # Use a lightweight model for cost efficiency
            model_name = "microsoft/DialoGPT-medium"  # Free alternative
            
            tokenizer = AutoTokenizer.from_pretrained(model_name)
            model = AutoModelForCausalLM.from_pretrained(model_name)
            
            # Create pipeline
            pipe = pipeline(
                "text-generation",
                model=model,
                tokenizer=tokenizer,
                max_length=512,
                temperature=0.7,
                do_sample=True,
                pad_token_id=tokenizer.eos_token_id
            )
            
            return HuggingFacePipeline(pipeline=pipe)
            
        except Exception as e:
            logger.error(f"❌ LLM initialization failed: {e}")
            # Fallback to a simple text generator
            return None
    
    def detect_language(self, text: str) -> str:
        """Detect language of input text"""
        # Simple language detection based on script
        if any('\u0900' <= char <= '\u097F' for char in text):  # Devanagari
            return "hi"
        elif any('\u0B80' <= char <= '\u0BFF' for char in text):  # Tamil
            return "ta"
        elif any('\u0C00' <= char <= '\u0C7F' for char in text):  # Telugu
            return "te"
        elif any('\u0980' <= char <= '\u09FF' for char in text):  # Bengali
            return "bn"
        elif any('\u0A80' <= char <= '\u0AFF' for char in text):  # Gujarati
            return "gu"
        else:
            return "en"  # Default to English
    
    def translate_text(self, text: str, target_lang: str) -> str:
        """Translate text to target language"""
        try:
            if target_lang == "en":
                return text
            
            # Language code mapping for NLLB model
            lang_codes = {
                "hi": "hin_Deva",
                "ta": "tam_Taml",
                "te": "tel_Telu",
                "bn": "ben_Beng",
                "mr": "mar_Deva",
                "gu": "guj_Gujr"
            }
            
            if target_lang not in lang_codes:
                return text
            
            result = self.translation_model(
                text,
                src_lang="eng_Latn",
                tgt_lang=lang_codes[target_lang],
                max_length=512
            )
            
            return result[0]["translation_text"]
            
        except Exception as e:
            logger.error(f"❌ Translation failed: {e}")
            return text
    
    def add_documents(self, documents: List[Dict[str, Any]]):
        """Add documents to the vector store"""
        try:
            logger.info(f"📄 Adding {len(documents)} documents to vector store")
            
            # Prepare documents for LangChain
            from langchain.docstore.document import Document
            
            langchain_docs = []
            for doc in documents:
                langchain_docs.append(Document(
                    page_content=doc["content"],
                    metadata={
                        "title": doc["title"],
                        "language": doc["language"],
                        "document_type": doc["document_type"],
                        "id": doc["id"]
                    }
                ))
            
            # Split documents into chunks
            text_splitter = RecursiveCharacterTextSplitter(
                chunk_size=MODEL_CONFIG["chunk_size"],
                chunk_overlap=MODEL_CONFIG["chunk_overlap"]
            )
            
            split_docs = text_splitter.split_documents(langchain_docs)
            
            # Add to vector store
            self.vector_store.add_documents(split_docs)
            self.vector_store.persist()
            
            logger.info("✅ Documents added successfully")
            
        except Exception as e:
            logger.error(f"❌ Failed to add documents: {e}")
            raise
    
    def search_similar_documents(self, query: str, language: str = "en") -> List[Dict[str, Any]]:
        """Search for similar documents"""
        try:
            # Translate query to English if needed
            if language != "en":
                query = self.translate_text(query, "en")
            
            # Search vector store
            docs = self.vector_store.similarity_search(
                query,
                k=5,
                filter={"language": language}
            )
            
            # Format results
            results = []
            for doc in docs:
                results.append({
                    "content": doc.page_content,
                    "metadata": doc.metadata,
                    "score": 0.8  # Placeholder score
                })
            
            return results
            
        except Exception as e:
            logger.error(f"❌ Document search failed: {e}")
            return []
    
    def generate_response(self, question: str, language: str = "en", context: Optional[str] = None) -> Dict[str, Any]:
        """Generate response using RAG"""
        try:
            # Detect language if not provided
            if language == "auto":
                language = self.detect_language(question)
            
            # Translate question to English for processing
            english_question = question
            if language != "en":
                english_question = self.translate_text(question, "en")
            
            # Generate response
            if self.qa_chain:
                result = self.qa_chain({"query": english_question})
                response = result["result"]
                source_docs = result["source_documents"]
            else:
                # Fallback response
                response = "I'm sorry, I'm having trouble processing your request right now. Please try again later."
                source_docs = []
            
            # Translate response back to original language
            if language != "en":
                response = self.translate_text(response, language)
            
            # Calculate confidence score
            confidence_score = self._calculate_confidence(question, response, source_docs)
            
            # Check if human intervention is needed
            requires_human = confidence_score < MODEL_CONFIG["similarity_threshold"]
            
            return {
                "response": response,
                "confidence_score": confidence_score,
                "language": language,
                "requires_human": requires_human,
                "source_documents": [doc.metadata for doc in source_docs],
                "timestamp": "2024-01-01T00:00:00Z"
            }
            
        except Exception as e:
            logger.error(f"❌ Response generation failed: {e}")
            return {
                "response": "I apologize, but I'm experiencing technical difficulties. Please contact our support team for assistance.",
                "confidence_score": 0.0,
                "language": language,
                "requires_human": True,
                "source_documents": [],
                "timestamp": "2024-01-01T00:00:00Z"
            }
    
    def _calculate_confidence(self, question: str, response: str, source_docs: List) -> float:
        """Calculate confidence score for the response"""
        try:
            if not source_docs:
                return 0.0
            
            # Simple confidence calculation based on source relevance
            base_confidence = 0.7
            
            # Increase confidence if we have multiple relevant sources
            if len(source_docs) >= 3:
                base_confidence += 0.2
            
            # Increase confidence if response is substantial
            if len(response) > 50:
                base_confidence += 0.1
            
            return min(base_confidence, 1.0)
            
        except Exception as e:
            logger.error(f"❌ Confidence calculation failed: {e}")
            return 0.5

# Global RAG service instance
rag_service = RAGService()
