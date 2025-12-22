"""
Error Taxonomy

Framework for categorizing and analyzing failures and low-quality commit messages.

Error Categories:
1. Missing Key Change - Generated message omits important code change
2. Too Generic - Message is vague and doesn't describe specific changes
3. Hallucinated/Incorrect - Claims changes not present in diff
4. Wrong Commit Type - Incorrect type classification (e.g., feature vs bugfix)
5. Formatting Violation - Breaks conventional commit format
6. Incomplete - Message is truncated or cut off
7. Out of Scope - Describes changes not in the diff
8. Semantic Mismatch - Technically correct but misleading or confusing
"""

import logging
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, asdict, field
from enum import Enum
import json
from pathlib import Path

logger = logging.getLogger(__name__)


class ErrorCategory(Enum):
    """Categories of commit message errors."""
    MISSING_KEY_CHANGE = "missing_key_change"
    TOO_GENERIC = "too_generic"
    HALLUCINATED = "hallucinated_incorrect"
    WRONG_TYPE = "wrong_commit_type"
    FORMAT_VIOLATION = "format_violation"
    INCOMPLETE = "incomplete"
    OUT_OF_SCOPE = "out_of_scope"
    SEMANTIC_MISMATCH = "semantic_mismatch"
    OTHER = "other"


class SeverityLevel(Enum):
    """Severity of error impact."""
    CRITICAL = "critical"      # Message is unusable
    HIGH = "high"              # Significant issues
    MEDIUM = "medium"          # Moderate issues
    LOW = "low"                # Minor issues
    NONE = "none"              # No error


@dataclass
class ErrorAnnotation:
    """Annotation of an error in a commit message."""
    commit_hash: str
    generated_message: str
    reference_message: str
    
    category: ErrorCategory
    severity: SeverityLevel
    description: str              # Detailed explanation
    affected_section: Optional[str] = None  # Quote of problematic text
    suggestion: Optional[str] = None       # Proposed correction
    
    def to_dict(self) -> Dict:
        """Convert to dictionary with enum strings."""
        data = asdict(self)
        data['category'] = self.category.value
        data['severity'] = self.severity.value
        return data


@dataclass
class MessageQualityAssessment:
    """Overall quality assessment of a commit message."""
    commit_hash: str
    generated_message: str
    reference_message: str
    
    has_errors: bool = False
    quality_score: float = 1.0  # 0-1, where 1 is perfect
    errors: List[ErrorAnnotation] = field(default_factory=list)
    overall_severity: SeverityLevel = SeverityLevel.NONE
    is_usable: bool = True  # Can this be used in production?
    
    def to_dict(self) -> Dict:
        """Convert to dictionary."""
        data = {
            'commit_hash': self.commit_hash,
            'generated_message': self.generated_message,
            'reference_message': self.reference_message,
            'has_errors': self.has_errors,
            'quality_score': self.quality_score,
            'overall_severity': self.overall_severity.value,
            'is_usable': self.is_usable,
            'errors': [e.to_dict() for e in self.errors]
        }
        return data


