"""
LLM Client for Ollama Integration

This module provides a unified interface for interacting with language models
via Ollama API. It supports any model available in Ollama (openchat, llama2, etc.)

Default Configuration:
- API URL: http://localhost:11434/v1
- Model: openchat:7b
- Timeout: 300 seconds (suitable for CPU inference)

Usage:
    config = LLMConfig.from_env()
    client = LLMClient(config)
    response = client.generate("Write a commit message for...")
"""

import os
import logging
from typing import Optional, Dict, Any, List
from abc import ABC, abstractmethod
import requests
from dataclasses import dataclass


logger = logging.getLogger(__name__)


@dataclass
class LLMConfig:
    """Configuration for LLM client."""
    mode: str = "local"  # "local" or "api"
    model_path: str = "openchat/openchat-3.5-0106"
    device: str = "cuda"
    max_new_tokens: int = 512
    temperature: float = 0.7
    api_base_url: str = "http://localhost:8000/v1"
    api_key: str = ""
    api_model: str = "openchat-3.5"
    use_8bit: bool = False
    top_p: float = 0.9
    
    @classmethod
    def from_env(cls) -> "LLMConfig":
        """Create config from environment variables."""
        return cls(
            mode=os.getenv("LLM_MODE", "local"),
            model_path=os.getenv("LOCAL_MODEL_PATH", "openchat/openchat-3.5-0106"),
            device=os.getenv("DEVICE", "cuda"),
            max_new_tokens=int(os.getenv("MAX_NEW_TOKENS", "512")),
            temperature=float(os.getenv("TEMPERATURE", "0.7")),
            api_base_url=os.getenv("API_BASE_URL", "http://localhost:8000/v1"),
            api_key=os.getenv("API_KEY", ""),
            api_model=os.getenv("API_MODEL", "openchat-3.5"),
            use_8bit=os.getenv("USE_8BIT", "false").lower() == "true",
            top_p=float(os.getenv("TOP_P", "0.9"))
        )


class BaseLLMClient(ABC):
    """Abstract base class for LLM clients."""
    
    @abstractmethod
    def generate(self, prompt: str, **kwargs) -> str:
        """Generate text from prompt."""
        pass
    
    @abstractmethod
    def is_available(self) -> bool:
        """Check if the LLM is available and ready."""
        pass


class LocalLLMClient(BaseLLMClient):
    """Local inference using transformers library."""
    
    def __init__(self, config: LLMConfig):
        self.config = config
        self.model = None
        self.tokenizer = None
        self._initialize_model()
    
    def _initialize_model(self):
        """Initialize the model and tokenizer."""
        try:
            import torch
            from transformers import AutoTokenizer, AutoModelForCausalLM
            
            logger.info(f"Loading model: {self.config.model_path}")
            logger.info(f"Device: {self.config.device}")
            
            # Load tokenizer
            self.tokenizer = AutoTokenizer.from_pretrained(
                self.config.model_path,
                trust_remote_code=True
            )
            
            # Load model
            load_kwargs = {
                "trust_remote_code": True,
                "torch_dtype": torch.float16 if self.config.device == "cuda" else torch.float32
            }
            
            if self.config.use_8bit:
                load_kwargs["load_in_8bit"] = True
                load_kwargs["device_map"] = "auto"
            
            self.model = AutoModelForCausalLM.from_pretrained(
                self.config.model_path,
                **load_kwargs
            )
            
            if not self.config.use_8bit:
                self.model = self.model.to(self.config.device)
            
            self.model.eval()
            logger.info("Model loaded successfully")
            
        except ImportError as e:
            logger.error(f"Failed to import required libraries: {e}")
            logger.error("Please install: pip install torch transformers accelerate")
            raise
        except Exception as e:
            logger.error(f"Failed to initialize model: {e}")
            raise
    
    def generate(self, prompt: str, **kwargs) -> str:
        """
        Generate text using local model.
        
        Args:
            prompt: Input prompt
            **kwargs: Additional generation parameters
            
        Returns:
            Generated text
        """
        if self.model is None or self.tokenizer is None:
            raise RuntimeError("Model not initialized")
        
        try:
            import torch
            
            # Format prompt for OpenChat-3.5
            formatted_prompt = self._format_prompt(prompt)
            
            # Tokenize
            inputs = self.tokenizer(formatted_prompt, return_tensors="pt")
            inputs = inputs.to(self.config.device)
            
            # Generate
            with torch.no_grad():
                outputs = self.model.generate(
                    inputs.input_ids,
                    max_new_tokens=kwargs.get("max_new_tokens", self.config.max_new_tokens),
                    temperature=kwargs.get("temperature", self.config.temperature),
                    top_p=kwargs.get("top_p", self.config.top_p),
                    do_sample=True,
                    pad_token_id=self.tokenizer.eos_token_id
                )
            
            # Decode
            generated_text = self.tokenizer.decode(outputs[0], skip_special_tokens=True)
            
            # Extract only the generated part (remove prompt)
            response = self._extract_response(generated_text, formatted_prompt)
            
            return response.strip()
            
        except Exception as e:
            logger.error(f"Generation failed: {e}")
            raise
    
    def _format_prompt(self, prompt: str) -> str:
        """Format prompt for OpenChat-3.5."""
        # OpenChat-3.5 uses a specific format
        return f"GPT4 Correct User: {prompt}<|end_of_turn|>GPT4 Correct Assistant:"
    
    def _extract_response(self, generated_text: str, prompt: str) -> str:
        """Extract the response from generated text."""
        # Remove the prompt part
        if prompt in generated_text:
            response = generated_text.split(prompt)[-1]
        else:
            response = generated_text
        
        # Remove special tokens
        response = response.replace("<|end_of_turn|>", "").strip()
        
        return response
    
    def is_available(self) -> bool:
        """Check if model is loaded and ready."""
        return self.model is not None and self.tokenizer is not None


