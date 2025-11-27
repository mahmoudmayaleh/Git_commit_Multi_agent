"""
Base Agent Class

Defines the abstract interface that all pipeline agents must implement.
"""

from abc import ABC, abstractmethod
import logging
from typing import Optional
from src.state import PipelineState


logger = logging.getLogger(__name__)


class BaseAgent(ABC):
    """
    Abstract base class for all pipeline agents.
    
    All agents must implement the process() method which takes a PipelineState
    and returns an updated PipelineState.
    """
    
    def __init__(self, name: Optional[str] = None):
        """
        Initialize the agent.
        
        Args:
            name: Optional custom name for the agent
        """
        self.name = name or self.__class__.__name__
        self.logger = logging.getLogger(f"agents.{self.name}")
    
    @abstractmethod
    def process(self, state: PipelineState) -> PipelineState:
        """
        Process the pipeline state.
        
        Args:
            state: Current pipeline state
            
        Returns:
            Updated pipeline state
        """
        pass
    
    def validate_input(self, state: PipelineState) -> bool:
        """
        Validate that the state has required inputs for this agent.
        Override in subclasses for custom validation.
        
        Args:
            state: Pipeline state to validate
            
        Returns:
            True if valid, False otherwise
        """
        return True
    
    def log_start(self):
        """Log agent start."""
        self.logger.info(f"{'='*60}")
        self.logger.info(f"Starting {self.name}")
        self.logger.info(f"{'='*60}")
    
    def log_end(self):
        """Log agent completion."""
        self.logger.info(f"{self.name} completed successfully")
        self.logger.info(f"{'='*60}\n")
    
    def log_error(self, error: Exception):
        """Log agent error."""
        self.logger.error(f"{self.name} failed: {error}")
    
    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(name={self.name})"
