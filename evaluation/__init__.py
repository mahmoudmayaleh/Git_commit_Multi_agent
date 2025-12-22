"""
Evaluation Framework

Complete evaluation system for AI-generated commit messages.

Modules:
- dataset_extractor: Extract diffs from Kaggle dataset
- test_set_builder: Build stratified test sets
- metrics_calculator: Compute BLEU, ROUGE, BERTScore
- error_taxonomy: Categorize and analyze errors
- human_eval_interface: Collect human evaluations
- evaluator: Main orchestration pipeline
"""

from evaluation.src.dataset_extractor import (
    DatasetExtractor,
    CommitSample,
    CommitType,
    DiffComplexity,
    CommitClassifier,
)

from evaluation.src.test_set_builder import (
    TestSetBuilder,
    StratificationConfig,
)

from evaluation.src.metrics_calculator import (
    MetricsCalculator,
    MetricsAnalyzer,
    MetricScores,
    save_metrics,
)

from evaluation.src.error_taxonomy import (
    ErrorTaxonomy,
    ErrorDetector,
    ErrorAnnotation,
    MessageQualityAssessment,
    ErrorCategory,
    SeverityLevel,
)

from evaluation.src.human_eval_interface import (
    HumanEvaluationInterface,
    CLIEvaluator,
    HumanEvaluation,
    EvaluationSummary,
    EvaluationConfig,
)

from evaluation.src.evaluator import (
    EvaluationPipeline,
    EvaluationConfig as PipelineConfig,
)

__all__ = [
    # Dataset
    "DatasetExtractor",
    "CommitSample",
    "CommitType",
    "DiffComplexity",
    "CommitClassifier",
    
    # Test Set
    "TestSetBuilder",
    "StratificationConfig",
    
    # Metrics
    "MetricsCalculator",
    "MetricsAnalyzer",
    "MetricScores",
    "save_metrics",
    
    # Error Analysis
    "ErrorTaxonomy",
    "ErrorDetector",
    "ErrorAnnotation",
    "MessageQualityAssessment",
    "ErrorCategory",
    "SeverityLevel",
    
    # Human Evaluation
    "HumanEvaluationInterface",
    "CLIEvaluator",
    "HumanEvaluation",
    "EvaluationSummary",
    "EvaluationConfig",
    
    # Pipeline
    "EvaluationPipeline",
    "PipelineConfig",
]

__version__ = "0.1.0"
