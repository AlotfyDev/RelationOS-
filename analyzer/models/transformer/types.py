#!/usr/bin/env python3
"""
RelationOS Transformer Types
All data classes, enums, and type definitions for the transformer classifier
"""

import numpy as np
from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Tuple, Any, Optional

@dataclass
class ClassificationResult:
    """Enhanced classification result with detailed metrics"""
    relation_name: str
    primary_domain: str
    subdomain: str
    confidence: float
    alternative_domains: List[Tuple[str, float]]
    reasoning: Dict[str, Any]
    feature_contributions: Dict[str, float]
    processing_details: Dict[str, Any] = field(default_factory=dict)

@dataclass
class ExpertParameters:
    """Expert-tunable parameters for MODE_EXPERT"""
    # Model hyperparameters
    learning_rate: float = 2e-5
    batch_size: int = 16
    num_epochs: int = 3
    max_length: int = 512
    warmup_steps: int = 500

    # Classification thresholds
    confidence_threshold: float = 0.75
    uncertainty_buffer: float = 0.1

    # Feature engineering
    use_context_window: bool = True
    context_window_size: int = 100
    include_ngrams: bool = True
    ngram_range: Tuple[int, int] = (1, 3)

    # Domain-specific boosting
    sysml_boost: float = 1.2
    uml_boost: float = 1.1

    # Training parameters
    use_data_augmentation: bool = True
    augmentation_factor: float = 1.5
    validation_split: float = 0.2

    # Inference optimization
    quantization: bool = False
    mixed_precision: bool = True
    batch_inference: bool = True
    inference_batch_size: int = 32

class ClassificationMode(Enum):
    """Operating modes with different accuracy/speed trade-offs"""
    MODE_EXPRESS = "express"      # Fast, basic sklearn accuracy (~85%)
    MODE_STANDARD = "standard"    # Balanced ML performance (~90%)
    MODE_PRECISE = "precise"      # Maximum accuracy with ensemble (~92%)
    MODE_EXPERT = "expert"        # Tunable parameters, custom fine-tuning (~95%+)

@dataclass
class TrainingResult:
    """Result of a training operation"""
    success: bool
    training_time: float = 0.0
    final_loss: float = 0.0
    eval_accuracy: float = 0.0
    eval_f1: float = 0.0
    model_type: str = ""
    error_message: str = ""

@dataclass
class InferenceResult:
    """Result of an inference operation"""
    predictions: List[ClassificationResult]
    processing_time_ms: float
    batch_size: int
    model_used: str
    errors: List[str] = field(default_factory=list)

@dataclass
class ModelMetadata:
    """Metadata about trained models"""
    model_name: str
    model_type: str
    trained_on: str
    accuracy_score: float
    domain_coverage: Dict[str, int]
    hyperparameters: Dict[str, Any]
    training_date: str

# Type aliases for better readability
RelationList = List[str]
ContextList = List[str]
ClassificationList = List[ClassificationResult]
DomainMapping = Dict[str, int]
FeatureVector = np.ndarray

# Constants for type safety
MAX_RELATION_LENGTH = 512
MAX_CONTEXT_WINDOW = 1000
DEFAULT_CONFIDENCE_THRESHOLD = 0.75

# Validation helpers for type checking
def validate_classification_result(result: ClassificationResult) -> bool:
    """Validate a classification result for correctness"""
    if not isinstance(result, ClassificationResult):
        return False
    if not isinstance(result.relation_name, str) or len(result.relation_name) == 0:
        return False
    if not isinstance(result.primary_domain, str) or len(result.primary_domain) == 0:
        return False
    if not isinstance(result.confidence, (int, float)) or not 0 <= result.confidence <= 1:
        return False
    return True

def validate_expert_parameters(params: ExpertParameters) -> List[str]:
    """Validate expert parameters and return error messages"""
    errors = []

    # Learning rate validation
    if not 1e-6 <= params.learning_rate <= 1e-2:
        errors.append(f"learning_rate must be between 1e-6 and 1e-2, got {params.learning_rate}")

    # Batch size validation
    if not 1 <= params.batch_size <= 128:
        errors.append(f"batch_size must be between 1 and 128, got {params.batch_size}")

    # Confidence threshold validation
    if not 0.1 <= params.confidence_threshold <= 1.0:
        errors.append(f"confidence_threshold must be between 0.1 and 1.0, got {params.confidence_threshold}")

    # Context window validation
    if not 0 <= params.context_window_size <= MAX_CONTEXT_WINDOW:
        errors.append(f"context_window_size must be <= {MAX_CONTEXT_WINDOW}, got {params.context_window_size}")

    # Domain boost validation
    for boost_name, boost_value in [("sysml_boost", params.sysml_boost), ("uml_boost", params.uml_boost)]:
        if not 1.0 <= boost_value <= 3.0:
            errors.append(f"{boost_name} must be between 1.0 and 3.0, got {boost_value}")

    return errors