class APILLMClient(BaseLLMClient):
    """API-based inference using OpenAI-compatible endpoints."""
    
    def __init__(self, config: LLMConfig):
        self.config = config
        self.session = requests.Session()
        
        if self.config.api_key:
            self.session.headers.update({
                "Authorization": f"Bearer {self.config.api_key}"
            })
    
    def generate(self, prompt: str, **kwargs) -> str:
        """
        Generate text using API.
        
        Args:
            prompt: Input prompt
            **kwargs: Additional generation parameters
            
        Returns:
            Generated text
        """
        try:
            url = f"{self.config.api_base_url.rstrip('/')}/chat/completions"
            
            payload = {
                "model": self.config.api_model,
                "messages": [
                    {"role": "user", "content": prompt}
                ],
                "max_tokens": kwargs.get("max_new_tokens", self.config.max_new_tokens),
                "temperature": kwargs.get("temperature", self.config.temperature),
                "top_p": kwargs.get("top_p", self.config.top_p)
            }
            
            # Increased timeout for Ollama local inference (can be slow on CPU)
            response = self.session.post(url, json=payload, timeout=300)
            response.raise_for_status()
            
            data = response.json()
            
            # Extract content from response
            if "choices" in data and len(data["choices"]) > 0:
                return data["choices"][0]["message"]["content"].strip()
            else:
                raise ValueError("Invalid API response format")
                
        except requests.exceptions.RequestException as e:
            logger.error(f"API request failed: {e}")
            raise
        except Exception as e:
            logger.error(f"Generation failed: {e}")
            raise
    
    def is_available(self) -> bool:
        """Check if API is accessible."""
        try:
            url = f"{self.config.api_base_url.rstrip('/')}/models"
            response = self.session.get(url, timeout=5)
            return response.status_code == 200
        except:
            return False


class LLMClient:
    """
    Unified LLM client that automatically selects between local and API modes.
    
    Usage:
        config = LLMConfig.from_env()
        client = LLMClient(config)
        response = client.generate("Your prompt here")
    """
    
    def __init__(self, config: Optional[LLMConfig] = None):
        """
        Initialize LLM client.
        
        Args:
            config: LLM configuration. If None, loads from environment.
        """
        self.config = config or LLMConfig.from_env()
        self.client: BaseLLMClient = self._create_client()
        
        logger.info(f"Initialized LLM client in {self.config.mode} mode")
    
    def _create_client(self) -> BaseLLMClient:
        """Create appropriate client based on mode."""
        if self.config.mode == "local":
            return LocalLLMClient(self.config)
        elif self.config.mode == "api":
            return APILLMClient(self.config)
        else:
            raise ValueError(f"Invalid LLM mode: {self.config.mode}")
    
    def generate(self, prompt: str, **kwargs) -> str:
        """
        Generate text from prompt.
        
        Args:
            prompt: Input prompt
            **kwargs: Additional generation parameters
            
        Returns:
            Generated text
        """
        return self.client.generate(prompt, **kwargs)
    
    def is_available(self) -> bool:
        """Check if LLM is available."""
        return self.client.is_available()
    
    def __repr__(self) -> str:
        return f"LLMClient(mode={self.config.mode}, model={self.config.model_path})"


# Convenience function for quick usage
def create_llm_client(mode: Optional[str] = None) -> LLMClient:
    """
    Create an LLM client with optional mode override.
    
    Args:
        mode: Optional mode override ("local" or "api")
        
    Returns:
        Configured LLM client
    """
    config = LLMConfig.from_env()
    if mode:
        config.mode = mode
    return LLMClient(config)
