#!/usr/bin/env python
"""
Quick Start Script for Evaluation Framework

Run this to understand the evaluation pipeline and see examples of each phase.

Usage:
    python evaluation_quickstart.py --phase all        # Run all phases
    python evaluation_quickstart.py --phase 1          # Run phase 1 only
    python evaluation_quickstart.py --help             # Show options
"""

import argparse
import logging
import json
from pathlib import Path
from typing import Optional

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def demo_phase_1():
    """Demonstrate Phase 1: Test Case Preparation."""
    print("\n" + "="*80)
    print("PHASE 1: TEST CASE PREPARATION")
    print("="*80)
    
    print("""
This phase extracts commits from a Kaggle dataset and creates a stratified test set.

What it does:
1. Loads commits from evaluation/data/raw_dataset/commits.json
2. Classifies each by type (fix, feat, refactor, etc.)
3. Classifies each by complexity (small, medium, large)
4. Selects a balanced test set ensuring representation across all types/complexities

To run Phase 1:
    python -m evaluation.src.dataset_extractor
    python -m evaluation.src.test_set_builder

Expected outputs:
    evaluation/data/extracted/extracted_commits.json
    evaluation/data/test_set/test_samples.json
    evaluation/data/test_set/stratification_report.txt

Key insight:
    Stratification ensures evaluation results aren't biased toward simple/easy commits.
    You get a fair assessment across all code change types.
""")
    
    print("\nExample: Extracting and stratifying 1000 commits...")
    print("-" * 80)
    print("""
Total commits extracted: 1000

By Type:
  fix:      450 (45%)
  feat:     350 (35%)
  refactor: 200 (20%)

By Complexity:
  small:  600 (60%)
  medium: 300 (30%)
  large:  100 (10%)

Test Set: 200 samples (20% of total)

Coverage by Type:
  fix:      30 (6.7% of 450)
  feat:     25 (7.1% of 350)
  refactor: 20 (10.0% of 200)
  
Coverage by Complexity:
  small:  80 (13.3%)
  medium: 70 (23.3%)
  large:  50 (50.0%)  ← Large commits oversampled to ensure diversity
""")


def demo_phase_2():
    """Demonstrate Phase 2: Automated Evaluation."""
    print("\n" + "="*80)
    print("PHASE 2: AUTOMATED EVALUATION")
    print("="*80)
    
    print("""
This phase generates commit messages and calculates quality metrics.

What it does:
1. For each test sample, runs your commit generation pipeline
2. Compares generated message with human-written reference
3. Calculates BLEU, ROUGE, and BERTScore
4. Generates stratified analysis by type and complexity

Key metrics:
    BLEU        - N-gram precision (good for exact matches)
    ROUGE-1     - Unigram recall (word-level coverage)
    ROUGE-2     - Bigram recall (phrase coverage)
    ROUGE-L     - Longest common subsequence
    BERTScore   - Semantic similarity using embeddings (MOST IMPORTANT)

Why BERTScore matters:
    For short texts like commit messages, BLEU and ROUGE are unreliable because:
    - "fix null pointer" vs "resolve null reference" → Different BLEU, same meaning
    - BERTScore understands semantic equivalence through contextual embeddings
    - This makes BERTScore the most reliable metric for your use case

To integrate your pipeline:
    Edit evaluator.py, _generate_baseline_message() method
    Call your CommitPipeline there
    
Expected outputs:
    evaluation/data/results/automated_metrics.json
    Individual scores for all 200 test samples + summary statistics
""")
    
    print("\nExample: Evaluating 200 test samples...")
    print("-" * 80)
    print("""
Sample Results:

Commit: abc123def456
Generated: "fix: resolve null pointer exception in auth module"
Reference: "fix: handle null reference in authentication"
Metrics:
  BLEU:       0.45  (moderate n-gram overlap)
  ROUGE-1:    0.62  (good word coverage)
  ROUGE-2:    0.38  (moderate phrase coverage)
  ROUGE-L:    0.54  (good sequence overlap)
  BERTScore:  0.82  (excellent semantic similarity!)
  Average:    0.56

---

SUMMARY STATISTICS (across all 200 samples):

BLEU:       mean=0.42, min=0.08, max=0.91, stdev=0.18
ROUGE-1:    mean=0.61, min=0.20, max=0.95, stdev=0.16
ROUGE-2:    mean=0.37, min=0.00, max=0.88, stdev=0.19
ROUGE-L:    mean=0.52, min=0.15, max=0.93, stdev=0.17
BERTScore:  mean=0.74, min=0.31, max=0.98, stdev=0.14
Overall:    mean=0.53, min=0.17, max=0.93, stdev=0.15

---

BY COMMIT TYPE:

fix (30 samples):
  BERTScore: mean=0.71, stdev=0.15
feat (25 samples):
  BERTScore: mean=0.76, stdev=0.13
refactor (20 samples):
  BERTScore: mean=0.79, stdev=0.11

Insight: Refactoring messages are easier to generate!
Fix messages are harder (more variable error conditions)

---

BY COMPLEXITY:

small (80 samples):
  BERTScore: mean=0.78, stdev=0.12
medium (70 samples):
  BERTScore: mean=0.74, stdev=0.13
large (50 samples):
  BERTScore: mean=0.68, stdev=0.16

Insight: Your model performs better on small, focused changes
Struggles with large, multi-file refactorings
""")


