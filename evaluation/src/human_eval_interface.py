"""
Human Evaluation Interface

Interface for collecting human developer feedback on sampled commit messages.

Evaluators rate messages on:
- Readability: How easy is the message to understand?
- Completeness: Does it capture all important changes?
- Suitability: Would you use this in actual Git workflow?

Also collects free-form feedback and suggestions.
"""

import json
import logging
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, asdict, field
from enum import Enum
from datetime import datetime

logger = logging.getLogger(__name__)


class RatingScale(Enum):
    """5-point rating scale for human evaluation."""
    POOR = 1
    FAIR = 2
    GOOD = 3
    VERY_GOOD = 4
    EXCELLENT = 5


@dataclass
class EvaluationConfig:
    """Configuration for human evaluation."""
    sample_size: int = 50
    min_per_type: int = 5
    min_per_complexity: int = 5
    
    # Rating scales
    readability_scale: int = 5  # 1-5
    completeness_scale: int = 5  # 1-5
    suitability_scale: int = 5  # 1-5


@dataclass
class HumanEvaluation:
    """Single human evaluation of a commit message."""
    commit_hash: str
    evaluator_name: str
    evaluation_date: str  # ISO format
    
    # Ratings (1-5)
    readability_rating: int
    completeness_rating: int
    suitability_rating: int
    
    # Feedback
    feedback: str = ""
    suggestion: Optional[str] = None
    issues_found: List[str] = field(default_factory=list)
    
    def average_rating(self) -> float:
        """Average of all ratings."""
        return (self.readability_rating + self.completeness_rating + 
                self.suitability_rating) / 3.0
    
    def to_dict(self) -> Dict:
        """Convert to dictionary."""
        return asdict(self)


@dataclass
class EvaluationSummary:
    """Summary of evaluations for a single message."""
    commit_hash: str
    generated_message: str
    reference_message: str
    commit_type: str
    complexity: str
    
    evaluations: List[HumanEvaluation] = field(default_factory=list)
    
    def average_readability(self) -> float:
        """Average readability rating."""
        if not self.evaluations:
            return 0.0
        return sum(e.readability_rating for e in self.evaluations) / len(self.evaluations)
    
    def average_completeness(self) -> float:
        """Average completeness rating."""
        if not self.evaluations:
            return 0.0
        return sum(e.completeness_rating for e in self.evaluations) / len(self.evaluations)
    
    def average_suitability(self) -> float:
        """Average suitability rating."""
        if not self.evaluations:
            return 0.0
        return sum(e.suitability_rating for e in self.evaluations) / len(self.evaluations)
    
    def overall_score(self) -> float:
        """Overall evaluation score."""
        return (self.average_readability() + self.average_completeness() + 
                self.average_suitability()) / 3.0
    
    def to_dict(self) -> Dict:
        """Convert to dictionary."""
        return {
            'commit_hash': self.commit_hash,
            'generated_message': self.generated_message,
            'reference_message': self.reference_message,
            'commit_type': self.commit_type,
            'complexity': self.complexity,
            'average_readability': self.average_readability(),
            'average_completeness': self.average_completeness(),
            'average_suitability': self.average_suitability(),
            'overall_score': self.overall_score(),
            'evaluations': [e.to_dict() for e in self.evaluations],
            'num_evaluators': len(self.evaluations)
        }


