import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    # Flask
    FLASK_ENV = 'development'
    DEBUG = True
    SECRET_KEY = os.getenv('SECRET_KEY', 'dev-secret-key-change-in-prod')
    
    # LLM API Keys
    GOOGLE_API_KEY = os.getenv('GOOGLE_API_KEY')
    OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
    SERPAPI_API_KEY = os.getenv('SERPAPI_API_KEY')
    YOUTUBE_TRANSCRIPT_IO_API_KEY = os.getenv('YOUTUBE_TRANSCRIPT_IO_API_KEY')
    
    # Model Settings
    SUMMARIZATION_MODEL = 'google'  # 'google', 'openai' or 'ollama' etc
    MAX_SUMMARY_LENGTH = 200000
    NUM_QUIZ_QUESTIONS = 5
    
    # Web Scraping
    REQUEST_TIMEOUT = 10
    MAX_CONTENT_LENGTH = 100000
    
    # Guardrails
    MIN_SUMMARY_LENGTH = 100
    MAX_SUMMARY_LENGTH = 200000
    ALLOWED_CONTENT_TYPES = ['text', 'video', 'article']

config = Config()
