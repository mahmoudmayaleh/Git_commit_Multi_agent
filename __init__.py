"""
Git Commit Writer Pipeline
Version 1.0.0
"""

__version__ = "1.0.0"
__author__ = "AI Assistant"
__description__ = "Automated Git commit message generation using OpenChat-3.5 LLM"

from pipeline import CommitPipeline, create_pipeline
from state import PipelineState
from llm_client import LLMClient
from config import Config

__all__ = [
    "CommitPipeline",
    "create_pipeline",
    "PipelineState",
    "LLMClient",
    "Config",
]
