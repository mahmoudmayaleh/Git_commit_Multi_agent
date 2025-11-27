"""
Test Suite for Commit Pipeline

Run with: pytest tests/ -v
"""

import pytest
from state import PipelineState, StateValidator


class TestPipelineState:
    """Tests for PipelineState class."""
    
    def test_state_initialization(self):
        """Test basic state initialization."""
        state = PipelineState()
        
        assert state.staged_diff is None
        assert state.bullet_points is None
        assert state.summary is None
        assert state.commit_message is None
        assert len(state.errors) == 0
        assert "created_at" in state.metadata
    
    def test_add_error(self):
        """Test error addition."""
        state = PipelineState()
        
        state.add_error("Test error", "TestAgent")
        
        assert len(state.errors) == 1
        assert "TestAgent" in state.errors[0]
        assert "Test error" in state.errors[0]
        assert state.has_errors()
    
    def test_is_ready_for_agent(self):
        """Test agent readiness checks."""
        state = PipelineState()
        
        # DiffAgent should always be ready
        assert state.is_ready_for_agent("DiffAgent")
        
        # SummaryAgent needs bullet points
        assert not state.is_ready_for_agent("SummaryAgent")
        state.bullet_points = ["• Test change"]
        assert state.is_ready_for_agent("SummaryAgent")
        
        # CommitWriterAgent needs summary
        assert not state.is_ready_for_agent("CommitWriterAgent")
        state.summary = "Test summary"
        assert state.is_ready_for_agent("CommitWriterAgent")
    
    def test_to_dict_and_from_dict(self):
        """Test serialization."""
        state = PipelineState(
            staged_diff="test diff",
            bullet_points=["• Test"],
            summary="Test summary"
        )
        
        # Convert to dict
        state_dict = state.to_dict()
        
        # Recreate from dict
        new_state = PipelineState.from_dict(state_dict)
        
        assert new_state.staged_diff == state.staged_diff
        assert new_state.bullet_points == state.bullet_points
        assert new_state.summary == state.summary


class TestStateValidator:
    """Tests for StateValidator class."""
    
    def test_validate_diff(self):
        """Test diff validation."""
        state = PipelineState()
        
        # Should fail with no diff
        assert not StateValidator.validate_diff(state)
        assert state.has_errors()
        
        # Should fail with empty diff
        state = PipelineState(staged_diff="   ")
        assert not StateValidator.validate_diff(state)
        
        # Should succeed with valid diff
        state = PipelineState(staged_diff="diff --git a/file.py b/file.py")
        assert StateValidator.validate_diff(state)
    
    def test_validate_bullet_points(self):
        """Test bullet points validation."""
        state = PipelineState()
        
        # Should fail with no bullets
        assert not StateValidator.validate_bullet_points(state)
        
        # Should fail with empty list
        state.bullet_points = []
        assert not StateValidator.validate_bullet_points(state)
        
        # Should succeed with valid bullets
        state.bullet_points = ["• Valid bullet"]
        assert StateValidator.validate_bullet_points(state)
    
    def test_validate_summary(self):
        """Test summary validation."""
        state = PipelineState()
        
        # Should fail with no summary
        assert not StateValidator.validate_summary(state)
        
        # Should fail with short summary
        state.summary = "Short"
        assert not StateValidator.validate_summary(state)
        
        # Should succeed with valid summary
        state.summary = "This is a valid summary with enough content."
        assert StateValidator.validate_summary(state)
    
    def test_validate_commit_message(self):
        """Test commit message validation."""
        state = PipelineState()
        
        # Should fail with no message
        assert not StateValidator.validate_commit_message(state)
        
        # Should fail with short message
        state.commit_message = "Short"
        assert not StateValidator.validate_commit_message(state)
        
        # Should succeed with valid message
        state.commit_message = "feat: add new feature with proper description"
        assert StateValidator.validate_commit_message(state)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