class HumanEvaluationInterface:
    """
    Interface for human evaluation of commit messages.
    
    Supports:
    - CLI-based evaluation
    - Web interface integration
    - Batch export/import
    """
    
    def __init__(self, config: Optional[EvaluationConfig] = None):
        """Initialize interface."""
        self.config = config or EvaluationConfig()
        self.evaluations: Dict[str, EvaluationSummary] = {}
    
    def load_samples(self, samples_file: Path) -> List[Dict]:
        """
        Load samples prepared for human evaluation.
        
        Args:
            samples_file: Path to human_eval_samples.json
            
        Returns:
            List of sample dicts with commit info and metrics
        """
        with open(samples_file, 'r') as f:
            data = json.load(f)
        
        return data.get('samples', [])
    
    def collect_evaluation(self, commit_hash: str, generated: str, 
                          reference: str, commit_type: str, complexity: str,
                          evaluator_name: str, readability: int, 
                          completeness: int, suitability: int,
                          feedback: str = "", suggestion: Optional[str] = None,
                          issues: Optional[List[str]] = None) -> HumanEvaluation:
        """
        Record a human evaluation.
        
        Args:
            commit_hash: Commit identifier
            generated: Generated message
            reference: Reference message
            commit_type: Type of commit
            complexity: Diff complexity
            evaluator_name: Name of evaluator
            readability: Rating 1-5
            completeness: Rating 1-5
            suitability: Rating 1-5
            feedback: Optional feedback
            suggestion: Optional suggestion for improvement
            issues: Optional list of issues found
            
        Returns:
            Recorded HumanEvaluation
        """
        # Create evaluation
        evaluation = HumanEvaluation(
            commit_hash=commit_hash,
            evaluator_name=evaluator_name,
            evaluation_date=datetime.now().isoformat(),
            readability_rating=readability,
            completeness_rating=completeness,
            suitability_rating=suitability,
            feedback=feedback,
            suggestion=suggestion,
            issues_found=issues or []
        )
        
        # Add to summary
        if commit_hash not in self.evaluations:
            self.evaluations[commit_hash] = EvaluationSummary(
                commit_hash=commit_hash,
                generated_message=generated,
                reference_message=reference,
                commit_type=commit_type,
                complexity=complexity
            )
        
        self.evaluations[commit_hash].evaluations.append(evaluation)
        
        logger.info(f"Recorded evaluation for {commit_hash} by {evaluator_name}")
        return evaluation
    
    def get_evaluation_stats(self) -> Dict:
        """Get overall evaluation statistics."""
        if not self.evaluations:
            return {}
        
        summaries = list(self.evaluations.values())
        
        readability_scores = [s.average_readability() for s in summaries]
        completeness_scores = [s.average_completeness() for s in summaries]
        suitability_scores = [s.average_suitability() for s in summaries]
        overall_scores = [s.overall_score() for s in summaries]
        
        return {
            'total_evaluated': len(self.evaluations),
            'total_evaluations': sum(len(s.evaluations) for s in summaries),
            'average_evaluators_per_sample': (
                sum(len(s.evaluations) for s in summaries) / len(summaries)
                if summaries else 0
            ),
            'readability': {
                'mean': sum(readability_scores) / len(readability_scores),
                'min': min(readability_scores),
                'max': max(readability_scores)
            },
            'completeness': {
                'mean': sum(completeness_scores) / len(completeness_scores),
                'min': min(completeness_scores),
                'max': max(completeness_scores)
            },
            'suitability': {
                'mean': sum(suitability_scores) / len(suitability_scores),
                'min': min(suitability_scores),
                'max': max(suitability_scores)
            },
            'overall': {
                'mean': sum(overall_scores) / len(overall_scores),
                'min': min(overall_scores),
                'max': max(overall_scores)
            }
        }
    
    def save_evaluations(self, output_file: Path):
        """Save all evaluations to JSON."""
        output_file = Path(output_file)
        output_file.parent.mkdir(parents=True, exist_ok=True)
        
        data = {
            'timestamp': datetime.now().isoformat(),
            'stats': self.get_evaluation_stats(),
            'evaluations': {
                commit_hash: summary.to_dict()
                for commit_hash, summary in self.evaluations.items()
            }
        }
        
        with open(output_file, 'w') as f:
            json.dump(data, f, indent=2)
        
        logger.info(f"Saved {len(self.evaluations)} evaluations to {output_file}")
    
    def export_for_review(self, output_file: Path, include_metrics: bool = True):
        """
        Export evaluations in human-readable format.
        
        Useful for reports and presentations.
        """
        output_file = Path(output_file)
        output_file.parent.mkdir(parents=True, exist_ok=True)
        
        lines = [
            "=" * 80,
            "HUMAN EVALUATION REPORT",
            "=" * 80,
            f"Report generated: {datetime.now().isoformat()}",
            f"Total samples evaluated: {len(self.evaluations)}",
            ""
        ]
        
        # Summary statistics
        stats = self.get_evaluation_stats()
        if stats:
            lines.extend([
                "SUMMARY STATISTICS",
                "-" * 80,
                f"Average Readability: {stats['readability']['mean']:.2f}/5",
                f"Average Completeness: {stats['completeness']['mean']:.2f}/5",
                f"Average Suitability: {stats['suitability']['mean']:.2f}/5",
                f"Overall Average: {stats['overall']['mean']:.2f}/5",
                ""
            ])
        
        # Individual evaluations
        lines.append("INDIVIDUAL EVALUATIONS")
        lines.append("-" * 80)
        
        for commit_hash, summary in self.evaluations.items():
            lines.extend([
                f"\nCommit: {commit_hash}",
                f"Type: {summary.commit_type}, Complexity: {summary.complexity}",
                f"Generated: {summary.generated_message[:70]}...",
                f"Reference: {summary.reference_message[:70]}...",
                f"\nRatings (from {len(summary.evaluations)} evaluator(s)):",
                f"  Readability: {summary.average_readability():.1f}/5",
                f"  Completeness: {summary.average_completeness():.1f}/5",
                f"  Suitability: {summary.average_suitability():.1f}/5",
                f"  Overall: {summary.overall_score():.1f}/5",
            ])
            
            if summary.evaluations:
                lines.append("\nEvaluator Feedback:")
                for eval in summary.evaluations:
                    lines.extend([
                        f"  [{eval.evaluator_name}]",
                        f"    {eval.feedback}",
                    ])
                    if eval.suggestion:
                        lines.append(f"    Suggestion: {eval.suggestion}")
                    if eval.issues_found:
                        lines.append(f"    Issues: {', '.join(eval.issues_found)}")
            
            lines.append("")
        
        # Write file
        with open(output_file, 'w') as f:
            f.write('\n'.join(lines))
        
        logger.info(f"Exported human evaluation report to {output_file}")


