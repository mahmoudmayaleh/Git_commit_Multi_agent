"""
Test Set Builder

Creates a stratified test set ensuring balanced representation across:
- Commit types (bugfix, feature, refactor, etc.)
- Diff complexities (small, medium, large)

This ensures evaluation results are representative and not biased toward
any particular type of commit.
"""

import json
import logging
from pathlib import Path
from typing import List, Dict, Tuple, Optional
from dataclasses import dataclass, asdict
from collections import defaultdict
import random

from dataset_extractor import CommitSample, CommitType, DiffComplexity

logger = logging.getLogger(__name__)


@dataclass
class StratificationConfig:
    """Configuration for test set stratification."""
    total_size: int = 200  # Total test samples
    min_per_type: int = 5  # Minimum per commit type
    min_per_complexity: int = 10  # Minimum per complexity level
    stratify_by_both: bool = True  # Ensure diversity on both dimensions
    random_seed: int = 42


class TestSetBuilder:
    """Builds stratified test sets from extracted commits."""
    
    def __init__(self, config: Optional[StratificationConfig] = None):
        """
        Initialize builder.
        
        Args:
            config: Stratification configuration
        """
        self.config = config or StratificationConfig()
        random.seed(self.config.random_seed)
    
    def build(self, samples: List[CommitSample]) -> Tuple[List[CommitSample], Dict]:
        """
        Build stratified test set from samples.
        
        Returns:
            Tuple of (test_samples, stratification_report)
        """
        logger.info(f"Building test set with {self.config.total_size} samples from {len(samples)} total")
        
        # Group by type and complexity
        groups = self._group_samples(samples)
        
        # Select samples ensuring stratification
        test_samples = self._stratified_sample(groups)
        
        # Generate report
        report = self._generate_report(samples, test_samples, groups)
        
        logger.info(f"Selected {len(test_samples)} test samples")
        return test_samples, report
    
    def _group_samples(self, samples: List[CommitSample]) -> Dict:
        """
        Group samples by type and complexity.
        
        Returns:
            Dict structure:
            {
                commit_type: {
                    complexity: [samples]
                }
            }
        """
        groups = defaultdict(lambda: defaultdict(list))
        
        for sample in samples:
            type_key = sample.commit_type.value
            complexity_key = sample.complexity.value
            groups[type_key][complexity_key].append(sample)
        
        return dict(groups)
    
    def _stratified_sample(self, groups: Dict) -> List[CommitSample]:
        """
        Select samples ensuring representation across strata.
        
        Strategy:
        1. First pass: Ensure minimum per type
        2. Second pass: Ensure minimum per complexity
        3. Third pass: Fill remaining slots with balanced distribution
        """
        selected = []
        used_indices = set()
        
        # Flatten for easier indexing
        all_samples = []
        sample_to_group = {}  # Track which group each sample came from
        
        for ctype, complexities in groups.items():
            for complexity, samples in complexities.items():
                for sample in samples:
                    all_samples.append(sample)
                    sample_to_group[id(sample)] = (ctype, complexity)
        
        # Random shuffle
        random.shuffle(all_samples)
        
        # Phase 1: Ensure minimum per type
        type_counts = defaultdict(int)
        for sample in all_samples:
            ctype = sample.commit_type.value
            if type_counts[ctype] < self.config.min_per_type:
                selected.append(sample)
                type_counts[ctype] += 1
        
        # Phase 2: Ensure minimum per complexity
        complexity_counts = defaultdict(int)
        for sample in all_samples:
            if sample in selected:
                complexity = sample.complexity.value
                complexity_counts[complexity] += 1
        
        for sample in all_samples:
            if sample in selected:
                continue
            if len(selected) >= self.config.total_size:
                break
            complexity = sample.complexity.value
            if complexity_counts[complexity] < self.config.min_per_complexity:
                selected.append(sample)
                complexity_counts[complexity] += 1
        
        # Phase 3: Fill remaining slots with balanced distribution
        remaining = [s for s in all_samples if s not in selected]
        random.shuffle(remaining)
        
        for sample in remaining:
            if len(selected) >= self.config.total_size:
                break
            selected.append(sample)
        
        return selected
    
    def _generate_report(self, all_samples: List[CommitSample], 
                         test_samples: List[CommitSample], groups: Dict) -> Dict:
        """Generate stratification report."""
        
        # Count distributions
        test_by_type = defaultdict(int)
        test_by_complexity = defaultdict(int)
        test_by_both = defaultdict(lambda: defaultdict(int))
        
        for sample in test_samples:
            test_by_type[sample.commit_type.value] += 1
            test_by_complexity[sample.complexity.value] += 1
            test_by_both[sample.commit_type.value][sample.complexity.value] += 1
        
        all_by_type = defaultdict(int)
        all_by_complexity = defaultdict(int)
        
        for sample in all_samples:
            all_by_type[sample.commit_type.value] += 1
            all_by_complexity[sample.complexity.value] += 1
        
        # Build report
        report = {
            'total_samples': len(test_samples),
            'source_samples': len(all_samples),
            'by_type': {
                'test': dict(test_by_type),
                'all': dict(all_by_type),
                'coverage_percentage': {
                    ctype: (test_by_type[ctype] / max(all_by_type[ctype], 1)) * 100
                    for ctype in all_by_type
                }
            },
            'by_complexity': {
                'test': dict(test_by_complexity),
                'all': dict(all_by_complexity),
                'coverage_percentage': {
                    complexity: (test_by_complexity[complexity] / max(all_by_complexity[complexity], 1)) * 100
                    for complexity in all_by_complexity
                }
            },
            'by_both_dimensions': {
                ctype: dict(complexities)
                for ctype, complexities in test_by_both.items()
            },
            'config': {
                'total_size': self.config.total_size,
                'min_per_type': self.config.min_per_type,
                'min_per_complexity': self.config.min_per_complexity,
                'stratify_by_both': self.config.stratify_by_both
            }
        }
        
        return report
    
    def save_test_set(self, test_samples: List[CommitSample], 
                      report: Dict, output_dir: Path):
        """Save test set and stratification report."""
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)
        
        # Save test set
        test_file = output_dir / "test_samples.json"
        test_data = {
            'metadata': {
                'total': len(test_samples),
                'created_from': 'stratified_sampling'
            },
            'samples': [s.to_dict() for s in test_samples]
        }
        
        with open(test_file, 'w', encoding='utf-8') as f:
            json.dump(test_data, f, indent=2, ensure_ascii=False)
        
        logger.info(f"Saved test set to {test_file}")
        
        # Save stratification report
        report_file = output_dir / "stratification_report.json"
        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, ensure_ascii=False)
        
        logger.info(f"Saved stratification report to {report_file}")
        
        # Save human-readable summary
        summary_file = output_dir / "stratification_report.txt"
        with open(summary_file, 'w', encoding='utf-8') as f:
            f.write(self._format_report(report))
        
        logger.info(f"Saved stratification summary to {summary_file}")
    
    def _format_report(self, report: Dict) -> str:
        """Format report as readable text."""
        lines = [
            "=" * 60,
            "STRATIFICATION REPORT",
            "=" * 60,
            f"\nTotal test samples: {report['total_samples']}",
            f"Source samples: {report['source_samples']}",
            f"\nConfiguration:",
            f"  - Total size: {report['config']['total_size']}",
            f"  - Min per type: {report['config']['min_per_type']}",
            f"  - Min per complexity: {report['config']['min_per_complexity']}",
            f"\nDISTRIBUTION BY TYPE",
            "-" * 60,
        ]
        
        for ctype in sorted(report['by_type']['test'].keys()):
            test_count = report['by_type']['test'].get(ctype, 0)
            all_count = report['by_type']['all'].get(ctype, 0)
            coverage = report['by_type']['coverage_percentage'].get(ctype, 0)
            lines.append(f"{ctype:15} | Test: {test_count:3d} | All: {all_count:4d} | Coverage: {coverage:5.1f}%")
        
        lines.extend([
            f"\nDISTRIBUTION BY COMPLEXITY",
            "-" * 60,
        ])
        
        for complexity in ['small', 'medium', 'large']:
            test_count = report['by_complexity']['test'].get(complexity, 0)
            all_count = report['by_complexity']['all'].get(complexity, 0)
            coverage = report['by_complexity']['coverage_percentage'].get(complexity, 0)
            lines.append(f"{complexity:15} | Test: {test_count:3d} | All: {all_count:4d} | Coverage: {coverage:5.1f}%")
        
        lines.extend([
            f"\nDISTRIBUTION BY TYPE AND COMPLEXITY",
            "-" * 60,
        ])
        
        for ctype in sorted(report['by_both_dimensions'].keys()):
            lines.append(f"\n{ctype}:")
            for complexity in ['small', 'medium', 'large']:
                count = report['by_both_dimensions'][ctype].get(complexity, 0)
                lines.append(f"  {complexity:12}: {count:3d}")
        
        return "\n".join(lines)


