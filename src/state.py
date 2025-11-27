"""
Pipeline State Management

This module defines the central state object that flows through all agents
in the commit message generation pipeline.
"""

from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any
from datetime import datetime
import json


@dataclass
class PipelineState:
    """
    Central state object that tracks data flow between agents.
    
    Attributes:
        staged_diff: Raw output from 'git diff --staged'
        bullet_points: List of parsed changes from DiffAgent
        summary: Concise summary from SummaryAgent
        commit_message: Final commit message from CommitWriterAgent
        errors: List of errors encountered during processing
        metadata: Additional metadata for debugging and tracking
    """
    staged_diff: Optional[str] = None
    bullet_points: Optional[List[str]] = None
    summary: Optional[str] = None
    commit_message: Optional[str] = None
    errors: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def __post_init__(self):
        """Initialize metadata with timestamp."""
        if "created_at" not in self.metadata:
            self.metadata["created_at"] = datetime.now().isoformat()
    
    def add_error(self, error: str, agent: str = "Unknown") -> None:
        """
        Add an error to the state.
        
        Args:
            error: Error message
            agent: Name of the agent that encountered the error
        """
        error_msg = f"[{agent}] {error}"
        self.errors.append(error_msg)
        self.metadata.setdefault("error_count", 0)
        self.metadata["error_count"] += 1
    
    def has_errors(self) -> bool:
        """Check if any errors were encountered."""
        return len(self.errors) > 0
    
    def is_ready_for_agent(self, agent_name: str) -> bool:
        """
        Check if state has required data for a specific agent.
        
        Args:
            agent_name: Name of the agent (DiffAgent, SummaryAgent, CommitWriterAgent)
            
        Returns:
            True if state is ready, False otherwise
        """
        requirements = {
            "DiffAgent": lambda: True,  # No prerequisites
            "SummaryAgent": lambda: self.bullet_points is not None and len(self.bullet_points) > 0,
            "CommitWriterAgent": lambda: self.summary is not None and len(self.summary.strip()) > 0
        }
        
        checker = requirements.get(agent_name)
        if checker is None:
            return False
        
        return checker()
    
    def get_stage_output(self, stage: str) -> Optional[Any]:
        """
        Get output from a specific pipeline stage.
        
        Args:
            stage: Stage name (diff, bullet_points, summary, commit)
            
        Returns:
            Output from the specified stage or None
        """
        stage_mapping = {
            "diff": self.staged_diff,
            "bullet_points": self.bullet_points,
            "summary": self.summary,
            "commit": self.commit_message
        }
        return stage_mapping.get(stage)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert state to dictionary for serialization."""
        return {
            "staged_diff": self.staged_diff,
            "bullet_points": self.bullet_points,
            "summary": self.summary,
            "commit_message": self.commit_message,
            "errors": self.errors,
            "metadata": self.metadata
        }
    
    def to_json(self, indent: int = 2) -> str:
        """Convert state to JSON string."""
        return json.dumps(self.to_dict(), indent=indent)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "PipelineState":
        """Create PipelineState from dictionary."""
        return cls(
            staged_diff=data.get("staged_diff"),
            bullet_points=data.get("bullet_points"),
            summary=data.get("summary"),
            commit_message=data.get("commit_message"),
            errors=data.get("errors", []),
            metadata=data.get("metadata", {})
        )
    
    def __repr__(self) -> str:
        """String representation for debugging."""
        return (
            f"PipelineState(\n"
            f"  staged_diff={'✓' if self.staged_diff else '✗'},\n"
            f"  bullet_points={len(self.bullet_points) if self.bullet_points else 0} items,\n"
            f"  summary={'✓' if self.summary else '✗'},\n"
            f"  commit_message={'✓' if self.commit_message else '✗'},\n"
            f"  errors={len(self.errors)}\n"
            f")"
        )


class StateValidator:
    """Validates pipeline state at different stages."""
    
    @staticmethod
    def validate_diff(state: PipelineState) -> bool:
        """Validate that diff is present and non-empty."""
        if not state.staged_diff:
            state.add_error("No staged diff found", "StateValidator")
            return False
        
        if len(state.staged_diff.strip()) == 0:
            state.add_error("Staged diff is empty", "StateValidator")
            return False
        
        return True
    
    @staticmethod
    def validate_bullet_points(state: PipelineState) -> bool:
        """Validate that bullet points are present and well-formed."""
        if not state.bullet_points:
            state.add_error("No bullet points generated", "StateValidator")
            return False
        
        if len(state.bullet_points) == 0:
            state.add_error("Bullet points list is empty", "StateValidator")
            return False
        
        # Check for empty strings
        empty_bullets = [i for i, bp in enumerate(state.bullet_points) if not bp.strip()]
        if empty_bullets:
            state.add_error(f"Found empty bullet points at indices: {empty_bullets}", "StateValidator")
            return False
        
        return True
    
    @staticmethod
    def validate_summary(state: PipelineState) -> bool:
        """Validate that summary is present and meaningful."""
        if not state.summary:
            state.add_error("No summary generated", "StateValidator")
            return False
        
        if len(state.summary.strip()) < 10:
            state.add_error("Summary is too short (< 10 characters)", "StateValidator")
            return False
        
        return True
    
    @staticmethod
    def validate_commit_message(state: PipelineState) -> bool:
        """Validate that commit message is well-formed."""
        if not state.commit_message:
            state.add_error("No commit message generated", "StateValidator")
            return False
        
        msg = state.commit_message.strip()
        
        if len(msg) < 10:
            state.add_error("Commit message is too short", "StateValidator")
            return False
        
        # Check for conventional commit format (optional but recommended)
        lines = msg.split('\n')
        first_line = lines[0].strip()
        
        if len(first_line) > 100:
            state.add_error("First line of commit message is too long (> 100 chars)", "StateValidator")
            # Not a hard failure, just a warning
        
        return True
