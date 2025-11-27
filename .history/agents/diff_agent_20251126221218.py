"""
DiffAgent (CoderAgent)

This agent executes 'git diff --staged' and parses the raw diff output
into structured, human-readable bullet points describing the changes.
"""

import re
import logging
from typing import List, Optional, Tuple
from git import Repo, GitCommandError
from agents.base_agent import BaseAgent
from state import PipelineState
from llm_client import LLMClient


logger = logging.getLogger(__name__)


class DiffAgent(BaseAgent):
    """
    Agent that parses Git diffs and extracts structured change information.
    
    This agent:
    1. Executes 'git diff --staged' to get staged changes
    2. Parses the diff to extract file-level and line-level changes
    3. Optionally uses LLM to enhance change descriptions
    4. Produces human-readable bullet points
    """
    
    def __init__(self, repo_path: str = ".", use_llm: bool = False, llm_client: Optional[LLMClient] = None):
        """
        Initialize DiffAgent.
        
        Args:
            repo_path: Path to Git repository
            use_llm: Whether to use LLM for enhanced descriptions
            llm_client: Optional LLM client for enhanced parsing
        """
        super().__init__("DiffAgent")
        self.repo_path = repo_path
        self.use_llm = use_llm
        self.llm_client = llm_client
        
        try:
            self.repo = Repo(repo_path)
        except Exception as e:
            logger.error(f"Failed to initialize Git repository at {repo_path}: {e}")
            raise
    
    def process(self, state: PipelineState) -> PipelineState:
        """
        Process the pipeline state by extracting and parsing Git diff.
        
        Args:
            state: Current pipeline state
            
        Returns:
            Updated state with staged_diff and bullet_points
        """
        self.log_start()
        
        try:
            # Get staged diff
            state.staged_diff = self._get_staged_diff()
            
            if not state.staged_diff or len(state.staged_diff.strip()) == 0:
                state.add_error("No staged changes found", self.name)
                logger.warning("No staged changes detected")
                return state
            
            logger.info(f"Retrieved diff: {len(state.staged_diff)} characters")
            
            # Parse diff into bullet points
            if self.use_llm and self.llm_client:
                state.bullet_points = self._parse_diff_with_llm(state.staged_diff)
            else:
                state.bullet_points = self._parse_diff_rule_based(state.staged_diff)
            
            logger.info(f"Generated {len(state.bullet_points)} bullet points")
            
            # Store metadata
            state.metadata["diff_length"] = len(state.staged_diff)
            state.metadata["bullet_count"] = len(state.bullet_points)
            
            self.log_end()
            
        except Exception as e:
            self.log_error(e)
            state.add_error(str(e), self.name)
        
        return state
    
    def _get_staged_diff(self) -> str:
        """
        Execute 'git diff --staged' and return the output.
        
        Returns:
            Raw diff output as string
        """
        try:
            # Get staged diff using GitPython
            diff = self.repo.git.diff('--staged')
            return diff
        except GitCommandError as e:
            logger.error(f"Git command failed: {e}")
            raise
    
    def _parse_diff_rule_based(self, diff: str) -> List[str]:
        """
        Parse diff using rule-based approach (no LLM).
        
        Args:
            diff: Raw diff string
            
        Returns:
            List of bullet points describing changes
        """
        bullet_points = []
        
        # Split diff by file
        file_diffs = self._split_diff_by_file(diff)
        
        for file_info in file_diffs:
            file_path = file_info["path"]
            change_type = file_info["type"]
            stats = file_info["stats"]
            
            # Create bullet point based on change type
            if change_type == "new":
                bullet_points.append(f"• Added new file `{file_path}` (+{stats['additions']} lines)")
            elif change_type == "deleted":
                bullet_points.append(f"• Deleted file `{file_path}` (-{stats['deletions']} lines)")
            elif change_type == "renamed":
                old_path = file_info.get("old_path", "unknown")
                bullet_points.append(f"• Renamed `{old_path}` to `{file_path}`")
            elif change_type == "modified":
                # Parse function/class changes if possible
                detailed_changes = self._extract_detailed_changes(file_info["content"])
                
                if detailed_changes:
                    for change in detailed_changes:
                        bullet_points.append(f"• {change} in `{file_path}`")
                else:
                    bullet_points.append(
                        f"• Modified `{file_path}` "
                        f"(+{stats['additions']} -{stats['deletions']} lines)"
                    )
        
        return bullet_points
    
    def _parse_diff_with_llm(self, diff: str) -> List[str]:
        """
        Parse diff using LLM for enhanced understanding.
        
        Args:
            diff: Raw diff string
            
        Returns:
            List of bullet points describing changes
        """
        prompt = f"""You are analyzing a Git diff to extract key changes.
Parse the following diff and create concise bullet points describing each significant change.
Focus on:
- New files, deleted files, renamed files
- New functions, classes, or methods added
- Modified functions or methods
- Configuration changes
- Dependency updates

Format each bullet point starting with "•" and keep them concise (one line each).

Git Diff:
```
{diff[:4000]}  
```

Bullet Points:"""

        try:
            response = self.llm_client.generate(prompt, max_new_tokens=512, temperature=0.3)
            
            # Extract bullet points from response
            lines = response.strip().split('\n')
            bullet_points = []
            
            for line in lines:
                line = line.strip()
                if line and (line.startswith('•') or line.startswith('-') or line.startswith('*')):
                    # Normalize bullet point format
                    if not line.startswith('•'):
                        line = '• ' + line.lstrip('-*').strip()
                    bullet_points.append(line)
            
            # Fallback to rule-based if LLM produces poor results
            if len(bullet_points) == 0:
                logger.warning("LLM produced no bullet points, falling back to rule-based parsing")
                return self._parse_diff_rule_based(diff)
            
            return bullet_points
            
        except Exception as e:
            logger.error(f"LLM parsing failed: {e}, falling back to rule-based")
            return self._parse_diff_rule_based(diff)
    
    def _split_diff_by_file(self, diff: str) -> List[dict]:
        """
        Split diff output by file and extract metadata.
        
        Args:
            diff: Raw diff string
            
        Returns:
            List of dictionaries containing file information
        """
        files = []
        current_file = None
        
        lines = diff.split('\n')
        
        for i, line in enumerate(lines):
            # Detect new file diff
            if line.startswith('diff --git'):
                if current_file:
                    files.append(current_file)
                
                # Extract file paths
                match = re.search(r'diff --git a/(.*?) b/(.*?)$', line)
                if match:
                    current_file = {
                        "old_path": match.group(1),
                        "path": match.group(2),
                        "type": "modified",
                        "stats": {"additions": 0, "deletions": 0},
                        "content": []
                    }
            
            elif current_file:
                # Detect file type
                if line.startswith('new file'):
                    current_file["type"] = "new"
                elif line.startswith('deleted file'):
                    current_file["type"] = "deleted"
                elif line.startswith('rename from'):
                    current_file["type"] = "renamed"
                
                # Count additions/deletions
                elif line.startswith('+') and not line.startswith('+++'):
                    current_file["stats"]["additions"] += 1
                    current_file["content"].append(("add", line[1:]))
                elif line.startswith('-') and not line.startswith('---'):
                    current_file["stats"]["deletions"] += 1
                    current_file["content"].append(("del", line[1:]))
                else:
                    current_file["content"].append(("ctx", line))
        
        # Add last file
        if current_file:
            files.append(current_file)
        
        return files
    
    def _extract_detailed_changes(self, content: List[Tuple[str, str]]) -> List[str]:
        """
        Extract detailed changes like function additions/modifications.
        
        Args:
            content: List of (change_type, line) tuples
            
        Returns:
            List of detailed change descriptions
        """
        changes = []
        
        # Look for function/method definitions
        function_patterns = [
            r'def\s+(\w+)\s*\(',  # Python
            r'function\s+(\w+)\s*\(',  # JavaScript
            r'(public|private|protected)?\s*\w+\s+(\w+)\s*\(',  # Java/C#/C++
            r'const\s+(\w+)\s*=\s*\(',  # Arrow functions
        ]
        
        for change_type, line in content:
            if change_type == "add":
                for pattern in function_patterns:
                    match = re.search(pattern, line)
                    if match:
                        func_name = match.group(1) if match.lastindex == 1 else match.group(2)
                        changes.append(f"Added function `{func_name}()`")
                        break
                
                # Check for class definitions
                class_match = re.search(r'class\s+(\w+)', line)
                if class_match:
                    changes.append(f"Added class `{class_match.group(1)}`")
        
        return changes
    
    def validate_input(self, state: PipelineState) -> bool:
        """
        Validate that the repository has staged changes.
        
        Args:
            state: Pipeline state
            
        Returns:
            True if valid
        """
        try:
            diff = self.repo.git.diff('--staged')
            return len(diff.strip()) > 0
        except:
            return False
