"""
Configuration Module

Loads and validates application configuration from environment variables.
Settings are loaded from the .env file in the project root.

Default Configuration (optimized for Ollama):
    - LLM_MODE: "api" (uses Ollama)
    - API_BASE_URL: "http://localhost:11434/v1" (Ollama default)
    - API_MODEL: "openchat:7b"
    - DEBUG_MODE: true
    - COMMIT_STYLE: "conventional"

To customize, edit the .env file.
"""

import os
from pathlib import Path
from dotenv import load_dotenv
from typing import Optional


# Load .env file if it exists
env_path = Path(__file__).parent / '.env'
if env_path.exists():
    load_dotenv(env_path)


class Config:
    """
    Application configuration loaded from environment variables.
    
    All settings can be customized via the .env file.
    
    LLM Settings:
        LLM_MODE: "api" (Ollama) or "local" (HuggingFace transformers)
        API_BASE_URL: Ollama endpoint (default: http://localhost:11434/v1)
        API_MODEL: Model name in Ollama (default: openchat:7b)
        API_KEY: Any value (Ollama doesn't require auth)
        
    Pipeline Settings:
        DEBUG_MODE: Show intermediate outputs (default: true)
        LOG_LEVEL: Logging verbosity (default: INFO)
        COMMIT_STYLE: Message format (default: conventional)
        
    Git Settings:
        GIT_REPO_PATH: Target repository (default: current directory)
    """
    
    # LLM Configuration (Ollama by default)
    LLM_MODE: str = os.getenv("LLM_MODE", "api")
    LOCAL_MODEL_PATH: str = os.getenv("LOCAL_MODEL_PATH", "openchat/openchat-3.5-0106")
    DEVICE: str = os.getenv("DEVICE", "cpu")
    MAX_NEW_TOKENS: int = int(os.getenv("MAX_NEW_TOKENS", "512"))
    TEMPERATURE: float = float(os.getenv("TEMPERATURE", "0.7"))
    
    # API Configuration (Ollama defaults)
    API_BASE_URL: str = os.getenv("API_BASE_URL", "http://localhost:11434/v1")
    API_KEY: str = os.getenv("API_KEY", "ollama")
    API_MODEL: str = os.getenv("API_MODEL", "openchat:7b")
    
    # Git Configuration
    GIT_REPO_PATH: str = os.getenv("GIT_REPO_PATH", ".")
    
    # Pipeline Configuration
    DEBUG_MODE: bool = os.getenv("DEBUG_MODE", "false").lower() == "true"
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")
    COMMIT_STYLE: str = os.getenv("COMMIT_STYLE", "conventional")
    
    # Optional features
    USE_8BIT: bool = os.getenv("USE_8BIT", "false").lower() == "true"
    USE_LLM_FOR_DIFF: bool = os.getenv("USE_LLM_FOR_DIFF", "false").lower() == "true"
    
    @classmethod
    def validate(cls) -> bool:
        """Validate configuration."""
        errors = []
        
        if cls.LLM_MODE not in ["local", "api"]:
            errors.append(f"Invalid LLM_MODE: {cls.LLM_MODE} (must be 'local' or 'api')")
        
        if cls.DEVICE not in ["cuda", "cpu", "mps"]:
            errors.append(f"Invalid DEVICE: {cls.DEVICE} (must be 'cuda', 'cpu', or 'mps')")
        
        if cls.COMMIT_STYLE not in ["conventional", "angular", "gitmoji"]:
            errors.append(f"Invalid COMMIT_STYLE: {cls.COMMIT_STYLE}")
        
        if errors:
            for error in errors:
                print(f"Configuration Error: {error}")
            return False
        
        return True
    
    @classmethod
    def display(cls):
        """Display current configuration."""
        print("\n" + "="*60)
        print("CONFIGURATION")
        print("="*60)
        print(f"LLM Mode:          {cls.LLM_MODE}")
        if cls.LLM_MODE == "local":
            print(f"Model:             {cls.LOCAL_MODEL_PATH}")
            print(f"Device:            {cls.DEVICE}")
            print(f"8-bit Loading:     {cls.USE_8BIT}")
        else:
            print(f"API URL:           {cls.API_BASE_URL}")
            print(f"API Model:         {cls.API_MODEL}")
        print(f"Repository:        {cls.GIT_REPO_PATH}")
        print(f"Commit Style:      {cls.COMMIT_STYLE}")
        print(f"Debug Mode:        {cls.DEBUG_MODE}")
        print(f"Log Level:         {cls.LOG_LEVEL}")
        print("="*60 + "\n")


# Validate config on import
if not Config.validate():
    print("\nPlease check your .env file configuration.")
    print("Copy .env.example to .env and update the values.\n")
