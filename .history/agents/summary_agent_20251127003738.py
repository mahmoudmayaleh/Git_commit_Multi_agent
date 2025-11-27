"""
SummaryAgent

This agent takes the bullet points from DiffAgent and produces a concise,
context-aware summary by filtering, grouping, and condensing the information.
"""

import logging
from typing import List, Optional
from agents.base_agent import BaseAgent
from state import PipelineState
from llm_client import LLMClient


logger = logging.getLogger(__name__)


class SummaryAgent(BaseAgent):
    """
    Agent that summarizes and filters bullet points into a concise summary.
    
    This agent:
    1. Receives bullet points from DiffAgent
    2. Groups related changes together
    3. Filters out noise and unimportant details
    4. Generates a clear, context-aware summary
    5. Uses LLM to create natural language summary
    """
    
    def __init__(self, llm_client: LLMClient, max_summary_length: int = 500):
        """
        Initialize SummaryAgent.
        
        Args:
            llm_client: LLM client for generating summaries
            max_summary_length: Maximum length of summary in characters
        """
        super().__init__("SummaryAgent")
        self.llm_client = llm_client
        self.max_summary_length = max_summary_length
    
    def process(self, state: PipelineState) -> PipelineState:
        """
        Process the pipeline state by summarizing bullet points.
        
        Args:
            state: Current pipeline state
            
        Returns:
            Updated state with summary
        """
        self.log_start()
        
        try:
            # Validate input
            if not self.validate_input(state):
                state.add_error("No bullet points to summarize", self.name)
                logger.warning("No bullet points found in state")
                return state
            
            logger.info(f"Summarizing {len(state.bullet_points)} bullet points")
            
            # Filter and group bullet points
            filtered_bullets = self._filter_bullet_points(state.bullet_points)
            grouped_bullets = self._group_bullet_points(filtered_bullets)
            
            logger.info(f"Filtered to {len(filtered_bullets)} relevant changes")
            
            # Generate summary using LLM
            state.summary = self._generate_summary(grouped_bullets)
            
            logger.info(f"Generated summary: {len(state.summary)} characters")
            
            # Store metadata
            state.metadata["original_bullet_count"] = len(state.bullet_points)
            state.metadata["filtered_bullet_count"] = len(filtered_bullets)
            state.metadata["summary_length"] = len(state.summary)
            
            self.log_end()
            
        except Exception as e:
            self.log_error(e)
            state.add_error(str(e), self.name)
        
        return state
    
    def _filter_bullet_points(self, bullets: List[str]) -> List[str]:
        """
        Filter out noise and unimportant bullet points.
        
        Also limits to max 50 bullets to avoid overwhelming the LLM.
        
        Args:
            bullets: List of bullet points
            
        Returns:
            Filtered list of bullet points (max 50)
        """
        import re
        
        filtered = []
        
        # Patterns to filter out
        noise_patterns = [
            r'whitespace',
            r'formatting',
            r'typo',
            r'comment.*updated',
            r'indentation',
            r'\.history/',  # Filter out history files
        ]
        
        for bullet in bullets:
            bullet_lower = bullet.lower()
            
            # Skip if matches noise pattern
            is_noise = any(
                re.search(pattern, bullet_lower) 
                for pattern in noise_patterns
            )
            
            if not is_noise and len(bullet.strip()) > 5:
                filtered.append(bullet)
        
        # Limit to 50 most important bullets to avoid overwhelming LLM
        if len(filtered) > 50:
            logger.info(f"Limiting {len(filtered)} bullets to top 50 to avoid LLM overload")
            # Prioritize: main files over tests, actual code over config
            priority_filtered = []
            non_priority = []
            
            for bullet in filtered:
                bullet_lower = bullet.lower()
                # Deprioritize test files, configs, and documentation
                if any(x in bullet_lower for x in ['test', '.md', '.txt', '.json', '.yml', 'config']):
                    non_priority.append(bullet)
                else:
                    priority_filtered.append(bullet)
            
            # Take top priority items + fill with non-priority up to 50
            filtered = priority_filtered[:40] + non_priority[:10]
        
        return filtered
    
    def _group_bullet_points(self, bullets: List[str]) -> dict:
        """
        Group bullet points by category.
        
        Args:
            bullets: List of bullet points
            
        Returns:
            Dictionary of grouped bullet points
        """
        groups = {
            "features": [],
            "fixes": [],
            "refactoring": [],
            "dependencies": [],
            "configuration": [],
            "documentation": [],
            "tests": [],
            "other": []
        }
        
        for bullet in bullets:
            bullet_lower = bullet.lower()
            
            # Categorize based on keywords
            if any(kw in bullet_lower for kw in ["add", "new", "implement", "create"]):
                groups["features"].append(bullet)
            elif any(kw in bullet_lower for kw in ["fix", "bug", "issue", "error"]):
                groups["fixes"].append(bullet)
            elif any(kw in bullet_lower for kw in ["refactor", "restructure", "reorganize", "rename"]):
                groups["refactoring"].append(bullet)
            elif any(kw in bullet_lower for kw in ["dependency", "package", "requirement", "version"]):
                groups["dependencies"].append(bullet)
            elif any(kw in bullet_lower for kw in ["config", "setting", ".env", "yml", "json"]):
                groups["configuration"].append(bullet)
            elif any(kw in bullet_lower for kw in ["doc", "readme", "comment"]):
                groups["documentation"].append(bullet)
            elif any(kw in bullet_lower for kw in ["test", "spec", "mock"]):
                groups["tests"].append(bullet)
            else:
                groups["other"].append(bullet)
        
        # Remove empty groups
        return {k: v for k, v in groups.items() if v}
    
    def _generate_summary(self, grouped_bullets: dict) -> str:
        """
        Generate natural language summary using LLM.
        
        Args:
            grouped_bullets: Dictionary of grouped bullet points
            
        Returns:
            Concise summary string
        """
        # Prepare bullet points for LLM
        bullets_text = self._format_grouped_bullets(grouped_bullets)
        
        prompt = f"""You are a technical writer creating a concise summary of code changes.

Review the following categorized changes and write a clear, concise summary that:
1. Highlights the main actions and impacts
2. Groups related changes together
3. Uses professional, technical language
4. Keeps the summary under {self.max_summary_length} characters
5. Focuses on WHAT changed and WHY (if apparent)
6. Removes redundant or minor details

Changes by Category:
{bullets_text}

Write a 2-3 sentence summary that captures the essence of these changes:"""

        try:
            summary = self.llm_client.generate(
                prompt,
                max_new_tokens=256,
                temperature=0.5
            )
            
            # Clean up the summary
            summary = summary.strip()
            
            # Ensure it's not too long
            if len(summary) > self.max_summary_length:
                summary = summary[:self.max_summary_length].rsplit('.', 1)[0] + '.'
            
            # Fallback if summary is too short or empty
            if len(summary) < 20:
                logger.warning("LLM summary too short, using fallback")
                summary = self._generate_fallback_summary(grouped_bullets)
            
            return summary
            
        except Exception as e:
            logger.error(f"LLM summary generation failed: {e}, using fallback")
            return self._generate_fallback_summary(grouped_bullets)
    
    def _format_grouped_bullets(self, grouped_bullets: dict) -> str:
        """
        Format grouped bullets for LLM prompt.
        
        Args:
            grouped_bullets: Dictionary of grouped bullets
            
        Returns:
            Formatted string
        """
        sections = []
        
        category_labels = {
            "features": "New Features",
            "fixes": "Bug Fixes",
            "refactoring": "Refactoring",
            "dependencies": "Dependencies",
            "configuration": "Configuration",
            "documentation": "Documentation",
            "tests": "Tests",
            "other": "Other Changes"
        }
        
        for category, bullets in grouped_bullets.items():
            label = category_labels.get(category, category.title())
            bullets_str = '\n'.join(bullets)
            sections.append(f"{label}:\n{bullets_str}")
        
        return '\n\n'.join(sections)
    
    def _generate_fallback_summary(self, grouped_bullets: dict) -> str:
        """
        Generate a simple rule-based summary as fallback.
        
        Args:
            grouped_bullets: Dictionary of grouped bullets
            
        Returns:
            Simple summary string
        """
        parts = []
        
        # Count changes by category
        if "features" in grouped_bullets:
            count = len(grouped_bullets["features"])
            parts.append(f"implemented {count} new feature{'s' if count > 1 else ''}")
        
        if "fixes" in grouped_bullets:
            count = len(grouped_bullets["fixes"])
            parts.append(f"fixed {count} bug{'s' if count > 1 else ''}")
        
        if "refactoring" in grouped_bullets:
            parts.append("refactored code structure")
        
        if "configuration" in grouped_bullets:
            parts.append("updated configuration")
        
        if "dependencies" in grouped_bullets:
            parts.append("updated dependencies")
        
        if "tests" in grouped_bullets:
            parts.append("added tests")
        
        if "documentation" in grouped_bullets:
            parts.append("updated documentation")
        
        if not parts:
            return "Updated codebase with various improvements."
        
        # Join parts into a sentence
        if len(parts) == 1:
            return f"This commit {parts[0]}."
        elif len(parts) == 2:
            return f"This commit {parts[0]} and {parts[1]}."
        else:
            return f"This commit {', '.join(parts[:-1])}, and {parts[-1]}."
    
    def validate_input(self, state: PipelineState) -> bool:
        """
        Validate that state has bullet points.
        
        Args:
            state: Pipeline state
            
        Returns:
            True if valid
        """
        return (
            state.bullet_points is not None and 
            len(state.bullet_points) > 0
        )
