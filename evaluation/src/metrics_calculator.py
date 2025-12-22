"""
Metrics Calculator

Computes BLEU, ROUGE, and BERTScore for generated vs reference commit messages.

Metrics:
- BLEU: Precision-based metric, good for exact match detection
- ROUGE: Recall-based metric, sensitive to content overlap
- BERTScore: Semantic similarity using contextual embeddings (most reliable for short texts)

All metrics produce scores in [0, 1] where 1 = perfect match.
"""

import logging
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass, asdict
import json
from pathlib import Path

import nltk
from nltk.translate.bleu_score import sentence_bleu, SmoothingFunction
from rouge_score import rouge_scorer
from bert_score import score as bert_score_fn

logger = logging.getLogger(__name__)

# Download required NLTK data
try:
    nltk.data.find('tokenizers/punkt')
except LookupError:
    nltk.download('punkt')


@dataclass
class MetricScores:
    """Container for all metric scores for a single message pair."""
    commit_hash: str
    generated_message: str
    reference_message: str
    
    bleu: float              # 0-1
    rouge1: float            # 0-1 (1-gram F1)
    rouge2: float            # 0-1 (2-gram F1)
    rougeL: float            # 0-1 (longest common subsequence)
    bertscore: float         # 0-1
    
    def average_score(self) -> float:
        """Compute average of all metrics."""
        scores = [self.bleu, self.rouge1, self.rouge2, self.rougeL, self.bertscore]
        return sum(scores) / len(scores)
    
    def to_dict(self) -> Dict:
        """Convert to dictionary."""
        return asdict(self)


class MetricsCalculator:
    """
    Calculates multiple metrics for commit message evaluation.
    
    Handles:
    - Tokenization and preprocessing
    - Batching for BERTScore efficiency
    - Error handling for edge cases
    """
    
    def __init__(self, model_name: str = "microsoft/deberta-xlarge-mnli", device: str = "cpu"):
        """
        Initialize calculator.
        
        Args:
            model_name: HuggingFace model for BERTScore
            device: Device for BERTScore ("cpu" or "cuda")
        """
        self.model_name = model_name
        self.device = device
        self.rouge_scorer = rouge_scorer.RougeScorer(
            ['rouge1', 'rouge2', 'rougeL'],
            use_stemmer=True
        )
        self.smoothing_fn = SmoothingFunction().method1
    
    def compute_all(self, 
                   commit_hash: str,
                   generated: str, 
                   reference: str) -> MetricScores:
        """
        Compute all metrics for a message pair.
        
        Args:
            commit_hash: Commit identifier
            generated: AI-generated message
            reference: Human-written reference message
            
        Returns:
            MetricScores object with all computed scores
        """
        logger.debug(f"Computing metrics for {commit_hash}")
        
        bleu = self._compute_bleu(generated, reference)
        rouge_scores = self._compute_rouge(generated, reference)
        bertscore = self._compute_bertscore(generated, reference)
        
        return MetricScores(
            commit_hash=commit_hash,
            generated_message=generated,
            reference_message=reference,
            bleu=bleu,
            rouge1=rouge_scores['rouge1'],
            rouge2=rouge_scores['rouge2'],
            rougeL=rouge_scores['rougeL'],
            bertscore=bertscore
        )
    
    def compute_batch(self, 
                     pairs: List[Tuple[str, str, str]]) -> List[MetricScores]:
        """
        Compute metrics for multiple message pairs.
        
        More efficient for BERTScore due to batching.
        
        Args:
            pairs: List of (commit_hash, generated, reference) tuples
            
        Returns:
            List of MetricScores
        """
        logger.info(f"Computing metrics for {len(pairs)} pairs")
        
        results = []
        
        # Compute BLEU and ROUGE individually
        for commit_hash, generated, reference in pairs:
            bleu = self._compute_bleu(generated, reference)
            rouge_scores = self._compute_rouge(generated, reference)
            
            results.append({
                'commit_hash': commit_hash,
                'generated': generated,
                'reference': reference,
                'bleu': bleu,
                'rouge1': rouge_scores['rouge1'],
                'rouge2': rouge_scores['rouge2'],
                'rougeL': rouge_scores['rougeL'],
                'bertscore': None  # Will compute in batch
            })
        
        # Batch compute BERTScore
        if pairs:
            generated_list = [p[1] for p in pairs]
            reference_list = [p[2] for p in pairs]
            
            try:
                bert_scores = self._compute_bertscore_batch(generated_list, reference_list)
                for i, bert_score in enumerate(bert_scores):
                    results[i]['bertscore'] = bert_score
            except Exception as e:
                logger.error(f"BERTScore computation failed: {e}. Using 0 as fallback.")
                for i in range(len(results)):
                    results[i]['bertscore'] = 0.0
        
        # Convert to MetricScores objects
        metric_scores = []
        for r in results:
            if r['bertscore'] is not None:
                metric_scores.append(MetricScores(
                    commit_hash=r['commit_hash'],
                    generated_message=r['generated'],
                    reference_message=r['reference'],
                    bleu=r['bleu'],
                    rouge1=r['rouge1'],
                    rouge2=r['rouge2'],
                    rougeL=r['rougeL'],
                    bertscore=r['bertscore']
                ))
        
        logger.info(f"Computed metrics for {len(metric_scores)} pairs")
        return metric_scores
    
    def _compute_bleu(self, generated: str, reference: str) -> float:
        """
        Compute BLEU score.
        
        BLEU measures n-gram overlap between generated and reference.
        Uses 1-2 grams with smoothing.
        """
        try:
            # Tokenize
            ref_tokens = nltk.word_tokenize(reference.lower())
            gen_tokens = nltk.word_tokenize(generated.lower())
            
            # Compute BLEU with 1-2 grams
            weights = (0.5, 0.5)  # Equal weight to 1-gram and 2-gram
            bleu = sentence_bleu(
                [ref_tokens],
                gen_tokens,
                weights=weights,
                smoothing_function=self.smoothing_fn
            )
            
            return float(bleu)
        except Exception as e:
            logger.warning(f"BLEU computation failed: {e}")
            return 0.0
    
    def _compute_rouge(self, generated: str, reference: str) -> Dict[str, float]:
        """
        Compute ROUGE scores (1, 2, L).
        
        ROUGE measures n-gram and LCS overlap.
        Returns F1 scores (harmonic mean of precision and recall).
        """
        try:
            scores = self.rouge_scorer.score(reference, generated)
            
            return {
                'rouge1': scores['rouge1'].fmeasure,
                'rouge2': scores['rouge2'].fmeasure,
                'rougeL': scores['rougeL'].fmeasure,
            }
        except Exception as e:
            logger.warning(f"ROUGE computation failed: {e}")
            return {'rouge1': 0.0, 'rouge2': 0.0, 'rougeL': 0.0}
    
    def _compute_bertscore(self, generated: str, reference: str) -> float:
        """
        Compute BERTScore (semantic similarity).
        
        BERTScore uses contextual embeddings to measure semantic similarity.
        More reliable than BLEU/ROUGE for short, paraphrased texts.
        
        Returns the F1 score.
        """
        try:
            # Compute BERTScore (F1)
            _, _, f1_scores = bert_score_fn(
                [generated],
                [reference],
                lang='en',
                model_type=self.model_name,
                device=self.device
            )
            
            return float(f1_scores[0])
        except Exception as e:
            logger.warning(f"BERTScore computation failed: {e}")
            return 0.0
    
    def _compute_bertscore_batch(self, generated_list: List[str], 
                                 reference_list: List[str]) -> List[float]:
        """
        Compute BERTScore for multiple pairs (batched, more efficient).
        
        Returns list of F1 scores.
        """
        try:
            _, _, f1_scores = bert_score_fn(
                generated_list,
                reference_list,
                lang='en',
                model_type=self.model_name,
                device=self.device,
                batch_size=32
            )
            
            return [float(score) for score in f1_scores]
        except Exception as e:
            logger.warning(f"BERTScore batch computation failed: {e}")
            return [0.0] * len(generated_list)


