"""
Dataset Extractor

Extracts code diffs and commit messages from raw Kaggle dataset.
Classifies commits by type and complexity for stratified sampling.

Expected dataset format: JSON with structure:
    {
        "commit_hash": str,
        "message": str,
        "diff": str,
        "timestamp": str
    }
"""

import json
import logging
from pathlib import Path
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass, asdict
from enum import Enum
import re

logger = logging.getLogger(__name__)


class CommitType(Enum):
    """Classification of commit types based on conventional commits."""
    BUGFIX = "bugfix"           # fix:
    FEATURE = "feature"         # feat:
    REFACTOR = "refactor"       # refactor:
    CHORE = "chore"             # chore:
    DOCS = "docs"               # docs:
    PERF = "perf"               # perf:
    TEST = "test"               # test:
    STYLE = "style"             # style:
    CI = "ci"                   # ci:
    UNKNOWN = "unknown"


class DiffComplexity(Enum):
    """Classification of diff complexity based on size and scope."""
    SMALL = "small"             # 1-10 files, <100 lines
    MEDIUM = "medium"           # 11-30 files, 100-500 lines
    LARGE = "large"             # 31+ files, 500+ lines


@dataclass
class CommitSample:
    """Single commit sample with metadata."""
    commit_hash: str
    original_message: str
    diff: str
    commit_type: CommitType
    complexity: DiffComplexity
    num_files: int
    num_additions: int
    num_deletions: int
    
    def to_dict(self) -> Dict:
        """Convert to dictionary with enum strings."""
        data = asdict(self)
        data['commit_type'] = self.commit_type.value
        data['complexity'] = self.complexity.value
        return data


class CommitClassifier:
    """Classifies commits by type and complexity."""
    
    @staticmethod
    def classify_type(message: str) -> CommitType:
        """
        Classify commit type from message using conventional commits format.
        
        Examples:
            "fix: resolve null pointer exception" -> BUGFIX
            "feat: add user authentication" -> FEATURE
            "refactor: simplify config loader" -> REFACTOR
        """
        message_lower = message.lower()
        
        # Map of keywords to types
        type_patterns = {
            CommitType.BUGFIX: r'^fix(\(.*\))?:',
            CommitType.FEATURE: r'^feat(\(.*\))?:',
            CommitType.REFACTOR: r'^refactor(\(.*\))?:',
            CommitType.PERF: r'^perf(\(.*\))?:',
            CommitType.DOCS: r'^docs(\(.*\))?:',
            CommitType.TEST: r'^test(\(.*\))?:',
            CommitType.CHORE: r'^chore(\(.*\))?:',
            CommitType.STYLE: r'^style(\(.*\))?:',
            CommitType.CI: r'^ci(\(.*\))?:',
        }
        
        for commit_type, pattern in type_patterns.items():
            if re.match(pattern, message_lower):
                return commit_type
        
        return CommitType.UNKNOWN
    
    @staticmethod
    def classify_complexity(diff: str, num_files: int) -> DiffComplexity:
        """
        Classify diff complexity based on size and scope.
        
        Factors:
            - Number of files changed
            - Total lines added/deleted
        """
        lines = diff.split('\n')
        num_additions = len([l for l in lines if l.startswith('+')])
        num_deletions = len([l for l in lines if l.startswith('-')])
        total_changes = num_additions + num_deletions
        
        if num_files >= 31 or total_changes >= 500:
            return DiffComplexity.LARGE
        elif num_files >= 11 or total_changes >= 100:
            return DiffComplexity.MEDIUM
        else:
            return DiffComplexity.SMALL
    
    @staticmethod
    def count_files_in_diff(diff: str) -> int:
        """Count number of files changed in diff."""
        return len(re.findall(r'^diff --git', diff, re.MULTILINE))


