"""
Main Evaluation Orchestrator

Coordinates the complete evaluation pipeline:
1. Test Case Preparation (dataset extraction + stratification)
2. Automated Evaluation (metrics calculation)
3. Error Analysis (error taxonomy)
4. Human Evaluation (sampling + interface)

Run this to execute the full evaluation workflow.
"""

import logging
import json
from pathlib import Path
from typing import Optional, List, Tuple
from dataclasses import dataclass
from datetime import datetime

from dataset_extractor import DatasetExtractor, CommitSample, CommitType, DiffComplexity
from test_set_builder import TestSetBuilder, StratificationConfig
from metrics_calculator import MetricsCalculator, MetricsAnalyzer, save_metrics
from error_taxonomy import ErrorTaxonomy
from human_eval_interface import HumanEvaluationInterface, EvaluationConfig

logger = logging.getLogger(__name__)


@dataclass
class EvaluationConfig:
    """Configuration for the entire evaluation pipeline."""
    
    # Dataset extraction
    dataset_path: Path = Path("evaluation/data/raw_dataset/commits.json")
    max_extract: Optional[int] = None  # None = all commits
    
    # Test set
    test_set_size: int = 200
    min_per_type: int = 5
    min_per_complexity: int = 10
    random_seed: int = 42
    
    # Evaluation
    bert_model: str = "microsoft/deberta-xlarge-mnli"
    device: str = "cpu"  # or "cuda"
    use_bertscore: bool = False  # Set to False to skip BERTScore (lighter, faster)
    
    # Human evaluation
    human_eval_sample_size: int = 50
    min_human_eval_per_type: int = 5
    
    # Output directory
    output_dir: Path = Path("evaluation/data/results")