class MetricsAnalyzer:
    """Analyzes computed metrics across samples."""
    
    @staticmethod
    def summarize(metric_scores: List[MetricScores]) -> Dict:
        """
        Compute summary statistics across all scores.
        
        Returns:
            Dict with mean, median, min, max for each metric
        """
        if not metric_scores:
            return {}
        
        metrics = {
            'bleu': [m.bleu for m in metric_scores],
            'rouge1': [m.rouge1 for m in metric_scores],
            'rouge2': [m.rouge2 for m in metric_scores],
            'rougeL': [m.rougeL for m in metric_scores],
            'bertscore': [m.bertscore for m in metric_scores],
            'average': [m.average_score() for m in metric_scores],
        }
        
        summary = {}
        for metric_name, values in metrics.items():
            summary[metric_name] = {
                'mean': float(sum(values) / len(values)),
                'median': float(sorted(values)[len(values) // 2]),
                'min': float(min(values)),
                'max': float(max(values)),
                'stdev': self._stdev(values)
            }
        
        return summary
    
    @staticmethod
    def summarize_by_group(metric_scores: List[MetricScores], 
                          grouping_fn) -> Dict[str, Dict]:
        """
        Compute summary statistics grouped by a criteria.
        
        Args:
            grouping_fn: Function that takes MetricScores and returns group key
            
        Returns:
            Dict[group_key] = summary statistics
        """
        groups = {}
        for score in metric_scores:
            group_key = grouping_fn(score)
            if group_key not in groups:
                groups[group_key] = []
            groups[group_key].append(score)
        
        return {
            group_key: MetricsAnalyzer.summarize(scores)
            for group_key, scores in groups.items()
        }
    
    @staticmethod
    def _stdev(values: List[float]) -> float:
        """Compute standard deviation."""
        if len(values) < 2:
            return 0.0
        mean = sum(values) / len(values)
        variance = sum((v - mean) ** 2 for v in values) / len(values)
        return variance ** 0.5


def save_metrics(metric_scores: List[MetricScores], output_file: Path):
    """Save computed metrics to JSON."""
    output_file = Path(output_file)
    output_file.parent.mkdir(parents=True, exist_ok=True)
    
    # Compute summary
    analyzer = MetricsAnalyzer()
    summary = analyzer.summarize(metric_scores)
    
    # Save
    data = {
        'total': len(metric_scores),
        'summary': summary,
        'individual_scores': [m.to_dict() for m in metric_scores]
    }
    
    with open(output_file, 'w') as f:
        json.dump(data, f, indent=2)
    
    logger.info(f"Saved metrics to {output_file}")


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    
    # Example
    calc = MetricsCalculator(device="cpu")
    
    test_pairs = [
        ("abc123", "fix: resolve null pointer exception in auth module", 
                   "fix: handle null reference in authentication"),
        ("def456", "feat: add user profile page with avatar support",
                   "feat: implement user profile UI component"),
    ]
    
    results = calc.compute_batch(test_pairs)
    
    for r in results:
        print(f"\n{r.commit_hash}:")
        print(f"  BLEU: {r.bleu:.3f}")
        print(f"  ROUGE-1: {r.rouge1:.3f}")
        print(f"  ROUGE-2: {r.rouge2:.3f}")
        print(f"  ROUGE-L: {r.rougeL:.3f}")
        print(f"  BERTScore: {r.bertscore:.3f}")
        print(f"  Average: {r.average_score():.3f}")