def demo_phase_3():
    """Demonstrate Phase 3: Error Analysis."""
    print("\n" + "="*80)
    print("PHASE 3: ERROR ANALYSIS")
    print("="*80)
    
    print("""
This phase automatically detects and categorizes errors.

Error Categories Detected:

1. MISSING_KEY_CHANGE
   When: Generated message omits important changes from reference
   Example: Generated "update config" vs Reference "update database connection string"
   
2. TOO_GENERIC
   When: Message is vague and non-descriptive
   Example: "fix: update code" or "feat: add feature"
   Impact: High - doesn't communicate what changed
   
3. HALLUCINATED_INCORRECT
   When: Message claims changes not present in diff
   Example: Generated mentions function "parse_json()" but diff has no such function
   Impact: Critical - misinformation about code
   
4. WRONG_COMMIT_TYPE
   When: Type classification is incorrect
   Example: Marked as "feat:" but is really a "fix:"
   Impact: High - breaks commit history organization
   
5. FORMAT_VIOLATION
   When: Breaks conventional commit format
   Example: Missing "type:" prefix or improper spacing
   Impact: High - automation/tooling won't recognize
   
6. INCOMPLETE
   When: Message is truncated or cut off
   Example: Message ends with "..." or is suspiciously short
   Impact: High - unusable
   
7. OUT_OF_SCOPE
   When: Describes changes not in the actual diff
   Example: Message describes changes to API but diff is UI-only
   Impact: Critical - complete mismatch
   
8. SEMANTIC_MISMATCH
   When: Technically correct but misleading
   Example: Description doesn't match diff intent
   Impact: Medium - confusing

Severity Levels:
  CRITICAL (0.5 deduction) - Message is unusable
  HIGH     (0.2 deduction) - Significant issues
  MEDIUM   (0.1 deduction) - Moderate issues
  LOW      (0.05 deduction) - Minor issues

Quality Score Calculation:
  Quality = 1.0 - Σ(error_deductions)
  Score < 0 clamped to 0.0
  
  Examples:
  - No errors → 1.0 (perfect)
  - 1 HIGH error → 0.8 (good, usable)
  - 1 CRITICAL error → 0.5 or lower (unusable)

Expected output:
    evaluation/data/results/error_taxonomy.json
    Detailed error assessments for all 200 samples
""")
    
    print("\nExample: Error Analysis on 200 samples...")
    print("-" * 80)
    print("""
SUMMARY:

Total assessed: 200
Messages with errors: 45 (22.5%)
Usable messages: 185 (92.5%)
Average quality score: 0.87/1.0

---

ERRORS BY CATEGORY:

too_generic:              18 occurrences
missing_key_change:       12 occurrences
wrong_commit_type:         8 occurrences
format_violation:          7 occurrences
semantic_mismatch:         5 occurrences
hallucinated_incorrect:    3 occurrences (CRITICAL!)
incomplete:                2 occurrences
out_of_scope:              1 occurrence

---

MOST COMMON: "too_generic" (18 messages)

Examples:
1. Generated: "fix: improve code"
   Reference: "fix: optimize database query performance"
   Issue: Doesn't specify what was improved
   
2. Generated: "feat: add new feature"
   Reference: "feat: implement user authentication with OAuth2"
   Issue: Completely vague

Recommendation:
  → Improve diff summarization in SummaryAgent
  → Add specific change extraction before CommitWriterAgent

---

CRITICAL ERRORS: "hallucinated_incorrect" (3 messages)

Example:
  Generated: "fix: update API endpoints for legacy protocol"
  Diff: Contains only UI component changes
  Issue: Generator invented changes not in diff
  
Recommendation:
  → Validate that all entities in message appear in diff
  → Improve LLM prompt to prevent hallucinations

---

ERROR DISTRIBUTION BY COMMIT TYPE:

fix:
  too_generic: 10
  missing_key_change: 6
  wrong_type: 2
  
feat:
  too_generic: 5
  wrong_type: 4
  missing_key_change: 3
  
refactor:
  missing_key_change: 3
  semantic_mismatch: 2
  format_violation: 2

Insight: Fix messages are most problematic
→ Different error patterns per type
→ May need type-specific improvements

---

ERROR DISTRIBUTION BY COMPLEXITY:

small:
  Average errors per message: 0.18
  Usable rate: 98%
  
medium:
  Average errors per message: 0.24
  Usable rate: 92%
  
large:
  Average errors per message: 0.38
  Usable rate: 78%

Insight: Larger changes have more issues
→ Complex changes need better handling
→ May need larger context windows for LLM
""")


