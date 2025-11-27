"""
Commit Message Generation Pipeline

Main orchestrator that runs three specialized agents in sequence to generate
professional conventional commit messages from staged Git changes.

The pipeline uses Ollama + OpenChat 7B by default for LLM-powered summarization
and commit message generation.

Execution Flow:
    1. DiffAgent - Parse git diff --staged into structured bullet points
    2. SummaryAgent - Use LLM to create concise summary from bullet points
    3. CommitWriterAgent - Use LLM to format summary into conventional commit
    
State Management:
    All agents share a PipelineState object that flows through the pipeline,
    accumulating outputs from each stage.

Error Handling:
    Each agent has fallback logic if LLM calls fail, ensuring the pipeline
    always produces a commit message (even if not LLM-enhanced).
"""

import logging
from typing import Optional
from pathlib import Path

from src.state import PipelineState, StateValidator
from src.llm_client import LLMClient, LLMConfig
from src.agents import DiffAgent, SummaryAgent, CommitWriterAgent
from src.config import Config


logger = logging.getLogger(__name__)


class CommitPipeline:
    """
    Main pipeline orchestrator for AI-powered commit message generation.
    
    This class coordinates three specialized agents that work together to
    transform raw git diffs into professional conventional commit messages.
    
    Pipeline Stages:
        1. DiffAgent - Parses `git diff --staged` into human-readable changes
        2. SummaryAgent - Uses Ollama LLM to create a concise summary
        3. CommitWriterAgent - Uses Ollama LLM to format as conventional commit
    
    The pipeline maintains a shared PipelineState object that accumulates
    outputs from each agent, allowing for full traceability and debugging.
    
    Example:
        >>> pipeline = CommitPipeline(debug=True)
        >>> result = pipeline.run()
        >>> print(result.commit_message)
        "feat(api): add user authentication endpoints"
    """
    
    def __init__(
        self,
        repo_path: Optional[str] = None,
        llm_client: Optional[LLMClient] = None,
        debug: bool = False
    ):
        """
        Initialize the commit pipeline.
        
        Args:
            repo_path: Path to git repository (defaults to current directory)
            llm_client: Optional LLM client (creates one if not provided)
            debug: Enable debug output
        """
        self.repo_path = repo_path or Config.GIT_REPO_PATH
        self.debug = debug or Config.DEBUG_MODE
        
        # Initialize LLM client
        if llm_client is None:
            llm_config = LLMConfig.from_env()
            self.llm_client = LLMClient(llm_config)
        else:
            self.llm_client = llm_client
        
        # Initialize agents
        self.diff_agent = DiffAgent(
            repo_path=self.repo_path,
            use_llm=Config.USE_LLM_FOR_DIFF,
            llm_client=self.llm_client if Config.USE_LLM_FOR_DIFF else None
        )
        
        self.summary_agent = SummaryAgent(
            llm_client=self.llm_client,
            max_summary_length=500
        )
        
        self.commit_writer_agent = CommitWriterAgent(
            llm_client=self.llm_client,
            commit_style=Config.COMMIT_STYLE
        )
        
        logger.info(f"Pipeline initialized for repository: {self.repo_path}")
    
    def run(self, state: Optional[PipelineState] = None) -> PipelineState:
        """
        Run the complete pipeline.
        
        Args:
            state: Optional initial state (creates new one if not provided)
            
        Returns:
            Final pipeline state with commit message
        """
        # Initialize state
        if state is None:
            state = PipelineState()
        
        try:
            # Step 1: DiffAgent - Parse Git changes
            print(f"\n{'='*70}")
            print(f"  STEP 1: Analyzing Git Changes")
            print(f"{'='*70}")
            state = self._run_agent(self.diff_agent, state, "DIFF ANALYSIS")
            
            if state.bullet_points:
                print(f"\nChanges detected ({len(state.bullet_points)} items):")
                for i, bullet in enumerate(state.bullet_points[:10], 1):  # Show first 10
                    print(f"  {i}. {bullet}")
                if len(state.bullet_points) > 10:
                    print(f"  ... and {len(state.bullet_points) - 10} more")
            
            if state.has_errors():
                return state
            
            # Step 2: SummaryAgent - Create summary
            print(f"\n{'='*70}")
            print(f"  STEP 2: Filtering & Summarizing with AI")
            print(f"{'='*70}")
            state = self._run_agent(self.summary_agent, state, "SUMMARY GENERATION")
            
            if state.summary:
                print(f"\nGenerated Summary:")
                print(f"  {state.summary}")
            
            if state.has_errors():
                return state
            
            # Step 3: CommitWriterAgent - Format commit message
            print(f"\n{'='*70}")
            print(f"  STEP 3: Creating Commit Message")
            print(f"{'='*70}")
            state = self._run_agent(self.commit_writer_agent, state, "COMMIT MESSAGE GENERATION")
            
            if state.commit_message:
                print(f"\nCommit Message Generated:")
                print(f"  {state.commit_message}")
            
        except Exception as e:
            logger.error(f"Pipeline failed: {e}")
            state.add_error(str(e), "Pipeline")
        
        return state
    
    def _run_agent(self, agent, state: PipelineState, stage_name: str) -> PipelineState:
        """
        Run a single agent and handle errors.
        
        Args:
            agent: Agent to run
            state: Current state
            stage_name: Name of the stage for logging
            
        Returns:
            Updated state
        """
        logger.info(f"\n{'*'*60}")
        logger.info(f"STAGE: {stage_name}")
        logger.info(f"{'*'*60}\n")
        
        try:
            state = agent.process(state)
        except Exception as e:
            logger.error(f"Agent {agent.name} failed: {e}")
            state.add_error(str(e), agent.name)
        
        return state
    
    def _print_debug(self, title: str, items: list):
        """
        Print debug information.
        
        Args:
            title: Section title
            items: Items to print
        """
        print(f"\n{'─'*60}")
        print(f"DEBUG: {title}")
        print(f"{'─'*60}")
        for item in items:
            print(f"  {item}")
        print(f"{'─'*60}\n")
    
    def get_commit_message(self) -> Optional[str]:
        """
        Run pipeline and return only the commit message.
        
        Returns:
            Commit message string or None if failed
        """
        state = self.run()
        return state.commit_message if not state.has_errors() else None
    
    def validate_repository(self) -> bool:
        """
        Validate that the repository has staged changes.
        
        Returns:
            True if repository is valid and has staged changes
        """
        try:
            return self.diff_agent.validate_input(PipelineState())
        except Exception as e:
            logger.error(f"Repository validation failed: {e}")
            return False


def create_pipeline(
    repo_path: Optional[str] = None,
    debug: bool = False
) -> CommitPipeline:
    """
    Convenience function to create a pipeline.
    
    Args:
        repo_path: Path to repository
        debug: Enable debug mode
        
    Returns:
        Configured pipeline
    """
    return CommitPipeline(repo_path=repo_path, debug=debug)
