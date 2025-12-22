# Evaluation Framework - Complete Implementation Guide

This guide walks you through the entire evaluation plan implementation for your commit message generation system.

## Overview

Your evaluation framework consists of **4 phases**:

1. **Test Case Preparation** - Extract and stratify commit samples
2. **Automated Evaluation** - Calculate metrics (BLEU, ROUGE, BERTScore)
3. **Error Analysis** - Categorize failures and quality issues
4. **Human Evaluation** - Collect developer feedback on samples

---

## Phase 1: Test Case Preparation

### Step 1.1: Prepare Your Dataset

You need a **Kaggle dataset** in JSON format with commits. Expected structure:

```json
[
  {
    "commit_hash": "abc123def456",
    "message": "fix: resolve null pointer exception",
    "diff": "diff --git a/src/auth.py b/src/auth.py\n...",
    "timestamp": "2023-01-15T10:30:00Z"
  },
  ...
]
```

**Where to get data:**
- Kaggle Datasets: Search for "git commits", "github commits", or "linux kernel commits"
- Popular options:
  - [Open Source Commits Dataset](https://www.kaggle.com/datasets)
  - [GitHub Events Dataset](https://www.kaggle.com/datasets)
  - Any GitHub repository with commit history

**How to prepare:**
1. Download the dataset (or extract from a Git repo using `git log`)
2. Place in: `evaluation/data/raw_dataset/commits.json`

### Step 1.2: Extract Commits

Run the dataset extractor to classify commits by type and complexity:

```bash
# From evaluation directory
python -m src.dataset_extractor
```

This will:
- Extract all commits from the JSON
- Classify by type (fix, feat, refactor, etc.)
- Classify by complexity (small, medium, large)
- Save to: `evaluation/data/extracted/extracted_commits.json`

**Output includes:**
- Total commit count
- Distribution by type
- Distribution by complexity

### Step 1.3: Build Stratified Test Set

Create a balanced test set with representation across all dimensions:

```bash
python -m src.test_set_builder
```

This will:
- Load extracted commits
- Ensure representation from each type and complexity level
- Create test set of 200 commits (configurable)
- Save to: `evaluation/data/test_set/test_samples.json`
- Generate stratification report: `evaluation/data/test_set/stratification_report.txt`

**Why stratification matters:**
- Ensures no bias toward simple/easy commits
- Provides fair assessment across all code change types
- Enables per-type and per-complexity analysis

**Example output:**
```
DISTRIBUTION BY TYPE
fix            | Test: 30  | All: 450  | Coverage: 6.7%
feat           | Test: 25  | All: 350  | Coverage: 7.1%
refactor       | Test: 20  | All: 200  | Coverage: 10.0%
...

DISTRIBUTION BY COMPLEXITY
small          | Test: 80  | All: 1200 | Coverage: 6.7%
medium         | Test: 70  | All: 800  | Coverage: 8.8%
large          | Test: 50  | All: 300  | Coverage: 16.7%
```

---

## Phase 2: Automated Evaluation

### Step 2.1: Generate Commit Messages

For each test sample, **generate a commit message using your pipeline**:

```python
from src.pipeline import CommitPipeline
from src.state import PipelineState

# Load a test sample
sample = test_samples[0]  # CommitSample object

# Run your pipeline
pipeline = CommitPipeline()
state = PipelineState(staged_diff=sample.diff)
final_message = pipeline.run(state)

# Store: (commit_hash, generated_message, reference_message)
```

**Or modify `evaluator.py`'s `_generate_baseline_message()` to integrate your pipeline:**

```python
def _generate_baseline_message(self, sample: CommitSample) -> str:
    """Generate a commit message using your pipeline."""
    from src.pipeline import CommitPipeline
    
    pipeline = CommitPipeline()
    state = PipelineState(staged_diff=sample.diff)
    result = pipeline.run(state)
    return result.commit_message
```

### Step 2.2: Calculate Metrics

Compute BLEU, ROUGE, and BERTScore for all generated messages:

```bash
# This happens automatically in the evaluation pipeline, but you can run manually:
python -c "
from evaluation.src.metrics_calculator import MetricsCalculator

calc = MetricsCalculator(device='cpu')

# For each generated vs reference pair
scores = calc.compute_all(
    commit_hash='abc123',
    generated='fix: resolve null pointer',
    reference='fix: handle null reference in auth'
)

print(f'BLEU: {scores.bleu:.3f}')
print(f'ROUGE-1: {scores.rouge1:.3f}')
print(f'BERTScore: {scores.bertscore:.3f}')
"
```

**Understand the metrics:**

| Metric | Range | What It Measures | Best For |
|--------|-------|------------------|----------|
| **BLEU** | 0-1 | N-gram precision overlap | Exact phrase matching |
| **ROUGE-1** | 0-1 | 1-gram recall overlap | Word-level coverage |
| **ROUGE-2** | 0-1 | 2-gram recall overlap | Phrase coverage |
| **ROUGE-L** | 0-1 | Longest common subsequence | Sequence preservation |
| **BERTScore** | 0-1 | Semantic similarity (embeddings) | **Most important** for short texts |

**Key insight:** BERTScore is most reliable for commit messages because:
- BLEU/ROUGE penalize paraphrasing (e.g., "fix null pointer" vs "resolve null reference")
- BERTScore understands semantic equivalence
- Commit messages are short (BLEU/ROUGE less effective on short texts)

### Step 2.3: Generate Reports

The framework automatically produces:
- `automated_metrics.json` - All metric scores
- Summary statistics (mean, min, max, stdev for each metric)
- Per-type and per-complexity breakdowns

**Example output:**
```
AVERAGE METRICS:
  BLEU: 0.425
  ROUGE-1: 0.612
  ROUGE-2: 0.381
  ROUGE-L: 0.543
  BERTScore: 0.738
  Overall: 0.540
```

---

## Phase 3: Error Analysis

### Step 3.1: Error Detection

The framework automatically detects errors in generated messages:

```python
from evaluation.src.error_taxonomy import ErrorDetector

detector = ErrorDetector()

assessment = detector.assess(
    commit_hash='abc123',
    generated='fix: update code',  # Too generic!
    reference='fix: resolve null pointer in auth module',
    diff='diff output...'
)

print(f"Quality: {assessment.quality_score:.2f}")
print(f"Errors: {len(assessment.errors)}")
for error in assessment.errors:
    print(f"  - [{error.category.value}] {error.description}")
```

### Step 3.2: Error Categories

The framework detects 8 error types:

1. **Missing Key Change** - Omits important code change from reference
2. **Too Generic** - Vague, non-descriptive message
3. **Hallucinated/Incorrect** - Claims changes not in the diff
4. **Wrong Commit Type** - Incorrect classification (feat vs fix, etc.)
5. **Format Violation** - Breaks conventional commit format
6. **Incomplete** - Truncated or unfinished message
7. **Out of Scope** - Describes changes not in diff
8. **Semantic Mismatch** - Technically correct but misleading

Each error has a **severity level**:
- **CRITICAL** (0.5 deduction) - Message is unusable
- **HIGH** (0.2 deduction) - Significant issues
- **MEDIUM** (0.1 deduction) - Moderate issues
- **LOW** (0.05 deduction) - Minor issues

### Step 3.3: Quality Scoring

Each message gets a quality score (0-1):

```
Quality = 1.0 - Σ(severity_deduction)

Examples:
- No errors → 1.0 (perfect)
- 1 HIGH error → 0.8 (good)
- 1 CRITICAL + 1 HIGH → 0.3 (poor)
```

A message is **usable in production** if it has no CRITICAL errors.

### Step 3.4: Error Report

The framework generates:
- `error_taxonomy.json` - All assessments and error details
- Summary report showing:
  - % of messages with errors
  - % of usable messages
  - Most common error types
  - Quality score distribution

**Example output:**
```
Total assessed: 200
Messages with errors: 45 (22.5%)
Usable messages: 185 (92.5%)
Most common error: too_generic (18 occurrences)

Error distribution:
  missing_key_change: 12
  too_generic: 18
  wrong_type: 8
  format_violation: 7
```

---

## Phase 4: Human Evaluation

### Step 4.1: Sample Selection

The framework samples 50-100 commits for human review, stratified across:
- Commit types (fix, feat, refactor, etc.)
- Complexity levels (small, medium, large)

```bash
# Automatically prepared by evaluator.py
# See: evaluation/data/results/human_eval_samples.json
```

### Step 4.2: Run Interactive Evaluation

Launch the CLI evaluation interface:

```bash
python -m evaluation.src.human_eval_interface
```

**Interactive session flow:**
1. Enter your name as evaluator
2. For each sample, you see:
   - Original diff (first 500 chars)
   - Generated message
   - Reference message
3. Rate on 3 dimensions (1-5 scale):
   - **Readability**: How easy to understand?
   - **Completeness**: Does it capture all changes?
   - **Suitability**: Would you use in actual Git?
4. Optional: Add feedback and suggestions

### Step 4.3: Multiple Evaluators

For better reliability, have **multiple developers** evaluate the same samples:

```bash
# Evaluator 1
python -m evaluation.src.human_eval_interface
# Enter name: "Alice"
# Evaluate samples...

# Evaluator 2
python -m evaluation.src.human_eval_interface
# Enter name: "Bob"
# Evaluate same samples...
```

The framework aggregates ratings and computes inter-rater agreement.

### Step 4.4: Collect Results

Results are saved to:
- `human_evaluations.json` - Structured evaluation data
- `human_evaluation_report.txt` - Human-readable summary

**Example output:**
```
SUMMARY STATISTICS
Average Readability: 4.2/5
Average Completeness: 3.8/5
Average Suitability: 4.0/5
Overall Average: 4.0/5

Sample abc123:
  Type: fix, Complexity: small
  Generated: fix: resolve null pointer
  Reference: fix: handle null reference in auth
  
  Ratings (from 2 evaluators):
    Readability: 4.5/5
    Completeness: 4.0/5
    Suitability: 4.5/5
```

---

## Running the Complete Pipeline

### Quick Start

```bash
# Install dependencies
pip install -r evaluation/requirements.txt

# Run full evaluation (from project root)
python -m evaluation.src.evaluator
```

### Configuration

Edit `evaluator.py` to customize:

```python
config = EvaluationConfig(
    dataset_path=Path("evaluation/data/raw_dataset/commits.json"),
    test_set_size=200,           # Number of test samples
    min_per_type=5,              # Min samples per commit type
    min_per_complexity=10,       # Min samples per complexity level
    bert_model="microsoft/deberta-xlarge-mnli",
    device="cpu",                # or "cuda" for GPU
    human_eval_sample_size=50,   # Number for human review
)

pipeline = EvaluationPipeline(config)
results = pipeline.run_full_pipeline()
```

### Output Directory Structure

After running the pipeline:

```
evaluation/data/results/
├── extracted_commits.json              # All extracted commits
├── test_samples.json                   # Stratified test set
├── stratification_report.json          # Stratification details
├── stratification_report.txt           # Human-readable report
├── automated_metrics.json              # BLEU, ROUGE, BERTScore
├── error_taxonomy.json                 # Error assessments
├── human_eval_samples.json             # Sampled for human review
├── human_evaluations.json              # Human ratings
└── human_evaluation_report.txt         # Human review summary
```

---

## Analysis and Visualization

### Using Pandas/Jupyter

```python
import json
import pandas as pd
from pathlib import Path

# Load metrics
with open('evaluation/data/results/automated_metrics.json') as f:
    metrics = json.load(f)

# Convert to DataFrame
df = pd.DataFrame(metrics['individual_scores'])

# Analyze by commit type
by_type = df.groupby('commit_type').agg({
    'bleu': ['mean', 'std'],
    'rouge1': ['mean', 'std'],
    'bertscore': ['mean', 'std']
})

# Analyze by complexity
by_complexity = df.groupby('complexity').agg({
    'bleu': ['mean', 'std'],
    'bertscore': ['mean', 'std']
})

print(by_type)
print(by_complexity)
```

### Key Metrics to Track

1. **Overall Quality**: BERTScore mean (most important)
2. **Per-Type Variance**: Which types are harder to generate?
3. **Per-Complexity Variance**: How does size affect quality?
4. **Error Rate**: % of messages with critical errors
5. **Human Agreement**: Do evaluators agree? (If multiple)
6. **Gap Analysis**: Generated vs reference ratings

---

## Interpretation Guide

### Interpreting Automated Metrics

```
BERTScore 0.85+     → Excellent semantic similarity
BERTScore 0.70-0.85 → Good, mostly useful
BERTScore 0.50-0.70 → Acceptable but needs work
BERTScore 0.30-0.50 → Poor, significant issues
BERTScore < 0.30    → Unusable
```

### Interpreting Human Ratings

```
4.0-5.0  → Production ready
3.0-3.9  → Acceptable with minor fixes
2.0-2.9  → Needs significant improvement
1.0-1.9  → Unusable
```

### Red Flags

- **High BLEU but low BERTScore**: Generator uses exact phrases but wrong context
- **Low score for "small" commits**: Model may work better on larger changes
- **Specific error type dominates**: Focus improvements there
- **Human ratings < 3.0**: Fundamental issues with generation approach

---

## Next Steps

After completing evaluation:

1. **Identify Issues**: Which error types are most common?
2. **Prioritize Fixes**: Focus on high-impact improvements
3. **Retrain/Adjust**: Improve the generation pipeline
4. **Re-evaluate**: Run assessment again to measure improvement
5. **Iterate**: Repeat until metrics reach target

### Example Improvement Areas

If top error is "too_generic":
- Add more specific training examples
- Improve diff summarization
- Use extracted change descriptions

If low BERTScore despite low errors:
- Check model understanding of technical terms
- Improve context passing to LLM
- Use better prompting

---

## Troubleshooting

### "No commits extracted"
- Check `evaluation/data/raw_dataset/commits.json` exists
- Verify JSON format matches expected schema
- Ensure file contains valid commit data

### BERTScore computation slow
- Set `device="cuda"` if GPU available
- Reduce batch size (edit in `metrics_calculator.py`)
- Run on smaller test set first

### Module import errors
- Run `pip install -e .` from project root
- Ensure all evaluation dependencies installed: `pip install -r evaluation/requirements.txt`

### Human evaluation not saving
- Check `evaluation/data/results/` directory exists
- Verify write permissions
- Check disk space

---

## References

- [Conventional Commits](https://www.conventionalcommits.org/)
- [BLEU Score](https://en.wikipedia.org/wiki/BLEU)
- [ROUGE Metrics](https://en.wikipedia.org/wiki/ROUGE_(metric))
- [BERTScore Paper](https://arxiv.org/abs/1904.09675)
- [Evaluation Best Practices](https://github.com/nlg-eval/nlg-eval)

---

## Summary

You now have a complete evaluation framework that:

✅ **Extracts** commits from Kaggle datasets  
✅ **Stratifies** samples across all dimensions  
✅ **Calculates** 5 quality metrics  
✅ **Detects** 8 types of errors  
✅ **Samples** for human review  
✅ **Collects** developer feedback  
✅ **Generates** comprehensive reports  

Use this to systematically evaluate and improve your commit message generation system!