def demo_phase_4():
    """Demonstrate Phase 4: Human Evaluation."""
    print("\n" + "="*80)
    print("PHASE 4: HUMAN EVALUATION")
    print("="*80)
    
    print("""
This phase collects developer feedback on sampled messages.

Workflow:
1. Framework samples 50-100 commits stratified across type and complexity
2. Developers review each sample using CLI interface
3. Rate on three dimensions (1-5 scale):
   - Readability: How easy to understand?
   - Completeness: Does it capture all changes?
   - Suitability: Would you use in actual Git workflow?
4. Collect optional feedback and improvement suggestions
5. Aggregate ratings and generate report

Sample Stratification:
The 50 samples are selected to represent:
  - All commit types proportionally
  - All complexity levels proportionally
  - Mixed high/low automated scores (to understand disagreements)

To run human evaluation:
    python -m evaluation.src.human_eval_interface

Expected outputs:
    evaluation/data/results/human_eval_samples.json
    evaluation/data/results/human_evaluations.json
    evaluation/data/results/human_evaluation_report.txt

Tip: Have 2-3 developers evaluate to:
  - Assess inter-rater agreement
  - Reduce individual bias
  - Get more confident scores
""")
    
    print("\nExample: Human evaluation on 50 samples...")
    print("-" * 80)
    print("""
INTERACTIVE SESSION:

Human Evaluation Session - Alice
================================================================================
Total samples to evaluate: 50

────────────────────────────────────────────────────────────────────────────────
Sample 1/50
────────────────────────────────────────────────────────────────────────────────

Commit Hash: abc123def456
Type: fix, Complexity: small

Diff Preview (first 500 chars):
  diff --git a/src/auth.py b/src/auth.py
  --- a/src/auth.py
  +++ b/src/auth.py
  @@ -142,8 +142,12 @@ class AuthManager:
    def verify_token(self, token):
  -    if token is None:
  -        return False
  +    if token is None or len(token) == 0:
  +        logger.warning("Invalid token received")
  +        return False
  +    if not self._is_token_valid(token):
  +        logger.error("Token validation failed")
       return True

Generated Message:
  fix: handle empty token strings in authentication

Reference Message:
  fix: add token validation and logging in verify_token method

Please rate this generated message (1=Poor, 5=Excellent):
Readability (1-5): 4
Completeness (1-5): 3
Suitability for Git workflow (1-5): 4

Optional feedback: Good, but missing the logging addition mentioned in reference
Optional suggestion for improvement: fix: improve token validation with logging

✓ Evaluation recorded

────────────────────────────────────────────────────────────────────────────────
Sample 2/50
[... continue for 50 samples ...]

---

FINAL REPORT:

SUMMARY STATISTICS
Average Readability: 4.2/5
Average Completeness: 3.8/5
Average Suitability: 4.0/5
Overall Average: 4.0/5

INDIVIDUAL EVALUATIONS

Commit: abc123def456
Type: fix, Complexity: small
Generated: fix: handle empty token strings in authentication
Reference: fix: add token validation and logging in verify_token method

Ratings (from 1 evaluator(s)):
  Readability: 4.0/5
  Completeness: 3.0/5
  Suitability: 4.0/5
  Overall: 3.7/5

Evaluator Feedback:
  [Alice]
    Good, but missing the logging addition mentioned in reference
    Suggestion: fix: improve token validation with logging
    Issues: missing_key_change

---

Commit: xyz789abc123
Type: feat, Complexity: medium
Generated: feat: add user authentication system
Reference: feat: implement OAuth2-based user authentication with session management

Ratings (from 1 evaluator(s)):
  Readability: 5.0/5
  Completeness: 2.0/5
  Suitability: 3.0/5
  Overall: 3.3/5

Evaluator Feedback:
  [Alice]
    Very clear message, but misses the session management aspect completely
    Suggestion: feat: implement OAuth2 authentication with session handling
    Issues: missing_key_change, incomplete

---

Correlation Analysis (if multiple evaluators):

Pair-wise agreement (Pearson correlation):
  Alice vs Bob: 0.82 (good agreement)
  Alice vs Charlie: 0.75 (moderate agreement)
  
This indicates consistent evaluation quality
""")


