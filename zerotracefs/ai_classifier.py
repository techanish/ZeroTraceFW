from __future__ import annotations

import logging
import re
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class ClassificationResult:
    level: str
    categories: list[str]
    confidence_score: float
    matched_patterns: int


class AIClassifier:
    """Lightweight local classifier for auto-tagging sensitive documents via regex heuristics."""
    
    CLASSIFICATION_LEVELS = {
        "public": 0,
        "internal": 1,
        "confidential": 2,
        "secret": 3
    }

    def __init__(self):
        # Patterns and their associated weights (0.0 to 1.0)
        self.patterns = {
            "PII_SSN": (re.compile(r"\b\d{3}-\d{2}-\d{4}\b"), 0.8),
            "PII_EMAIL": (re.compile(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b"), 0.3),
            "FINANCIAL_CC": (re.compile(r"\b(?:\d[ -]*?){13,16}\b"), 0.9),
            "FINANCIAL_IBAN": (re.compile(r"\b[A-Z]{2}\d{2}[A-Z0-9]{1,30}\b"), 0.7),
            "MEDICAL_RECORD": (re.compile(r"(?i)\b(patient|diagnosis|treatment|HIPAA|medical history)\b"), 0.6),
            "LEGAL_CONFIDENTIAL": (re.compile(r"(?i)\b(attorney-client privilege|nda|non-disclosure|strictly confidential)\b"), 0.9),
            "GOV_CLASSIFIED": (re.compile(r"(?i)\b(top secret|classified material|compartmented)\b"), 1.0),
        }

    def classify_text(self, text: str) -> ClassificationResult:
        """Analyzes text and assigns a classification level based on detected sensitive patterns."""
        if not text:
            return ClassificationResult(level="internal", categories=[], confidence_score=0.0, matched_patterns=0)

        total_weight = 0.0
        categories = set()
        matches = 0

        for cat, (pattern, weight) in self.patterns.items():
            found = pattern.findall(text)
            if found:
                matches += len(found)
                # Cap the weight addition per category to avoid a single category dominating infinitely
                total_weight += weight + (min(len(found), 10) * (weight * 0.1))
                categories.add(cat.split("_")[0])

        if total_weight >= 3.0:
            level = "secret"
        elif total_weight >= 1.5:
            level = "confidential"
        elif total_weight >= 0.5:
            level = "internal"
        else:
            level = "public"
            
        # If there are explicit highly sensitive words, bump it up
        if "GOV" in categories or "LEGAL" in categories:
            if self.CLASSIFICATION_LEVELS[level] < self.CLASSIFICATION_LEVELS["confidential"]:
                level = "confidential"

        return ClassificationResult(
            level=level,
            categories=list(categories),
            confidence_score=min(total_weight / 4.0, 1.0),
            matched_patterns=matches
        )

    def classify_bytes(self, data: bytes) -> ClassificationResult:
        """Attempts to decode bytes to string for classification. Fallback for binary data."""
        try:
            # Try to grab a reasonable chunk of text from the bytes
            text = data[:50000].decode('utf-8', errors='ignore')
            return self.classify_text(text)
        except Exception as e:
            logger.debug(f"Failed to classify bytes: {e}")
            return ClassificationResult(level="internal", categories=[], confidence_score=0.0, matched_patterns=0)
