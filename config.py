"""
Configuration module for Chinese TTS Video Generator
"""
import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Base directory
BASE_DIR = Path(__file__).parent

# Flask Configuration
class Config:
    """Base configuration"""
    SECRET_KEY = os.getenv('SECRET_KEY', 'dev-key-change-in-production')
    DEBUG = False
    TESTING = False
    
    # Upload configuration
    MAX_CONTENT_LENGTH = int(os.getenv('MAX_CONTENT_LENGTH', 104857600))  # 100MB
    UPLOAD_FOLDER = Path(os.getenv('UPLOAD_FOLDER', 'uploads'))
    MAX_VIDEO_FILES = int(os.getenv('MAX_VIDEO_FILES', 10))  # Max number of video files to keep
    UPLOAD_FOLDER.mkdir(exist_ok=True)
    
    # TTS Configuration
    FONT_PATH = os.getenv('FONT_PATH', 'models/msyh.ttc')
    
    # Video Configuration
    BG_IMAGE = os.getenv('BG_IMAGE', 'background.png')
    OUTPUT_FOLDER = Path(os.getenv('OUTPUT_FOLDER', 'data'))
    OUTPUT_FOLDER.mkdir(exist_ok=True)
    
    # Cleanup Configuration
    # VIDEO_RETENTION_HOURS = int(os.getenv('VIDEO_RETENTION_HOURS', 24))
    
    # Server Configuration
    HOST = os.getenv('HOST', '0.0.0.0')
    PORT = int(os.getenv('PORT', 5000))
    FLASK_DEBUG = os.getenv('FLASK_DEBUG', 'False').lower() in ['true', '1', 't']


class DevelopmentConfig(Config):
    """Development configuration"""
    DEBUG = True
    FLASK_ENV = 'development'


class ProductionConfig(Config):
    """Production configuration"""
    DEBUG = False
    FLASK_ENV = 'production'
    SECRET_KEY = os.getenv('SECRET_KEY')  # Must be set in production
    
    if not SECRET_KEY:
        raise ValueError("SECRET_KEY environment variable must be set in production")


class TestingConfig(Config):
    """Testing configuration"""
    TESTING = True
    DEBUG = True


# Configuration selector
config_name = os.getenv('FLASK_ENV', 'development')
if config_name == 'production':
    config = ProductionConfig
elif config_name == 'testing':
    config = TestingConfig
else:
    config = DevelopmentConfig