class ErrorDetector:
    """
    Detects and categorizes errors in commit messages.
    
    Uses heuristic and pattern-based detection for automated error annotation.
    """
    
    def __init__(self):
        """Initialize detector."""
        self.conventional_types = {
            'fix', 'feat', 'refactor', 'perf', 'docs', 
            'test', 'chore', 'style', 'ci', 'build'
        }
    
    def assess(self, commit_hash: str, generated: str, reference: str, 
               diff: str = "") -> MessageQualityAssessment:
        """
        Assess message quality and detect errors.
        
        Args:
            commit_hash: Commit identifier
            generated: AI-generated message
            reference: Human-written reference
            diff: Original code diff (optional, for hallucination detection)
            
        Returns:
            MessageQualityAssessment with detected errors
        """
        assessment = MessageQualityAssessment(
            commit_hash=commit_hash,
            generated_message=generated,
            reference_message=reference
        )
        
        # Run detectors
        self._detect_format_violations(assessment)
        self._detect_incompleteness(assessment)
        self._detect_missing_changes(assessment, reference)
        self._detect_hallucinations(assessment, diff)
        self._detect_generic_message(assessment)
        self._detect_wrong_type(assessment, reference)
        
        # Compute overall assessment
        self._compute_overall(assessment)
        
        return assessment
    
    def _detect_format_violations(self, assessment: MessageQualityAssessment):
        """Detect conventional commit format violations."""
        msg = assessment.generated_message.strip()
        
        # Check if starts with type:
        valid_prefix = any(msg.lower().startswith(f"{t}:") for t in self.conventional_types)
        
        if msg and not valid_prefix:
            # Try to detect if it looks like it should have a type
            if ':' not in msg.split('\n')[0]:  # First line has no colon
                assessment.errors.append(ErrorAnnotation(
                    commit_hash=assessment.commit_hash,
                    generated_message=assessment.generated_message,
                    reference_message=assessment.reference_message,
                    category=ErrorCategory.FORMAT_VIOLATION,
                    severity=SeverityLevel.HIGH,
                    description="Message doesn't follow conventional commit format (missing type:scope)",
                    affected_section=msg.split('\n')[0][:50]
                ))
    
    def _detect_incompleteness(self, assessment: MessageQualityAssessment):
        """Detect incomplete/truncated messages."""
        msg = assessment.generated_message.strip()
        
        # Signs of truncation
        if msg.endswith('...') or msg.endswith('…'):
            assessment.errors.append(ErrorAnnotation(
                commit_hash=assessment.commit_hash,
                generated_message=assessment.generated_message,
                reference_message=assessment.reference_message,
                category=ErrorCategory.INCOMPLETE,
                severity=SeverityLevel.HIGH,
                description="Message appears truncated (ends with ellipsis)",
                affected_section=msg[-30:]
            ))
        
        # Very short messages might be incomplete
        if len(msg.split('\n')[0]) < 10:
            assessment.errors.append(ErrorAnnotation(
                commit_hash=assessment.commit_hash,
                generated_message=assessment.generated_message,
                reference_message=assessment.reference_message,
                category=ErrorCategory.INCOMPLETE,
                severity=SeverityLevel.MEDIUM,
                description="Message is very short; may be incomplete",
                affected_section=msg[:50]
            ))
    
    def _detect_missing_changes(self, assessment: MessageQualityAssessment, reference: str):
        """Detect when generated message is missing key changes from reference."""
        gen_lower = assessment.generated_message.lower()
        ref_lower = reference.lower()
        
        # Extract keywords from reference
        keywords = self._extract_keywords(reference)
        missing = [kw for kw in keywords if kw not in gen_lower and len(kw) > 3]
        
        if len(missing) >= 2:  # Multiple important keywords missing
            assessment.errors.append(ErrorAnnotation(
                commit_hash=assessment.commit_hash,
                generated_message=assessment.generated_message,
                reference_message=assessment.reference_message,
                category=ErrorCategory.MISSING_KEY_CHANGE,
                severity=SeverityLevel.HIGH,
                description=f"Missing key terms from reference message: {', '.join(missing[:3])}",
                suggestion=reference
            ))
    
    def _detect_hallucinations(self, assessment: MessageQualityAssessment, diff: str):
        """Detect claims about changes not in the actual diff."""
        if not diff:
            return
        
        # Simple heuristic: check if message mentions function/class names
        # that don't appear in the diff
        gen_msg = assessment.generated_message
        
        # Extract potential identifiers (word-like sequences)
        import re
        identifiers = re.findall(r'\b[A-Za-z_][A-Za-z0-9_]*\b', gen_msg)
        
        # Check which appear in diff
        missing_from_diff = [
            ident for ident in identifiers
            if ident not in diff and len(ident) > 3 and ident.lower() not in ['this', 'that', 'with', 'from']
        ]
        
        if len(missing_from_diff) >= 2:
            assessment.errors.append(ErrorAnnotation(
                commit_hash=assessment.commit_hash,
                generated_message=assessment.generated_message,
                reference_message=assessment.reference_message,
                category=ErrorCategory.HALLUCINATED,
                severity=SeverityLevel.CRITICAL,
                description=f"Message mentions items not in diff: {', '.join(missing_from_diff[:3])}",
                affected_section=gen_msg
            ))
    
    def _detect_generic_message(self, assessment: MessageQualityAssessment):
        """Detect messages that are too generic and non-descriptive."""
        msg = assessment.generated_message.lower()
        
        generic_patterns = [
            'update code',
            'fix code',
            'make changes',
            'adjust settings',
            'work on',
            'improve code',
            'fix bugs',
            'add feature',
        ]
        
        if any(pattern in msg for pattern in generic_patterns):
            assessment.errors.append(ErrorAnnotation(
                commit_hash=assessment.commit_hash,
                generated_message=assessment.generated_message,
                reference_message=assessment.reference_message,
                category=ErrorCategory.TOO_GENERIC,
                severity=SeverityLevel.MEDIUM,
                description="Message is too generic and lacks specific details",
                suggestion=assessment.reference_message
            ))
    
    def _detect_wrong_type(self, assessment: MessageQualityAssessment, reference: str):
        """Detect wrong commit type classification."""
        gen_type = self._extract_commit_type(assessment.generated_message)
        ref_type = self._extract_commit_type(reference)
        
        if gen_type and ref_type and gen_type != ref_type:
            assessment.errors.append(ErrorAnnotation(
                commit_hash=assessment.commit_hash,
                generated_message=assessment.generated_message,
                reference_message=assessment.reference_message,
                category=ErrorCategory.WRONG_TYPE,
                severity=SeverityLevel.HIGH,
                description=f"Wrong commit type: '{gen_type}' instead of '{ref_type}'",
                affected_section=f"{gen_type}:",
                suggestion=reference.replace(ref_type + ":", gen_type + ":")
            ))
    
    def _extract_commit_type(self, message: str) -> Optional[str]:
        """Extract commit type from message."""
        match = message.split(':')[0].split('(')[0].strip()
        if match in self.conventional_types:
            return match
        return None
    
    def _extract_keywords(self, text: str) -> List[str]:
        """Extract important keywords from text."""
        import re
        # Get words longer than 3 chars, excluding common words
        common_words = {'the', 'and', 'for', 'with', 'from', 'this', 'that', 'have', 'will'}
        words = re.findall(r'\b[a-z]{4,}\b', text.lower())
        return [w for w in words if w not in common_words]
    
    def _compute_overall(self, assessment: MessageQualityAssessment):
        """Compute overall quality assessment."""
        if not assessment.errors:
            assessment.has_errors = False
            assessment.quality_score = 1.0
            assessment.overall_severity = SeverityLevel.NONE
            assessment.is_usable = True
        else:
            assessment.has_errors = True
            
            # Find max severity
            severities = [e.severity for e in assessment.errors]
            severity_order = [SeverityLevel.CRITICAL, SeverityLevel.HIGH, 
                            SeverityLevel.MEDIUM, SeverityLevel.LOW]
            assessment.overall_severity = max(severities, key=lambda s: severity_order.index(s))
            
            # Compute quality score (deduct based on severity)
            deductions = {
                SeverityLevel.CRITICAL: 0.5,
                SeverityLevel.HIGH: 0.2,
                SeverityLevel.MEDIUM: 0.1,
                SeverityLevel.LOW: 0.05
            }
            quality = 1.0
            for error in assessment.errors:
                quality -= deductions.get(error.severity, 0.05)
            
            assessment.quality_score = max(0.0, quality)
            assessment.is_usable = assessment.overall_severity != SeverityLevel.CRITICAL