def main():
    """Example usage."""
    import sys
    
    logging.basicConfig(level=logging.INFO)
    
    # Load extracted commits
    extracted_file = Path("evaluation/data/extracted/extracted_commits.json")
    
    if not extracted_file.exists():
        logger.error(f"Extracted commits not found at {extracted_file}")
        logger.error("Run dataset_extractor.py first")
        sys.exit(1)
    
    # Load samples
    with open(extracted_file, 'r') as f:
        data = json.load(f)
    
    samples = []
    for commit_data in data['commits']:
        sample = CommitSample(
            commit_hash=commit_data['commit_hash'],
            original_message=commit_data['original_message'],
            diff=commit_data['diff'],
            commit_type=CommitType(commit_data['commit_type']),
            complexity=DiffComplexity(commit_data['complexity']),
            num_files=commit_data['num_files'],
            num_additions=commit_data['num_additions'],
            num_deletions=commit_data['num_deletions']
        )
        samples.append(sample)
    
    # Build test set
    config = StratificationConfig(total_size=200)
    builder = TestSetBuilder(config)
    test_samples, report = builder.build(samples)
    
    # Save
    output_dir = Path("evaluation/data/test_set")
    builder.save_test_set(test_samples, report, output_dir)
    
    print("\nTest set creation complete!")


if __name__ == "__main__":
    main()