def demo_integration():
    """Show how to integrate everything."""
    print("\n" + "="*80)
    print("INTEGRATION EXAMPLE")
    print("="*80)
    
    print("""
Here's how to run the complete evaluation pipeline:

Step 1: Install dependencies
    pip install -r evaluation/requirements.txt

Step 2: Prepare your dataset
    - Download from Kaggle or extract from Git repo
    - Save as: evaluation/data/raw_dataset/commits.json
    - Format: [{commit_hash, message, diff, ...}, ...]

Step 3: Run the pipeline
    python -m evaluation.src.evaluator

Step 4: Customize (optional)
    Edit evaluator.py, EvaluationConfig class:
    
    config = EvaluationConfig(
        dataset_path=Path("..."),
        test_set_size=200,
        bert_model="microsoft/deberta-xlarge-mnli",
        device="cpu",  # or "cuda"
        human_eval_sample_size=50,
    )

Step 5: Integrate your commit pipeline
    Edit evaluator.py, _generate_baseline_message():
    
    def _generate_baseline_message(self, sample: CommitSample) -> str:
        from src.pipeline import CommitPipeline
        
        pipeline = CommitPipeline()
        state = PipelineState(staged_diff=sample.diff)
        result = pipeline.run(state)
        return result.commit_message

Step 6: Collect human evaluations
    python -m evaluation.src.human_eval_interface
    
    Then run for each evaluator with their name

Step 7: Analyze results
    Review reports in evaluation/data/results/
    
    Key files:
    - automated_metrics.json → BLEU, ROUGE, BERTScore
    - error_taxonomy.json → Error analysis
    - human_evaluations.json → Developer feedback
    - stratification_report.txt → Test set distribution

Step 8: Iterate
    - Identify top error types
    - Improve your pipeline
    - Re-run evaluation
    - Measure improvement
""")


def main():
    """Run demonstrations."""
    parser = argparse.ArgumentParser(
        description="Evaluation Framework Quick Start",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python evaluation_quickstart.py --phase 1
  python evaluation_quickstart.py --phase all
  python evaluation_quickstart.py --show-integration
        """
    )
    
    parser.add_argument(
        '--phase',
        choices=['1', '2', '3', '4', 'all'],
        default='all',
        help='Which phase to demonstrate (default: all)'
    )
    
    parser.add_argument(
        '--show-integration',
        action='store_true',
        help='Show integration instructions'
    )
    
    args = parser.parse_args()
    
    if args.show_integration:
        demo_integration()
        return 0
    
    phases = {
        '1': demo_phase_1,
        '2': demo_phase_2,
        '3': demo_phase_3,
        '4': demo_phase_4,
    }
    
    if args.phase == 'all':
        for phase_fn in phases.values():
            phase_fn()
    else:
        phases[args.phase]()
    
    print("\n" + "="*80)
    print("NEXT STEPS")
    print("="*80)
    print("""
1. Read EVALUATION_GUIDE.md for detailed instructions

2. Prepare your dataset:
   - Download from Kaggle
   - Save to: evaluation/data/raw_dataset/commits.json

3. Install dependencies:
   pip install -r evaluation/requirements.txt

4. Run the pipeline:
   python -m evaluation.src.evaluator

5. Collect human evaluations:
   python -m evaluation.src.human_eval_interface

6. Analyze results in:
   evaluation/data/results/

Questions? See EVALUATION_GUIDE.md or check the source code comments.
""")
    
    return 0


if __name__ == '__main__':
    import sys
    sys.exit(main())