class EvaluationPipeline:
    """Main evaluation pipeline orchestrator."""
    
    def __init__(self, config: Optional[EvaluationConfig] = None):
        """Initialize pipeline."""
        self.config = config or EvaluationConfig()
        self.config.output_dir.mkdir(parents=True, exist_ok=True)
        
        logger.info(f"Initialized evaluation pipeline with output: {self.config.output_dir}")
    
    def run_full_pipeline(self):
        """Run complete evaluation pipeline."""
        logger.info("Starting full evaluation pipeline")        
        # Phase 1: Test preparation
        logger.info("\n" + "="*60)
        logger.info("PHASE 1: TEST CASE PREPARATION")
        logger.info("="*60)
        test_samples, stratification_report = self.phase_test_preparation()
        
        # Phase 2: Automated evaluation
        logger.info("\n" + "="*60)
        logger.info("PHASE 2: AUTOMATED EVALUATION")
        logger.info("="*60)
        metric_scores = self.phase_automated_evaluation(test_samples)
        
        # Phase 3: Error analysis
        logger.info("\n" + "="*60)
        logger.info("PHASE 3: ERROR ANALYSIS")
        logger.info("="*60)
        error_taxonomy = self.phase_error_analysis(test_samples, metric_scores)
        
        # Phase 4: Human evaluation preparation
        logger.info("\n" + "="*60)
        logger.info("PHASE 4: HUMAN EVALUATION SAMPLING")
        logger.info("="*60)
        human_eval_samples = self.phase_human_evaluation_prep(test_samples, metric_scores)
        
        # Generate final summary
        logger.info("\n" + "="*60)
        logger.info("EVALUATION COMPLETE")
        logger.info("="*60)
        self._print_summary(stratification_report, metric_scores, error_taxonomy)
        
        return {
            'test_samples': test_samples,
            'stratification_report': stratification_report,
            'metric_scores': metric_scores,
            'error_taxonomy': error_taxonomy,
            'human_eval_samples': human_eval_samples
        }
    
    def phase_test_preparation(self) -> Tuple[List[CommitSample], dict]:
        """
        Phase 1: Extract commits and build stratified test set.
        
        Returns:
            Tuple of (test_samples, stratification_report)
        """
        logger.info("Extracting commits from dataset...")
        
        # Extract
        extractor = DatasetExtractor(self.config.dataset_path, self.config.output_dir / "extracted", allow_message_only=True)
        samples = extractor.extract(limit=self.config.max_extract)
        
        if not samples:
            logger.error("No commits extracted. Check dataset path.")
            return [], {}
        
        logger.info(f"Extracted {len(samples)} commits")
        extractor.save_extracted(samples)
        
        # Build stratified test set
        logger.info(f"Building stratified test set of size {self.config.test_set_size}...")
        
        strat_config = StratificationConfig(
            total_size=self.config.test_set_size,
            min_per_type=self.config.min_per_type,
            min_per_complexity=self.config.min_per_complexity,
            random_seed=self.config.random_seed
        )
        
        builder = TestSetBuilder(strat_config)
        test_samples, stratification_report = builder.build(samples)
        
        # Save test set
        test_set_dir = self.config.output_dir / "test_set"
        builder.save_test_set(test_samples, stratification_report, test_set_dir)
        
        logger.info(f"Created test set with {len(test_samples)} samples")
        
        return test_samples, stratification_report
    
    def phase_automated_evaluation(self, test_samples: List[CommitSample]):
        """
        Phase 2: Generate commit messages and compute metrics.
        
        For this to work, you need to:
        1. Run the commit pipeline on each diff to generate messages
        2. Compare with reference messages
        
        This is a placeholder that shows the structure.
        """
        logger.info("Computing metrics for all test samples...")
        
        # TODO: Replace with actual commit message generation
        # For now, we'll create mock generated messages for demonstration
        
        calculator = MetricsCalculator(
            model_name=self.config.bert_model,
            device=self.config.device
        )
        
        # Prepare pairs for evaluation
        pairs = []
        for sample in test_samples:
            # TODO: Generate message using your commit pipeline
            # For demo, use a simple baseline
            generated = self._generate_baseline_message(sample)
            pairs.append((sample.commit_hash, generated, sample.original_message))
        
        # Compute metrics
        metric_scores = calculator.compute_batch(pairs)
        
        # Save metrics
        metrics_file = self.config.output_dir / "automated_metrics.json"
        save_metrics(metric_scores, metrics_file)
        
        # Analyze
        analyzer = MetricsAnalyzer()
        summary = analyzer.summarize(metric_scores)
        
        logger.info(f"Computed metrics for {len(metric_scores)} samples")
        if summary and 'average' in summary:
            logger.info(f"Average quality score: {summary['average']['mean']:.3f}")
        
        return metric_scores
    
    def phase_error_analysis(self, test_samples: List[CommitSample], metric_scores):
        """
        Phase 3: Analyze errors and low-quality messages.
        """
        logger.info("Analyzing errors and message quality...")
        
        # Create assessment triples
        triples = [
            (sample.commit_hash, 
             score.generated_message,
             score.reference_message)
            for sample, score in zip(test_samples, metric_scores)
        ]
        
        # Get diffs for hallucination detection
        diffs = [sample.diff for sample in test_samples]
        
        # Assess
        taxonomy = ErrorTaxonomy()
        assessments = taxonomy.assess_messages(triples, diffs)
        
        # Save
        taxonomy_file = self.config.output_dir / "error_taxonomy.json"
        taxonomy.save_report(taxonomy_file)
        
        # Report
        report = taxonomy.generate_report()
        logger.info(f"Messages with errors: {report['messages_with_errors']}")
        logger.info(f"Usable messages: {report['usable_messages']} ({report['usable_percentage']:.1f}%)")
        logger.info(f"Most common error: {report['most_common_error']}")
        
        return taxonomy
    
    def phase_human_evaluation_prep(self, test_samples: List[CommitSample], metric_scores):
        """
        Phase 4: Prepare samples for human evaluation.
        
        Samples stratified across complexity and commit type.
        """
        logger.info(f"Sampling {self.config.human_eval_sample_size} cases for human review...")
        
        # Create sample info with metrics
        sample_info = []
        for sample, score in zip(test_samples, metric_scores):
            sample_info.append({
                'sample': sample,
                'generated': score.generated_message,
                'reference': score.reference_message,
                'metrics': {
                    'bleu': score.bleu,
                    'rouge1': score.rouge1,
                    'rouge2': score.rouge2,
                    'rougeL': score.rougeL,
                    'bertscore': score.bertscore
                }
            })
        
        # Stratified sampling
        human_eval_samples = self._stratified_sample_for_human_eval(
            sample_info,
            self.config.human_eval_sample_size
        )
        
        # Save for human evaluation
        human_eval_file = self.config.output_dir / "human_eval_samples.json"
        human_eval_data = {
            'total': len(human_eval_samples),
            'samples': [
                {
                    'commit_hash': s['sample'].commit_hash,
                    'diff': s['sample'].diff,
                    'generated_message': s['generated'],
                    'reference_message': s['reference'],
                    'commit_type': s['sample'].commit_type.value,
                    'complexity': s['sample'].complexity.value,
                    'metrics': s['metrics']
                }
                for s in human_eval_samples
            ]
        }
        
        with open(human_eval_file, 'w') as f:
            json.dump(human_eval_data, f, indent=2)
        
        logger.info(f"Prepared {len(human_eval_samples)} samples for human review")
        
        return human_eval_samples
    
    def _generate_baseline_message(self, sample: CommitSample) -> str:
        """
        Generate a baseline commit message.
        
        TODO: Replace with actual call to your commit pipeline.
        """
        # Simple baseline: type + first line of reference
        ctype = sample.commit_type.value
        first_line = sample.original_message.split('\n')[0]
        
        if not first_line.startswith(ctype + ':'):
            return f"{ctype}: {first_line}"
        return first_line
    
    def _stratified_sample_for_human_eval(self, sample_info: List[dict], 
                                          sample_size: int) -> List[dict]:
        """Sample for human evaluation ensuring stratification."""
        import random
        
        # Group by type and complexity
        groups = {}
        for info in sample_info:
            key = (info['sample'].commit_type.value, info['sample'].complexity.value)
            if key not in groups:
                groups[key] = []
            groups[key].append(info)
        
        # Sample from each group proportionally
        samples = []
        for group_samples in groups.values():
            group_size = max(1, int(len(group_samples) / len(sample_info) * sample_size))
            samples.extend(random.sample(group_samples, min(group_size, len(group_samples))))
        
        # If we don't have enough, add more from any group
        while len(samples) < sample_size:
            extra = random.sample(sample_info, min(5, sample_size - len(samples)))
            samples.extend([s for s in extra if s not in samples])
        
        return samples[:sample_size]
    
    def _print_summary(self, strat_report, metric_scores, error_taxonomy):
        """Print evaluation summary."""
        analyzer = MetricsAnalyzer()
        summary = analyzer.summarize(metric_scores)
        error_report = error_taxonomy.generate_report()
        
        print("\n" + "="*60)
        print("EVALUATION RESULTS SUMMARY")
        print("="*60)
        
        print("\nTEST SET:")
        print(f"  Total test samples: {strat_report.get('total_samples', 'N/A')}")
        
        print("\nAVERAGE METRICS:")
        print(f"  BLEU: {summary['bleu']['mean']:.3f}")
        print(f"  ROUGE-1: {summary['rouge1']['mean']:.3f}")
        print(f"  ROUGE-2: {summary['rouge2']['mean']:.3f}")
        print(f"  ROUGE-L: {summary['rougeL']['mean']:.3f}")
        print(f"  BERTScore: {summary['bertscore']['mean']:.3f}")
        print(f"  Overall: {summary['average']['mean']:.3f}")
        
        print("\nQUALITY ANALYSIS:")
        print(f"  Messages with errors: {error_report['messages_with_errors']}")
        print(f"  Usable messages: {error_report['usable_messages']} ({error_report['usable_percentage']:.1f}%)")
        
        print("\nERROR CATEGORIES:")
        for category, count in error_report['errors_by_category'].items():
            print(f"  {category}: {count}")
        
        print("\n" + "="*60)
        print("Results saved to:", self.config.output_dir)
        print("="*60 + "\n")


def main():
    """Run evaluation pipeline."""
    import sys
    
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Configuration
    config = EvaluationConfig(
        dataset_path=Path("evaluation/data/raw_dataset/commits.json"),
        test_set_size=50,  # Start small for testing
        human_eval_sample_size=10,
        device="cpu"  # Change to "cuda" if available
    )
    
    # Run pipeline
    pipeline = EvaluationPipeline(config)
    
    try:
        results = pipeline.run_full_pipeline()
        print("\n✓ Evaluation pipeline completed successfully!")
        return 0
    except Exception as e:
        logger.error(f"Pipeline failed: {e}", exc_info=True)
        return 1


if __name__ == "__main__":
    import sys
    sys.exit(main())
