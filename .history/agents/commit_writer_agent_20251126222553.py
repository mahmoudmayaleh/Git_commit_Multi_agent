"""
CommitWriterAgent

This agent transforms the summary into a properly formatted conventional
commit message following best practices.
"""

import logging
from typing import Optional
from agents.base_agent import BaseAgent
from state import PipelineState
from llm_client import LLMClient


logger = logging.getLogger(__name__)


class CommitWriterAgent(BaseAgent):
    """
    Agent that crafts conventional commit messages from summaries.
    
    This agent:
    1. Receives a summary from SummaryAgent
    2. Determines the appropriate commit type (feat, fix, refactor, etc.)
    3. Generates a properly formatted conventional commit message
    4. Ensures compliance with best practices
    """
    
    COMMIT_TYPES = {
        "feat": "A new feature",
        "fix": "A bug fix",
        "docs": "Documentation only changes",
        "style": "Changes that do not affect the meaning of the code",
        "refactor": "A code change that neither fixes a bug nor adds a feature",
        "perf": "A code change that improves performance",
        "test": "Adding missing tests or correcting existing tests",
        "build": "Changes that affect the build system or external dependencies",
        "ci": "Changes to CI configuration files and scripts",
        "chore": "Other changes that don't modify src or test files",
        "revert": "Reverts a previous commit"
    }
    
    def __init__(self, llm_client: LLMClient, commit_style: str = "conventional"):
        """
        Initialize CommitWriterAgent.
        
        Args:
            llm_client: LLM client for generating commit messages
            commit_style: Style of commit message (conventional, angular, gitmoji)
        """
        super().__init__("CommitWriterAgent")
        self.llm_client = llm_client
        self.commit_style = commit_style
    
    def process(self, state: PipelineState) -> PipelineState:
        """
        Process the pipeline state by generating a commit message.
        
        Args:
            state: Current pipeline state
            
        Returns:
            Updated state with commit_message
        """
        self.log_start()
        
        try:
            # Validate input
            if not self.validate_input(state):
                state.add_error("No summary to convert to commit message", self.name)
                logger.warning("No summary found in state")
                return state
            
            logger.info(f"Generating commit message from summary: '{state.summary[:100]}...'")
            
            # Generate commit message using LLM
            state.commit_message = self._generate_commit_message(
                state.summary,
                state.bullet_points
            )
            
            logger.info(f"Generated commit message:\n{state.commit_message}")
            
            # Store metadata
            state.metadata["commit_message_length"] = len(state.commit_message)
            state.metadata["commit_style"] = self.commit_style
            
            self.log_end()
            
        except Exception as e:
            self.log_error(e)
            state.add_error(str(e), self.name)
        
        return state
    
    def _generate_commit_message(self, summary: str, bullet_points: Optional[list] = None) -> str:
        """
        Generate a conventional commit message using LLM.
        
        Args:
            summary: Summary of changes
            bullet_points: Original bullet points (optional context)
            
        Returns:
            Formatted commit message
        """
        # Prepare context
        context = f"Summary: {summary}"
        if bullet_points and len(bullet_points) > 0:
            context += f"\n\nDetailed Changes:\n" + '\n'.join(bullet_points[:10])
        
        # Create prompt based on style
        prompt = self._create_prompt(context)
        
        try:
            commit_msg = self.llm_client.generate(
                prompt,
                max_new_tokens=300,
                temperature=0.4
            )
            
            # Clean up the message
            commit_msg = self._clean_commit_message(commit_msg)
            
            # Validate format
            if not self._validate_commit_format(commit_msg):
                logger.warning("Generated commit message doesn't follow format, attempting to fix")
                commit_msg = self._fix_commit_format(commit_msg, summary)
            
            return commit_msg
            
        except Exception as e:
            logger.error(f"LLM commit generation failed: {e}, using fallback")
            return self._generate_fallback_commit(summary)
    
    def _create_prompt(self, context: str) -> str:
        """
        Create prompt for LLM based on commit style.
        
        Args:
            context: Summary and bullet points
            
        Returns:
            Formatted prompt
        """
        if self.commit_style == "conventional":
            return f"""You are a Git expert writing a conventional commit message.

Based on the following context, write a commit message that follows the Conventional Commits specification:

Format:
<type>[optional scope]: <description>

[optional body]

[optional footer(s)]

Rules:
1. Type must be one of: feat, fix, docs, style, refactor, perf, test, build, ci, chore, revert
2. Description should be lowercase and not end with a period
3. Subject line should be no more than 72 characters
4. Body (if present) should explain what and why, not how
5. Use imperative mood ("add feature" not "added feature")

Context:
{context}

Generate the commit message (just the commit message, no extra text):"""

        elif self.commit_style == "angular":
            return f"""Write an Angular-style commit message.

Format:
<type>(<scope>): <subject>
<BLANK LINE>
<body>
<BLANK LINE>
<footer>

Types: feat, fix, docs, style, refactor, perf, test, build, ci, chore, revert

Context:
{context}

Commit message:"""

        else:  # Default to conventional
            return self._create_prompt(context)
    
    def _clean_commit_message(self, message: str) -> str:
        """
        Clean up the generated commit message.
        
        Args:
            message: Raw generated message
            
        Returns:
            Cleaned message
        """
        # Remove any markdown formatting
        message = message.replace('```', '').strip()
        
        # Remove "Commit message:" prefix if present
        if message.lower().startswith('commit message:'):
            message = message[15:].strip()
        
        # Remove leading/trailing quotes
        message = message.strip('"\'')
        
        # Ensure proper line breaks
        lines = [line.rstrip() for line in message.split('\n')]
        message = '\n'.join(lines)
        
        return message.strip()
    
    def _validate_commit_format(self, message: str) -> bool:
        """
        Validate that commit message follows conventional format.
        
        Args:
            message: Commit message to validate
            
        Returns:
            True if valid
        """
        import re
        
        lines = message.split('\n')
        if len(lines) == 0:
            return False
        
        first_line = lines[0].strip()
        
        # Check conventional commit format: type(scope): description
        # or: type: description
        pattern = r'^(feat|fix|docs|style|refactor|perf|test|build|ci|chore|revert)(\([a-z\-]+\))?: .+'
        
        return bool(re.match(pattern, first_line))
    
    def _fix_commit_format(self, message: str, summary: str) -> str:
        """
        Attempt to fix malformed commit message.
        
        Args:
            message: Malformed message
            summary: Original summary
            
        Returns:
            Fixed message
        """
        # Determine type from summary
        commit_type = self._infer_commit_type(summary)
        
        # Extract meaningful description
        lines = message.split('\n')
        description = lines[0].strip()
        
        # Remove type prefix if already present
        for type_name in self.COMMIT_TYPES.keys():
            if description.lower().startswith(type_name):
                description = description[len(type_name):].strip(':() ')
                break
        
        # Ensure lowercase first letter and no trailing period
        if description:
            description = description[0].lower() + description[1:]
            description = description.rstrip('.')
        else:
            description = summary[:50].lower()
        
        # Reconstruct first line
        first_line = f"{commit_type}: {description}"
        
        # Keep body if present
        body = '\n'.join(lines[1:]).strip() if len(lines) > 1 else ""
        
        if body:
            return f"{first_line}\n\n{body}"
        else:
            return first_line
    
    def _infer_commit_type(self, summary: str) -> str:
        """
        Infer commit type from summary.
        
        Args:
            summary: Summary text
            
        Returns:
            Commit type
        """
        summary_lower = summary.lower()
        
        # Keyword mapping
        type_keywords = {
            "feat": ["add", "new", "implement", "create", "feature"],
            "fix": ["fix", "bug", "issue", "error", "resolve"],
            "docs": ["document", "readme", "comment", "docs"],
            "style": ["format", "style", "whitespace"],
            "refactor": ["refactor", "restructure", "reorganize", "rename"],
            "perf": ["performance", "optimize", "faster", "speed"],
            "test": ["test", "spec", "coverage"],
            "build": ["build", "dependency", "package", "npm", "pip"],
            "ci": ["ci", "pipeline", "github actions", "travis"],
            "chore": ["chore", "update", "maintain"]
        }
        
        # Count matches for each type
        type_scores = {}
        for commit_type, keywords in type_keywords.items():
            score = sum(1 for kw in keywords if kw in summary_lower)
            if score > 0:
                type_scores[commit_type] = score
        
        # Return type with highest score, default to chore
        if type_scores:
            return max(type_scores, key=type_scores.get)
        else:
            return "chore"
    
    def _generate_fallback_commit(self, summary: str) -> str:
        """
        Generate a simple commit message as fallback.
        
        Args:
            summary: Summary text
            
        Returns:
            Basic commit message
        """
        commit_type = self._infer_commit_type(summary)
        
        # Create simple message
        description = summary[:72].lower()
        if '.' in description:
            description = description.split('.')[0]
        
        description = description.strip().rstrip('.')
        
        return f"{commit_type}: {description}"
    
    def validate_input(self, state: PipelineState) -> bool:
        """
        Validate that state has a summary.
        
        Args:
            state: Pipeline state
            
        Returns:
            True if valid
        """
        return (
            state.summary is not None and 
            len(state.summary.strip()) > 0
        )
