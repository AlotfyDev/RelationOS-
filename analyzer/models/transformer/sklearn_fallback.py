#!/usr/bin/env python3
"""
Sklearn Fallback Classifier
Traditional ML approach using ensemble methods for relation classification
Provides backward compatibility when transformers are unavailable
"""

from typing import Dict, List, Tuple, Any, Optional
import logging
import numpy as np
import pickle
from pathlib import Path

try:
    from sklearn.ensemble import RandomForestClassifier, VotingClassifier
    from sklearn.svm import SVC
    from sklearn.naive_bayes import MultinomialNB
    from sklearn.feature_extraction.text import TfidfVectorizer
    from sklearn.model_selection import train_test_split
    from sklearn.metrics import classification_report
    SKLEARN_AVAILABLE = True
except ImportError:
    SKLEARN_AVAILABLE = False

from .base_classifier import BaseClassifier, register_classifier
from .relation_types import *

@register_classifier("sklearn")
class SklearnFallbackClassifier(BaseClassifier):
    """
    Sklearn-based ensemble classifier for relation classification.
    Uses TF-IDF vectorization with Random Forest, SVM, and Naive Bayes ensemble.
    Provides reliable performance with minimal dependencies.
    """

    def __init__(self,
                 mode: ClassificationMode = ClassificationMode.MODE_EXPRESS,
                 expert_params: Optional[ExpertParameters] = None,
                 config_path: Optional[str] = None):

        super().__init__(mode, expert_params, config_path)

        # Sklearn-specific attributes
        self.model_name = "sklearn_ensemble"
        self.vectorizer = None
        self.sklearn_model = None
        self.taxonomy = {}
        self.label_classes = []

        self.logger.info(f"Sklearn Fallback Classifier initialized in {self.mode.value} mode")

    def initialize(self) -> bool:
        """Initialize sklearn classifier components"""

        if not SKLEARN_AVAILABLE:
            error_msg = "Sklearn libraries not available. Install with: pip install scikit-learn"
            self.logger.error(error_msg)
            self.initialization_errors.append(error_msg)
            return False

        try:
            # Load domain taxonomy
            if not self._load_taxonomy():
                error_msg = "Failed to load domain taxonomy"
                self.initialization_errors.append(error_msg)
                return False

            # Initialize vectorizer and classifier
            if not self._initialize_sklearn_components():
                error_msg = "Failed to initialize sklearn components"
                self.initialization_errors.append(error_msg)
                return False

            self.is_initialized = True
            self.logger.info(f"Sklearn classifier initialized with {len(self.taxonomy)} domains")
            return True

        except Exception as e:
            error_msg = f"Sklearn initialization failed: {e}"
            self.logger.error(error_msg)
            self.initialization_errors.append(error_msg)
            return False

    def _load_taxonomy(self) -> bool:
        """Load domain taxonomy for sklearn classification"""
        try:
            with open("analyzer/config/domain_taxonomy.json", 'r') as f:
                config = json.load(f)

            self.taxonomy = config.get("primary_domains", {})
            self.logger.info(f"Loaded {len(self.taxonomy)} domain categories for sklearn")
            return True

        except Exception as e:
            self.logger.error(f"Failed to load taxonomy: {e}")
            return False

    def _initialize_sklearn_components(self) -> bool:
        """Initialize sklearn vectorizer and ensemble classifier"""
        try:
            # Initialize TF-IDF vectorizer with sklearn config
            vectorizer_config = self.config.get("ml_classifier", {}).get("features", {}).get("tfidf", {})
            self.vectorizer = TfidfVectorizer(
                max_features=vectorizer_config.get("max_features", 5000),
                ngram_range=tuple(vectorizer_config.get("ngram_range", [1, 2])),
                lowercase=True,
                stop_words='english'
            )

            # Initialize ensemble classifier
            estimators = [
                ('rf', RandomForestClassifier(
                    n_estimators=200,  # Increased for better accuracy
                    random_state=42,
                    class_weight='balanced',
                    max_depth=15,
                    min_samples_split=5
                )),
                ('svm', SVC(
                    probability=True,
                    random_state=42,
                    class_weight='balanced',
                    kernel='linear',  # Better for text classification
                    C=1.0
                )),
                ('nb', MultinomialNB(alpha=0.1))  # Laplace smoothing
            ]

            # Use soft voting for probability-based predictions
            self.sklearn_model = VotingClassifier(
                estimators=estimators,
                voting='soft',  # Use probabilities
                weights=[0.4, 0.4, 0.2]  # Weighted voting: RF/SVM more important
            )

            self.logger.info("Sklearn components initialized successfully")
            return True

        except Exception as e:
            self.logger.error(f"Sklearn component initialization failed: {e}")
            return False

    def is_ready_for_inference(self) -> bool:
        """Check if sklearn classifier is ready for inference"""
        return (self.is_initialized and
                self.vectorizer is not None and
                self.sklearn_model is not None and
                (self.is_trained or hasattr(self.sklearn_model, 'classes_')))

    def classify_relation(self,
                         relation: str,
                         context: str = "",
                         threshold_override: float = None) -> ClassificationResult:

        if not self.is_ready_for_inference():
            return ClassificationResult(
                relation_name=relation,
                primary_domain="Uncategorized",
                subdomain="general",
                confidence=0.0,
                alternative_domains=[],
                reasoning={"error": "Sklearn classifier not ready for inference"},
                feature_contributions={}
            )

        try:
            threshold = threshold_override if threshold_override is not None else self.expert_params.confidence_threshold

            # Input validation
            validation_errors = self.validate_input(relation, context)
            if validation_errors:
                return ClassificationResult(
                    relation_name=relation,
                    primary_domain="Uncategorized",
                    subdomain="general",
                    confidence=0.0,
                    alternative_domains=[],
                    reasoning={"validation_errors": validation_errors},
                    feature_contributions={}
                )

            # Prepare input text
            input_text = self._prepare_input_text(relation, context)

            # Vectorize
            features = self.vectorizer.transform([input_text])

            # Predict
            if hasattr(self.sklearn_model, 'predict_proba'):
                probabilities = self.sklearn_model.predict_proba(features)[0]
                predicted_class_id = np.argmax(probabilities)
                confidence = probabilities[predicted_class_id]
            else:
                predicted_class_id = self.sklearn_model.predict(features)[0]
                confidence = 0.5  # Default when no probabilities available

            # Get predicted domain
            if hasattr(self.sklearn_model, 'classes_'):
                predicted_domain = self.sklearn_model.classes_[predicted_class_id]
            else:
                predicted_domain = "Uncategorized"

            # Apply domain-specific boosting
            confidence = self._apply_domain_boosting(confidence, predicted_domain)

            # Get alternative domains
            if hasattr(self.sklearn_model, 'predict_proba'):
                prob_pairs = list(zip(self.sklearn_model.classes_, probabilities))
                prob_pairs.sort(key=lambda x: x[1], reverse=True)
                alternative_domains = prob_pairs[1:4]  # Top 3 alternatives
            else:
                alternative_domains = []

            # Determine subdomain
            subdomain = self._get_subdomain(relation, predicted_domain)

            # Generate reasoning
            reasoning = {
                'model_type': 'sklearn_ensemble',
                'vectorizer_features': self.vectorizer.transform([input_text]).shape[1],
                'input_length': len(input_text),
                'context_used': bool(context),
                'prediction_method': 'soft_voting' if hasattr(self.sklearn_model, 'predict_proba') else 'hard_voting'
            }

            # Feature contributions
            feature_contributions = {
                'tfidf_relevance': confidence,
                'context_boost': float(bool(context)),
                'domain_specific_boost': self._calculate_domain_boost(predicted_domain),
                'ensemble_agreement_score': confidence
            }

            processing_details = {
                'model_used': self.model_name,
                'classifier_type': 'VotingClassifier',
                'vectorizer_type': 'TfidfVectorizer',
                'feature_count': self.vectorizer.transform([input_text]).shape[1],
                'trained_domains': len(self.sklearn_model.classes_) if hasattr(self.sklearn_model, 'classes_') else 0
            }

            result = ClassificationResult(
                relation_name=relation,
                primary_domain=predicted_domain,
                subdomain=subdomain,
                confidence=min(confidence, 1.0),
                alternative_domains=alternative_domains,
                reasoning=reasoning,
                feature_contributions=feature_contributions,
                processing_details=processing_details
            )

            self._update_performance_stats(result)
            return result

        except Exception as e:
            self.logger.error(f"Sklearn classification failed for '{relation}': {e}")
            return ClassificationResult(
                relation_name=relation,
                primary_domain="Uncategorized",
                subdomain="general",
                confidence=0.0,
                alternative_domains=[],
                reasoning={"error": str(e)},
                feature_contributions={}
            )

    def classify_batch(self,
                      relations: List[str],
                      contexts: List[str] = None,
                      batch_size: int = None) -> List[ClassificationResult]:

        if not self.is_ready_for_inference():
            return [ClassificationResult(
                relation_name=rel,
                primary_domain="Uncategorized",
                subdomain="general",
                confidence=0.0,
                alternative_domains=[],
                reasoning={"error": "Sklearn classifier not ready"},
                feature_contributions={}
            ) for rel in relations]

        # For sklearn, process all at once (sklearn is efficient with vectorized operations)
        contexts = contexts or [''] * len(relations)
        results = []

        for relation, context in zip(relations, contexts):
            result = self.classify_relation(relation, context)
            results.append(result)

        return results

    def _prepare_input_text(self, relation: str, context: str = "") -> str:
        """Prepare input text for sklearn vectorization"""
        if context and self.expert_params.use_context_window:
            context_window = context[:self.expert_params.context_window_size]
            return f"{relation} {context_window}"
        else:
            return relation

    def _apply_domain_boosting(self, confidence: float, domain: str) -> float:
        """Apply domain-specific confidence boosting for sklearn"""
        boost = 1.0

        domain_lower = domain.lower()
        if 'traceability' in domain_lower or 'requirement' in domain_lower:
            boost = self.expert_params.sysml_boost
        elif 'structural' in domain_lower or 'component' in domain_lower:
            boost = 1.1
        elif 'behavioral' in domain_lower or 'function' in domain_lower:
            boost = 1.05

        return min(confidence * boost, 1.0)

    def _calculate_domain_boost(self, domain: str) -> float:
        """Calculate boost factor for feature contributions"""
        boost = self._apply_domain_boosting(1.0, domain)
        return boost - 1.0

    def train(self, training_data, training_parameters: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Train sklearn classifier on relation data"""

        if not self.is_initialized:
            return {'error': 'Classifier not initialized', 'success': False}

        training_params = training_parameters or {}

        try:
            self.logger.info("Starting sklearn ensemble training...")

            # Validate training data
            if not isinstance(training_data, pd.DataFrame):
                return {'error': 'Training data must be pandas DataFrame with relation_name and domain columns', 'success': False}

            # Prepare training data
            processed_data = self._prepare_sklearn_training_data(training_data)
            if not processed_data:
                return {'error': 'Failed to process training data', 'success': False}

            # Execute training
            training_result = self._train_sklearn_model(processed_data)

            if training_result.get('success'):
                self.is_trained = True
                self.logger.info("Sklearn training completed successfully")

            return training_result

        except Exception as e:
            error_msg = f"Sklearn training failed: {e}"
            self.logger.error(error_msg)
            return {'error': error_msg, 'success': False}

    def _prepare_sklearn_training_data(self, training_data: pd.DataFrame) -> Optional[Dict]:
        """Prepare training data for sklearn"""
        try:
            # Validate required columns
            required_cols = ['relation_name', 'domain']
            if not all(col in training_data.columns for col in required_cols):
                self.logger.error(f"Training data missing columns: {required_cols}")
                return None

            # Clean and prepare data
            data = training_data.copy()
            data['relation_name'] = data['relation_name'].astype(str).str.strip()
            data['domain'] = data['domain'].astype(str).str.strip()

            # Remove invalid entries
            data = data[data['relation_name'].str.len() > 0]
            data = data[data['domain'].str.len() > 0]

            if len(data) == 0:
                self.logger.error("No valid training data after cleaning")
                return None

            texts = []
            labels = []

            for idx, row in data.iterrows():
                # Prepare text (potentially with context)
                if row.get('context') and self.expert_params.use_context_window:
                    text = f"{row['relation_name']} {row['context'][:self.expert_params.context_window_size]}"
                else:
                    text = row['relation_name']

                texts.append(text)
                labels.append(row['domain'])

            return {
                'texts': texts,
                'labels': labels,
                'unique_labels': len(set(labels)),
                'total_samples': len(texts)
            }

        except Exception as e:
            self.logger.error(f"Training data preparation failed: {e}")
            return None

    def _train_sklearn_model(self, data: Dict) -> Dict[str, Any]:
        """Execute sklearn training"""
        try:
            texts, labels = data['texts'], data['labels']

            # Split data
            validation_split = self.expert_params.validation_split
            X_train, X_test, y_train, y_test = train_test_split(
                texts, labels,
                test_size=validation_split,
                random_state=42,
                stratify=labels
            )

            # Vectorize training data
            X_train_vec = self.vectorizer.fit_transform(X_train)
            X_test_vec = self.vectorizer.transform(X_test)

            # Train model
            self.sklearn_model.fit(X_train_vec, y_train)

            # Evaluate
            train_score = self.sklearn_model.score(X_train_vec, y_train)
            test_score = self.sklearn_model.score(X_test_vec, y_test)

            # Store classes for inference
            self.label_classes = list(self.sklearn_model.classes_)

            return {
                'success': True,
                'train_accuracy': train_score,
                'test_accuracy': test_score,
                'training_samples': len(X_train),
                'validation_samples': len(X_test),
                'unique_domains': data['unique_labels'],
                'model_type': 'sklearn_ensemble',
                'vectorizer_features': self.vectorizer.transform(['test']).shape[1]
            }

        except Exception as e:
            self.logger.error(f"Sklearn training execution failed: {e}")
            return {'error': str(e), 'success': False}

    def get_expert_parameters_template(self) -> Dict[str, Any]:
        """Get sklearn-specific expert parameter tuning template"""

        return {
            "performance_tuning": {
                "vectorizer_max_features": {
                    "description": "Maximum TF-IDF features",
                    "range": [1000, 10000],
                    "recommended": [3000, 5000, 7000],
                    "current": 5000  # Default in config
                },
                "ngram_range": {
                    "description": "N-gram range for vectorization",
                    "options": ["(1, 1)", "(1, 2)", "(1, 3)"],
                    "recommended": "(1, 2)",
                    "current": "(1, 2)"
                },
                "rf_n_estimators": {
                    "description": "Number of Random Forest trees",
                    "range": [50, 300],
                    "recommended": [100, 200],
                    "current": 200
                },
                "rf_max_depth": {
                    "description": "Random Forest maximum depth",
                    "range": [5, 25],
                    "recommended": [10, 15, 20],
                    "current": 15
                },
                "svm_c": {
                    "description": "SVM regularization parameter",
                    "range": [0.1, 10.0],
                    "recommended": [0.5, 1.0, 2.0],
                    "current": 1.0
                },
                "nb_alpha": {
                    "description": "Naive Bayes smoothing parameter",
                    "range": [0.01, 1.0],
                    "recommended": [0.1, 0.5],
                    "current": 0.1
                }
            },
            "domain_optimization": self._get_sklearn_domain_template(),
            "training_parameters": {
                "validation_split": {
                    "description": "Data validation split ratio",
                    "range": [0.1, 0.3],
                    "recommended": [0.15, 0.2],
                    "current": self.expert_params.validation_split
                }
            },
            "inference_optimization": {
                "batch_processing": {
                    "description": "Enable batch processing for multiple relations",
                    "options": [True, False],
                    "recommended": True,
                    "current": False  # Sklearn processes individually efficiently
                }
            }
        }

    def _get_sklearn_domain_template(self) -> Dict[str, Any]:
        """Get sklearn domain-specific tuning parameters"""
        # Use the same template as BGE but adapted for sklearn
        template = {
            "sysml_boost": {
                "description": "Boost SysML relations in ensemble voting",
                "range": [1.0, 2.0],
                "recommended": [1.2, 1.3],
                "current": self.expert_params.sysml_boost
            },
            "uml_boost": {
                "description": "Boost UML relations in ensemble voting",
                "range": [1.0, 2.0],
                "recommended": [1.0, 1.05],
                "current": self.expert_params.uml_boost
            }
        }
        return template

    def _get_subdomain(self, relation: str, primary_domain: str) -> str:
        """Determine subdomain for sklearn-based classification"""
        relation_lower = relation.lower()

        domain_config = self.taxonomy.get(primary_domain, {})
        subdomains = domain_config.get("subdomains", {})

        for subdomain, sub_config in subdomains.items():
            keywords = sub_config.get("keywords", [])
            if any(keyword in relation_lower for keyword in keywords):
                return subdomain

        return "general"
