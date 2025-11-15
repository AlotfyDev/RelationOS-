#!/usr/bin/env python3
"""
RelationOS Enhanced Transformer Classifier Package
State-of-the-art ML classifier using BAAI/bge-reranker-v2-m3
Optimized for accuracy with expert tunable parameters and feed-forward learning
"""

from .types import ClassificationResult, ExpertParameters, ClassificationMode
from .base_classifier import BaseClassifier
from .bge_classifier import BGEClassifier
from .sklearn_fallback import SklearnFallbackClassifier
from .rule_based import RuleBasedClassifier
from .training import TrainingPipeline
from .inference import InferenceEngine
from .utils import parameter_validator, preprocess_text, postprocess_result

__version__ = "2.0.0"
__author__ = "RelationOS Team"
__description__ = "State-of-the-art transformer-based relation classifier for MBSE"

__all__ = [
    # Core types
    "ClassificationResult",
    "ExpertParameters",
    "ClassificationMode",

    # Classifiers
    "BaseClassifier",
    "BGEClassifier",
    "SklearnFallbackClassifier",
    "RuleBasedClassifier",

    # Training & Inference
    "TrainingPipeline",
    "InferenceEngine",

    # Utilities
    "parameter_validator",
    "preprocess_text",
    "postprocess_result"
]