class CLIEvaluator:
    """
    CLI interface for human evaluation.
    
    Provides interactive command-line interface for evaluators to rate messages.
    """
    
    def __init__(self, interface: HumanEvaluationInterface):
        """Initialize CLI evaluator."""
        self.interface = interface
    
    def interactive_session(self, samples_file: Path, evaluator_name: str):
        """
        Run interactive evaluation session.
        
        Args:
            samples_file: Path to human_eval_samples.json
            evaluator_name: Name of the evaluator
        """
        samples = self.interface.load_samples(samples_file)
        
        if not samples:
            print("No samples loaded.")
            return
        
        print(f"\n{'='*80}")
        print(f"Human Evaluation Session - {evaluator_name}")
        print(f"{'='*80}")
        print(f"Total samples to evaluate: {len(samples)}\n")
        
        for i, sample in enumerate(samples, 1):
            self._evaluate_sample(sample, i, len(samples), evaluator_name)
    
    def _evaluate_sample(self, sample: Dict, index: int, total: int, evaluator_name: str):
        """Evaluate a single sample."""
        print(f"\n{'─'*80}")
        print(f"Sample {index}/{total}")
        print(f"{'─'*80}")
        
        print(f"\nCommit Hash: {sample['commit_hash']}")
        print(f"Type: {sample['commit_type']}, Complexity: {sample['complexity']}")
        
        print(f"\nDiff Preview (first 500 chars):")
        print(f"  {sample['diff'][:500]}...")
        
        print(f"\nGenerated Message:")
        print(f"  {sample['generated_message']}")
        
        print(f"\nReference Message:")
        print(f"  {sample['reference_message']}")
        
        # Collect ratings
        print(f"\nPlease rate this generated message (1=Poor, 5=Excellent):")
        
        readability = self._get_rating("Readability (1-5): ")
        completeness = self._get_rating("Completeness (1-5): ")
        suitability = self._get_rating("Suitability for Git workflow (1-5): ")
        
        # Collect feedback
        feedback = input("\nOptional feedback: ").strip()
        suggestion = input("Optional suggestion for improvement: ").strip() or None
        
        # Record
        self.interface.collect_evaluation(
            commit_hash=sample['commit_hash'],
            generated=sample['generated_message'],
            reference=sample['reference_message'],
            commit_type=sample['commit_type'],
            complexity=sample['complexity'],
            evaluator_name=evaluator_name,
            readability=readability,
            completeness=completeness,
            suitability=suitability,
            feedback=feedback,
            suggestion=suggestion
        )
        
        print("✓ Evaluation recorded")
    
    def _get_rating(self, prompt: str) -> int:
        """Get valid rating input."""
        while True:
            try:
                rating = int(input(prompt))
                if 1 <= rating <= 5:
                    return rating
                print("Please enter a number between 1 and 5")
            except ValueError:
                print("Please enter a valid number")


def main():
    """Example CLI evaluation session."""
    import sys
    
    logging.basicConfig(level=logging.INFO)
    
    # Configuration
    config = EvaluationConfig(sample_size=50)
    interface = HumanEvaluationInterface(config)
    
    # Sample file
    samples_file = Path("evaluation/data/results/human_eval_samples.json")
    
    if not samples_file.exists():
        print(f"Error: {samples_file} not found")
        print("Run the evaluation pipeline first.")
        sys.exit(1)
    
    # Get evaluator name
    evaluator_name = input("Enter your name as evaluator: ").strip()
    if not evaluator_name:
        evaluator_name = "Unknown"
    
    # Run interactive session
    cli = CLIEvaluator(interface)
    
    try:
        cli.interactive_session(samples_file, evaluator_name)
        
        # Save evaluations
        output_file = Path("evaluation/data/results/human_evaluations.json")
        interface.save_evaluations(output_file)
        
        # Export report
        report_file = Path("evaluation/data/results/human_evaluation_report.txt")
        interface.export_for_review(report_file)
        
        print("\n✓ Evaluation session complete!")
        print(f"Results saved to: {output_file}")
        print(f"Report saved to: {report_file}")
        
    except KeyboardInterrupt:
        print("\n\nEvaluation interrupted by user")
        # Still save what we have
        output_file = Path("evaluation/data/results/human_evaluations_partial.json")
        interface.save_evaluations(output_file)
        print(f"Partial results saved to: {output_file}")
        sys.exit(1)


if __name__ == "__main__":
    main()
