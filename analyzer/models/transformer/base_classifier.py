#!/usr/bin/env python3
"""
Base Classifier
Abstract interface for all relation classifiers with unified API
"""

import abc
from typing import Dict, List, Optional, Any
import logging
from .types import ClassificationResult, ClassificationMode, ExpertParameters
from pathlib import Path

class BaseClassifier:
    """
    Abstract base class for all relation classifiers.
    Provides unified interface while allowing different implementations.
    """

    def __init__(self,
                 mode: ClassificationMode = ClassificationMode.MODE_EXPERT,
                 expert_params: Optional[ExpertParameters] = None,
                 config_path: Optional[str] = None):

        self.mode = mode
        self.expert_params = expert_params or ExpertParameters()
        self.config_path = config_path or "analyzer/config/classifier_config.json"
        self.logger = logging.getLogger(self.__class__.__name__)

        # Initialization state
        self.is_initialized = False
        self.is_trained = False
        self.model_name = ""
        self.initialization_errors: List[str] = []

        # Performance tracking
        self.total_classifications = 0
        self.average_confidence = 0.0

    @abc.abstractmethod
    def initialize(self) -> bool:
        """Initialize the classifier with required resources"""
        pass

    @abc.abstractmethod
    def classify_relation(self,
                         relation: str,
                         context: str = "",
                         threshold_override: float = None) -> ClassificationResult:
        """Classify a single relation"""
        pass

    @abc.abstractmethod
    def classify_batch(self,
                      relations: List[str],
                      contexts: List[str] = None,
                      batch_size: int = None) -> List[ClassificationResult]:
        """Classify multiple relations efficiently"""
        pass

    @abc.abstractmethod
    def train(self,
             training_data,
             training_parameters: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Train the classifier on provided data"""
        pass

    @abc.abstractmethod
    def is_ready_for_inference(self) -> bool:
        """Check if classifier is ready for classification tasks"""
        pass

    # Utility methods with default implementations
    def validate_input(self, relation: str, context: str = "") -> List[str]:
        """Validate input parameters and return error messages"""
        errors = []

        if not relation or not isinstance(relation, str):
            errors.append("relation must be a non-empty string")

        if len(relation) > 1000:  # Reasonable limit
            errors.append("relation text is too long (max 1000 characters)")

        if context and len(context) > 5000:  # Context limit
            errors.append("context is too long (max 5000 characters)")

        return errors

    def get_performance_stats(self) -> Dict[str, Any]:
        """Get performance statistics for monitoring"""
        return {
            "total_classifications": self.total_classifications,
            "average_confidence": self.average_confidence,
            "model_name": self.model_name,
            "is_trained": self.is_trained,
            "mode": self.mode.value if self.mode else None,
            "initialization_errors": self.initialization_errors.copy()
        }

    def reset_stats(self):
        """Reset performance statistics"""
        self.total_classifications = 0
        self.average_confidence = 0.0

    def save_config(self, config_path: Optional[Path] = None) -> bool:
        """Save current configuration for persistence"""
        if config_path is None:
            config_path = Path(self.config_path)

        try:
            config_path.parent.mkdir(parents=True, exist_ok=True)

            config_data = {
                "mode": self.mode.value if self.mode else "expert",
                "model_name": self.model_name,
                "expert_params": self.expert_params.__dict__ if self.expert_params else {},
                "is_trained": self.is_trained,
                "performance_stats": self.get_performance_stats()
            }

            import json
            with open(config_path, 'w') as f:
                json.dump(config_data, f, indent=2, default=str)

            self.logger.info(f"Configuration saved to {config_path}")
            return True

        except Exception as e:
            self.logger.error(f"Failed to save config: {e}")
            return False

    def load_config(self, config_path: Optional[Path] = None) -> bool:
        """Load configuration from file"""
        if config_path is None:
            config_path = Path(self.config_path)

        try:
            import json
            with open(config_path, 'r') as f:
                config_data = json.load(f)

            # Restore state
            self.mode = ClassificationMode(config_data.get("mode", "expert"))
            self.model_name = config_data.get("model_name", "")
            self.is_trained = config_data.get("is_trained", False)

            # Expert parameters
            expert_config = config_data.get("expert_params", {})
            if expert_config and self.expert_params:
                for key, value in expert_config.items():
                    if hasattr(self.expert_params, key):
                        setattr(self.expert_params, key, value)

            # Performance stats
            stats = config_data.get("performance_stats", {})
            if stats:
                self.total_classifications = stats.get("total_classifications", 0)
                self.average_confidence = stats.get("average_confidence", 0.0)

            self.logger.info(f"Configuration loaded from {config_path}")
            return True

        except Exception as e:
            self.logger.error(f"Failed to load config: {e}")
            return False

    def get_expert_parameters_template(self) -> Dict[str, Any]:
        """Get template for expert parameter tuning (base implementation)"""
        return {
            "performance_tuning": {},
            "inference_optimization": {},
            "domain_optimization": {},
            "training_enhancements": {},
            "specific_parameters": {}
        }

    def _update_performance_stats(self, result: ClassificationResult):
        """Update internal performance statistics"""
        self.total_classifications += 1

        # Rolling average confidence calculation
        if self.total_classifications == 1:
            self.average_confidence = result.confidence
        else:
            # Incremental update for numerical stability
            self.average_confidence += (result.confidence - self.average_confidence) / self.total_classifications

    def __repr__(self) -> str:
        """String representation for debugging"""
        return (f"{self.__class__.__name__}("
                f"mode={self.mode.value if self.mode else 'none'}, "
                f"trained={self.is_trained}, "
                f"model={self.model_name or 'uninitialized'})")

class ClassifierRegistry:
    """
    Registry for managing classifier instances and configurations.
    Provides factory methods for creating classifier instances.
    """

    _registry: Dict[str, type] = {}

    @classmethod
    def register(cls, name: str, classifier_class: type):
        """Register a classifier class by name"""
        cls._registry[name.lower()] = classifier_class

    @classmethod
    def create_classifier(cls, name: str, **kwargs) -> Optional[BaseClassifier]:
        """Create a classifier instance by name"""
        classifier_class = cls._registry.get(name.lower())
        if classifier_class is None:
            return None

        try:
            return classifier_class(**kwargs)
        except Exception as e:
            logging.error(f"Failed to create classifier {name}: {e}")
            return None

    @classmethod
    def get_available_classifiers(cls) -> List[str]:
        """Get list of all registered classifier names"""
        return list(cls._registry.keys())

    @classmethod
    def get_classifier_info(cls, name: str) -> Optional[Dict[str, Any]]:
        """Get information about a specific classifier"""
        classifier_class = cls._registry.get(name.lower())
        if classifier_class is None:
            return None

        return {
            "name": name,
            "class": classifier_class.__name__,
            "description": getattr(classifier_class, "__doc__", ""),
            "module": classifier_class.__module__
        }

# Global registry instance
REGISTRY = ClassifierRegistry()

# Decorator for automatic registration
def register_classifier(name: str):
    """Decorator to automatically register classifier classes"""
    def decorator(cls):
        REGISTRY.register(name, cls)
        return cls
    return decorator