class ErrorTaxonomy:
    """Manages error taxonomy and analysis."""
    
    def __init__(self):
        """Initialize taxonomy."""
        self.detector = ErrorDetector()
        self.assessments: List[MessageQualityAssessment] = []
    
    def assess_messages(self, triples: List[Tuple[str, str, str]], 
                       diffs: Optional[List[str]] = None) -> List[MessageQualityAssessment]:
        """
        Assess multiple messages.
        
        Args:
            triples: List of (commit_hash, generated, reference) tuples
            diffs: Optional list of diffs for hallucination detection
            
        Returns:
            List of MessageQualityAssessment
        """
        diffs_map = {diff_hash: diff for diff_hash, diff in 
                    zip([t[0] for t in triples], diffs or [])} if diffs else {}
        
        assessments = []
        for commit_hash, generated, reference in triples:
            diff = diffs_map.get(commit_hash, "")
            assessment = self.detector.assess(commit_hash, generated, reference, diff)
            assessments.append(assessment)
        
        self.assessments.extend(assessments)
        return assessments
    
    def generate_report(self) -> Dict:
        """Generate error analysis report."""
        if not self.assessments:
            return {}
        
        # Count errors by category
        category_counts = {}
        severity_counts = {}
        
        for assessment in self.assessments:
            for error in assessment.errors:
                cat = error.category.value
                sev = error.severity.value
                
                category_counts[cat] = category_counts.get(cat, 0) + 1
                severity_counts[sev] = severity_counts.get(sev, 0) + 1
        
        # Quality statistics
        quality_scores = [a.quality_score for a in self.assessments]
        usable_count = sum(1 for a in self.assessments if a.is_usable)
        
        report = {
            'total_assessed': len(self.assessments),
            'messages_with_errors': sum(1 for a in self.assessments if a.has_errors),
            'usable_messages': usable_count,
            'usable_percentage': (usable_count / len(self.assessments) * 100) if self.assessments else 0,
            'quality_score_mean': sum(quality_scores) / len(quality_scores) if quality_scores else 0,
            'quality_score_median': sorted(quality_scores)[len(quality_scores) // 2] if quality_scores else 0,
            'errors_by_category': category_counts,
            'errors_by_severity': severity_counts,
            'most_common_error': max(category_counts.items(), key=lambda x: x[1])[0] if category_counts else None,
        }
        
        return report
    
    def save_report(self, output_file: Path):
        """Save error taxonomy report."""
        output_file = Path(output_file)
        output_file.parent.mkdir(parents=True, exist_ok=True)
        
        data = {
            'report': self.generate_report(),
            'assessments': [a.to_dict() for a in self.assessments]
        }
        
        with open(output_file, 'w') as f:
            json.dump(data, f, indent=2)
        
        logger.info(f"Saved error taxonomy report to {output_file}")


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    
    detector = ErrorDetector()
    
    # Test examples
    test_cases = [
        ("fix123", "fix: handle null reference", "fix: resolve null pointer exception in auth module", "diff"),
        ("feat456", "Update code", "feat: add user profile page with avatar support", "diff"),
        ("hal789", "fix: update database connection settings", "fix: refactor database query logic", "diff with query changes"),
    ]
    
    for commit_hash, generated, reference, diff in test_cases:
        assessment = detector.assess(commit_hash, generated, reference, diff)
        print(f"\n{commit_hash}:")
        print(f"  Quality Score: {assessment.quality_score:.2f}")
        print(f"  Errors: {len(assessment.errors)}")
        for error in assessment.errors:
            print(f"    - [{error.category.value}] {error.description}")