class DatasetExtractor:
    """Extracts and prepares commit dataset from raw Kaggle data."""
    
    def __init__(self, dataset_path: Path, output_dir: Path, allow_message_only: bool = False):
        """
        Initialize extractor.
        
        Args:
            dataset_path: Path to raw dataset JSON
            output_dir: Directory for extracted data
        """
        self.dataset_path = Path(dataset_path)
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.classifier = CommitClassifier()
        # If True, allow commits that only have a message (empty diff).
        # Useful when the dataset contains only commit messages without patches.
        self.allow_message_only = allow_message_only
        
        if not self.dataset_path.exists():
            logger.warning(f"Dataset not found at {dataset_path}")
    
    def extract(self, limit: Optional[int] = None) -> List[CommitSample]:
        """
        Extract commits from dataset.
        
        Args:
            limit: Maximum number of commits to extract (None = all)
            
        Returns:
            List of CommitSample objects
        """
        logger.info(f"Extracting commits from {self.dataset_path}")
        
        samples = []
        
        if not self.dataset_path.exists():
            logger.warning(f"Dataset not found at {self.dataset_path}. Returning empty list.")
            return samples
        
        try:
            with open(self.dataset_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
        except (json.JSONDecodeError, IOError) as e:
            logger.error(f"Failed to load dataset: {e}")
            return samples
        
        # Handle both list and dict formats
        commits = data if isinstance(data, list) else data.get('commits', [])
        
        for i, commit in enumerate(commits):
            if limit and i >= limit:
                break
            
            try:
                sample = self._process_commit(commit)
                if sample:
                    samples.append(sample)
            except Exception as e:
                logger.warning(f"Failed to process commit {i}: {e}")
                continue
        
        logger.info(f"Extracted {len(samples)} valid commits")
        return samples
    
    def _process_commit(self, commit: Dict) -> Optional[CommitSample]:
        """
        Process single commit into CommitSample.
        
        Validates required fields and extracts metadata.
        """
        # Validate required fields (commit_hash and message required)
        required_fields = ['commit_hash', 'message']
        if not all(field in commit for field in required_fields):
            return None

        message = (commit.get('message') or '').strip()
        diff = (commit.get('diff') or '').strip()

        # Skip if no message
        if not message:
            return None

        # If diff is empty and message-only commits are not allowed, skip
        if not diff and not self.allow_message_only:
            return None

        # Extract metadata
        num_files = self.classifier.count_files_in_diff(diff) if diff else 0
        if num_files == 0 and not self.allow_message_only:
            return None
        
        commit_type = self.classifier.classify_type(message)
        # Compute complexity using the classifier (will return SMALL for empty diffs)
        complexity = self.classifier.classify_complexity(diff, num_files)

        # Count additions/deletions
        num_additions = len([l for l in diff.split('\n') if l.startswith('+')]) if diff else 0
        num_deletions = len([l for l in diff.split('\n') if l.startswith('-')]) if diff else 0
        
        return CommitSample(
            commit_hash=commit['commit_hash'],
            original_message=message,
            diff=diff,
            commit_type=commit_type,
            complexity=complexity,
            num_files=num_files,
            num_additions=num_additions,
            num_deletions=num_deletions
        )
    
    def save_extracted(self, samples: List[CommitSample], filename: str = "extracted_commits.json"):
        """Save extracted samples to JSON file."""
        output_path = self.output_dir / filename
        
        data = {
            'total': len(samples),
            'by_type': self._count_by_type(samples),
            'by_complexity': self._count_by_complexity(samples),
            'commits': [s.to_dict() for s in samples]
        }
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        
        logger.info(f"Saved {len(samples)} extracted commits to {output_path}")
        return output_path
    
    def _count_by_type(self, samples: List[CommitSample]) -> Dict[str, int]:
        """Count samples by commit type."""
        counts = {}
        for sample in samples:
            key = sample.commit_type.value
            counts[key] = counts.get(key, 0) + 1
        return counts
    
    def _count_by_complexity(self, samples: List[CommitSample]) -> Dict[str, int]:
        """Count samples by complexity."""
        counts = {}
        for sample in samples:
            key = sample.complexity.value
            counts[key] = counts.get(key, 0) + 1
        return counts


def main():
    """Example usage."""
    import sys
    
    # Configure logging
    logging.basicConfig(level=logging.INFO)
    
    # Paths
    dataset_path = Path("evaluation/data/raw_dataset/commits.json")
    output_dir = Path("evaluation/data/extracted")
    
    # Extract
    extractor = DatasetExtractor(dataset_path, output_dir)
    samples = extractor.extract()
    
    # Save
    if samples:
        extractor.save_extracted(samples)
        
        # Print summary
        print(f"\n=== Extraction Summary ===")
        print(f"Total commits: {len(samples)}")
        print(f"\nBy Type:")
        for ctype, count in extractor._count_by_type(samples).items():
            print(f"  {ctype}: {count}")
        print(f"\nBy Complexity:")
        for complexity, count in extractor._count_by_complexity(samples).items():
            print(f"  {complexity}: {count}")
    else:
        print("No commits extracted. Check dataset path and format.")
        sys.exit(1)


if __name__ == "__main__":
    main()
