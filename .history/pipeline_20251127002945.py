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

from state import PipelineState, StateValidator
from llm_client import LLMClient, LLMConfig
from agents import DiffAgent, SummaryAgent, CommitWriterAgent
from config import Config


logger = logging.getLogger(__name__)


class CommitPipeline:
    """
    Main pipeline that orchestrates all agents to generate commit messages.
    
    The pipeline executes agents in the following order:
    1. DiffAgent - Extract and parse staged git changes
    2. SummaryAgent - Summarize changes into concise context
    3. CommitWriterAgent - Generate conventional commit message
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
        
        logger.info("\n" + "="*60)
        logger.info("STARTING COMMIT MESSAGE PIPELINE")
        logger.info("="*60 + "\n")
        
        try:
            # Step 1: DiffAgent
            state = self._run_agent(self.diff_agent, state, "DIFF ANALYSIS")
            if self.debug and state.bullet_points:
                self._print_debug("Bullet Points", state.bullet_points)
            
            # Check for errors
            if state.has_errors():
                logger.error("Pipeline stopped due to errors in DiffAgent")
                return state
            
            # Step 2: SummaryAgent
            state = self._run_agent(self.summary_agent, state, "SUMMARY GENERATION")
            if self.debug and state.summary:
                self._print_debug("Summary", [state.summary])
            
            # Check for errors
            if state.has_errors():
                logger.error("Pipeline stopped due to errors in SummaryAgent")
                return state
            
            # Step 3: CommitWriterAgent
            state = self._run_agent(self.commit_writer_agent, state, "COMMIT MESSAGE GENERATION")
            if self.debug and state.commit_message:
                self._print_debug("Commit Message", [state.commit_message])
            
            # Final validation
            if not state.has_errors() and state.commit_message:
                logger.info("\n" + "="*60)
                logger.info("PIPELINE COMPLETED SUCCESSFULLY")
                logger.info("="*60 + "\n")
            else:
                logger.warning("\n" + "="*60)
                logger.warning("PIPELINE COMPLETED WITH ERRORS")
                logger.warning("="*60 + "\n")
            
        except Exception as e:
            logger.error(f"Pipeline failed with unexpected error: {e}")
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
