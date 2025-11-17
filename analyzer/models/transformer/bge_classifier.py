#!/usr/bin/env python3
"""
BAAI BGE Classifier
State-of-the-art transformer classifier using BAAI/bge-reranker-v2-m3
Optimized for MBSE relation classification accuracy
"""

import torch
import torch.nn.functional as F
from typing import Dict, List, Tuple, Any, Optional
import logging
from pathlib import Path
import pickle

try:
    from transformers import AutoTokenizer, AutoModelForSequenceClassification
    from transformers import TrainingArguments, Trainer
    from torch.utils.data import Dataset
    TRANSFORMERS_AVAILABLE = True
except ImportError:
    TRANSFORMERS_AVAILABLE = False
    AutoTokenizer = None
    AutoModelForSequenceClassification = None
    TrainingArguments = None
    Trainer = None
    Dataset = None

from .base_classifier import BaseClassifier, register_classifier
from .relation_types import *

class RelationDataset(Dataset):
    """Dataset for relation classification training"""

    def __init__(self, encodings, labels):
        self.encodings = encodings
        self.labels = labels

    def __getitem__(self, idx):
        item = {key: torch.tensor(val[idx]) for key, val in self.encodings.items()}
        item['labels'] = torch.tensor(self.labels[idx])
        return item

    def __len__(self):
        return len(self.labels)

@register_classifier("bge")
class BGEClassifier(BaseClassifier):
    """
    BAAI BGE Reranker Classifier for MBSE relations.
    Uses BAAI/bge-reranker-v2-m3 model optimized for ranking/classification tasks.
    """

    def __init__(self,
                 mode: ClassificationMode = ClassificationMode.MODE_EXPERT,
                 expert_params: Optional[ExpertParameters] = None,
                 config_path: Optional[str] = None):

        super().__init__(mode, expert_params, config_path)

        # BGE-specific attributes
        self.model_name = "BAAI/bge-reranker-v2-m3"
        self.taxonomy = {}
        self.id_to_label = {}
        self.label_to_id = {}
        self.train_dataset = None
        self.val_dataset = None

        # Device detection with fallback
        self.device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
        self.logger.info(f"BGE Classifier initialized for device: {self.device}")

    def initialize(self) -> bool:
        """Initialize BGE model and taxonomy"""

        if not TRANSFORMERS_AVAILABLE:
            error_msg = "Transformers library not available. Install with: pip install transformers torch"
            self.logger.error(error_msg)
            self.initialization_errors.append(error_msg)
            return False

        try:
            # Load domain taxonomy
            if not self._load_taxonomy():
                error_msg = "Failed to load domain taxonomy"
                self.initialization_errors.append(error_msg)
                return False

            # Initialize BGE model
            if not self._initialize_bge_model():
                error_msg = "Failed to initialize BGE model"
                self.initialization_errors.append(error_msg)
                return False

            self.is_initialized = True
            self.logger.info(f"BGE Classifier initialized successfully with {len(self.taxonomy)} domains")
            return True

        except Exception as e:
            error_msg = f"BGE initialization failed: {e}"
            self.logger.error(error_msg)
            self.initialization_errors.append(error_msg)
            return False

    def _load_taxonomy(self) -> bool:
        """Load domain taxonomy for BGE classification"""
        try:
            with open("analyzer/config/domain_taxonomy.json", 'r') as f:
                config = json.load(f)

            self.taxonomy = config.get("primary_domains", {})
            self.logger.info(f"Loaded {len(self.taxonomy)} domain categories")
            return True

        except Exception as e:
            self.logger.error(f"Failed to load taxonomy: {e}")
            return False

    def _initialize_bge_model(self) -> bool:
        """Initialize BAAI BGE Reranker model"""
        try:
            self.logger.info(f"Loading BGE model: {self.model_name}")

            # Load tokenizer and model
            self.tokenizer = AutoTokenizer.from_pretrained(self.model_name)
            self.model = AutoModelForSequenceClassification.from_pretrained(
                self.model_name,
                num_labels=len(self.taxonomy),
                trust_remote_code=True  # BGE models may need this
            ).to(self.device)

            # Apply expert optimizations
            if self.expert_params.quantization:
                try:
                    self.model = torch.quantization.quantize_dynamic(
                        self.model, {torch.nn.Linear}, dtype=torch.qint8
                    )
                    self.logger.info("Model quantization applied")
                except Exception as e:
                    self.logger.warning(f"Quantization failed: {e}")

            if self.expert_params.mixed_precision and self.device.type == 'cuda':
                try:
                    self.model = self.model.half()  # FP16
                    self.logger.info("Mixed precision enabled")
                except Exception as e:
                    self.logger.warning(f"Mixed precision failed: {e}")

            # Create label mappings
            self._create_label_mappings()

            self.logger.info(f"BGE model loaded successfully for {len(self.taxonomy)} classes")
            return True

        except Exception as e:
            self.logger.error(f"BGE model initialization failed: {e}")
            return False

    def _create_label_mappings(self):
        """Create bidirectional label mappings"""
        unique_domains = list(self.taxonomy.keys())
        self.label_to_id = {domain: idx for idx, domain in enumerate(unique_domains)}
        self.id_to_label = {idx: domain for domain, idx in self.label_to_id.items()}
        self.logger.debug(f"Created mappings: {len(unique_domains)} domains")

    def is_ready_for_inference(self) -> bool:
        """Check if BGE classifier is ready for inference"""
        return (self.is_initialized and
                self.model is not None and
                self.tokenizer is not None and
                bool(self.id_to_label))

    def classify_relation(self,
                         relation: str,
                         context: str = "",
                         threshold_override: float = None) -> ClassificationResult:

        if not self.is_ready_for_inference():
            # Create error result
            return ClassificationResult(
                relation_name=relation,
                primary_domain="Uncategorized",
                subdomain="general",
                confidence=0.0,
                alternative_domains=[],
                reasoning={"error": "BGE classifier not ready for inference"},
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

            # Tokenize
            inputs = self.tokenizer(
                input_text,
                return_tensors="pt",
                truncation=True,
                padding=True,
                max_length=self.expert_params.max_length
            ).to(self.device)

            # Inference
            self.model.eval()
            with torch.no_grad():
                if self.expert_params.batch_inference:
                    outputs = self.model(**inputs)
                else:
                    with torch.inference_mode():
                        outputs = self.model(**inputs)

            # Process predictions
            result = self._process_prediction(outputs, relation, context)
            self._update_performance_stats(result)

            return result

        except Exception as e:
            self.logger.error(f"Classification failed for '{relation}': {e}")
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
                reasoning={"error": "BGE classifier not ready for inference"},
                feature_contributions={}
            ) for rel in relations]

        batch_size = batch_size or self.expert_params.inference_batch_size
        if contexts is None:
            contexts = [''] * len(relations)

        results = []

        # Process in batches
        for i in range(0, len(relations), batch_size):
            batch_relations = relations[i:i+batch_size]
            batch_contexts = contexts[i:i+batch_size]

            batch_results = self._classify_batch_transformer(batch_relations, batch_contexts)
            results.extend(batch_results)

        return results

    def _classify_batch_transformer(self, relations: List[str], contexts: List[str]) -> List[ClassificationResult]:
        """Batch classification using transformer optimization"""

        # Prepare batch inputs
        batch_texts = [self._prepare_input_text(rel, ctx) for rel, ctx in zip(relations, contexts)]

        # Batch tokenize
        inputs = self.tokenizer(
            batch_texts,
            return_tensors="pt",
            truncation=True,
            padding=True,
            max_length=self.expert_params.max_length
        ).to(self.device)

        # Batch inference
        self.model.eval()
        with torch.no_grad():
            outputs = self.model(**inputs)

        # Process batch results
        batch_results = []
        probabilities = F.softmax(outputs.logits, dim=1)

        for idx, (relation, context) in enumerate(zip(relations, contexts)):
            probs = probabilities[idx]
            predicted_class_id = torch.argmax(probs).item()
            confidence = probs[predicted_class_id].item()

            predicted_domain = self.id_to_label.get(predicted_class_id, "Uncategorized")

            # Get alternative domains
            prob_indices = torch.argsort(probs, descending=True)
            alternative_domains = [
                (self.id_to_label.get(prob_idx.item()), probs[prob_idx].item())
                for prob_idx in prob_indices[1:4] if prob_idx.item() in self.id_to_label
            ]

            result = ClassificationResult(
                relation_name=relation,
                primary_domain=predicted_domain,
                subdomain=self._get_subdomain(relation, predicted_domain),
                confidence=confidence,
                alternative_domains=alternative_domains,
                reasoning={'batch_processed': True, 'method': 'transformer'},
                feature_contributions={}
            )

            batch_results.append(result)
            self._update_performance_stats(result)

        return batch_results

    def _prepare_input_text(self, relation: str, context: str = "") -> str:
        """Prepare input text for BGE model"""
        if context and self.expert_params.use_context_window:
            context_window = context[:self.expert_params.context_window_size]
            return f"{relation} [SEP] {context_window}"
        else:
            return relation

    def _process_prediction(self, outputs, relation: str, context: str = "") -> ClassificationResult:
        """Process model outputs into classification result"""

        # Get predictions
        probabilities = F.softmax(outputs.logits[0], dim=0)
        predicted_class_id = torch.argmax(probabilities).item()
        confidence = probabilities[predicted_class_id].item()

        # Get predicted domain with domain boosting
        predicted_domain = self.id_to_label.get(predicted_class_id, "Uncategorized")

        # Apply domain-specific boosting for accuracy focus
        confidence = self._apply_domain_boosting(confidence, predicted_domain)

        # Get alternative domains
        prob_indices = torch.argsort(probabilities, descending=True)
        alternative_domains = [
            (self.id_to_label.get(idx.item()), probabilities[idx].item())
            for idx in prob_indices[1:4] if idx.item() in self.id_to_label
        ]

        # Determine subdomain
        subdomain = self._get_subdomain(relation, predicted_domain)

        # Generate reasoning with BGE-specific details
        reasoning = {
            'model_type': 'BAAI_BGE_Reranker',
            'input_length': len(self._prepare_input_text(relation, context)),
            'context_used': bool(context),
            'prediction_method': 'softmax_classifier',
            'domain_boosting_applied': self._get_boosting_info(predicted_domain)
        }

        # Feature contributions (simplified for BGE)
        feature_contributions = {
            'relation_semantic_score': confidence,
            'context_relevance_boost': float(bool(context)),
            'domain_confidence_boost': self._calculate_domain_boost(predicted_domain),
            'bge_ranking_score': probabilities[predicted_class_id].item()
        }

        processing_details = {
            'model_used': self.model_name,
            'quantization_active': self.expert_params.quantization,
            'mixed_precision': self.expert_params.mixed_precision,
            'inference_optimized': self.expert_params.batch_inference
        }

        return ClassificationResult(
            relation_name=relation,
            primary_domain=predicted_domain,
            subdomain=subdomain,
            confidence=min(confidence, 1.0),  # Clamp to [0,1]
            alternative_domains=alternative_domains,
            reasoning=reasoning,
            feature_contributions=feature_contributions,
            processing_details=processing_details
        )

    def _apply_domain_boosting(self, confidence: float, domain: str) -> float:
        """Apply domain-specific confidence boosting"""
        boost = 1.0

        if domain.lower().startswith('traceability'):
            boost = self.expert_params.sysml_boost  # Typical MBSE boosting
        elif domain.lower().startswith('structural'):
            boost = 1.1  # Moderate boost for structural relations
        elif domain.lower().startswith('behavioral'):
            boost = 1.0  # No boost for behavioral

        return min(confidence * boost, 1.0)

    def _get_boosting_info(self, domain: str) -> Dict[str, Any]:
        """Get information about applied boosting"""
        boost_value = self._apply_domain_boosting(1.0, domain)
        return {
            'boost_applied': boost_value > 1.0,
            'boost_factor': boost_value,
            'boost_type': 'domain_specific'
        }

    def _calculate_domain_boost(self, domain: str) -> float:
        """Calculate boost factor for feature contributions"""
        boost = self._apply_domain_boosting(1.0, domain)
        return boost - 1.0  # Return additional boost percentage

    def train(self, training_data, training_parameters: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Train BGE classifier on MBSE relation data"""

        if not self.is_initialized:
            return {'error': 'Classifier not initialized'}

        training_params = training_parameters or {}
        override_params = {
            'learning_rate': training_params.get('learning_rate', self.expert_params.learning_rate),
            'batch_size': training_params.get('batch_size', self.expert_params.batch_size),
            'num_epochs': training_params.get('num_epochs', self.expert_params.num_epochs),
            'max_length': training_params.get('max_length', self.expert_params.max_length),
            'warmup_steps': training_params.get('warmup_steps', self.expert_params.warmup_steps),
            'validation_split': training_params.get('validation_split', self.expert_params.validation_split)
        }

        try:
            self.logger.info("Starting BGE classifier training with expert parameters...")

            # Prepare MBSE-specific training data
            if not isinstance(training_data, pd.DataFrame):
                return {'error': 'Training data must be pandas DataFrame with relation_name and domain columns'}

            processed_data = self._prepare_training_data(training_data, override_params)
            if not processed_data:
                return {'error': 'Failed to process training data'}

            # Train the model
            training_result = self._train_bge_model(processed_data, override_params)

            if training_result.get('success'):
                self.is_trained = True
                self.logger.info("BGE classifier training completed successfully")

            return training_result

        except Exception as e:
            error_msg = f"BGE training failed: {e}"
            self.logger.error(error_msg)
            return {'error': error_msg, 'success': False}

    def _prepare_training_data(self, training_data: pd.DataFrame, params: Dict) -> Optional[Dict]:
        """Prepare MBSE training data for BGE fine-tuning"""

        try:
            # Validate data
            required_cols = ['relation_name', 'domain']
            if not all(col in training_data.columns for col in required_cols):
                self.logger.error(f"Training data missing required columns: {required_cols}")
                return None

            # Filter and clean data
            data = training_data.copy()
            data['relation_name'] = data['relation_name'].astype(str).str.strip()
            data['domain'] = data['domain'].astype(str).str.strip()

            # Remove invalid entries
            data = data[data['relation_name'].str.len() > 0]
            data = data[data['domain'].str.len() > 0]

            if len(data) == 0:
                self.logger.error("No valid training data after cleaning")
                return None

            # Prepare texts and labels
            train_texts = []
            train_labels = []
            val_texts = []
            val_labels = []

            for idx, row in data.iterrows():
                if row.get('context'):
                    text = f"{row['relation_name']} [SEP] {row['context'][:self.expert_params.context_window_size]}"
                else:
                    text = row['relation_name']

                label = self.label_to_id.get(row['domain'])

                if label is not None:
                    # Apply validation split
                    if np.random.random() < params['validation_split']:
                        val_texts.append(text)
                        val_labels.append(label)
                    else:
                        train_texts.append(text)
                        train_labels.append(label)

            if len(train_texts) == 0:
                self.logger.error("No training samples after label mapping")
                return None

            # Create datasets
            train_encodings = self.tokenizer(
                train_texts,
                truncation=True,
                padding=True,
                max_length=params['max_length']
            )

            val_encodings = self.tokenizer(
                val_texts,
                truncation=True,
                padding=True,
                max_length=params['max_length']
            ) if val_texts else None

            train_dataset = RelationDataset(train_encodings, train_labels)
            val_dataset = RelationDataset(val_encodings, val_labels) if val_encodings else None

            return {
                'train_dataset': train_dataset,
                'val_dataset': val_dataset,
                'num_train_samples': len(train_texts),
                'num_val_samples': len(val_texts) if val_texts else 0,
                'unique_domains': len(set(train_labels + val_labels)) if val_labels else len(set(train_labels))
            }

        except Exception as e:
            self.logger.error(f"Training data preparation failed: {e}")
            return None

    def _train_bge_model(self, data: Dict, params: Dict) -> Dict[str, Any]:
        """Execute BGE fine-tuning training"""

        try:
            # Setup training arguments
            training_args = TrainingArguments(
                output_dir='./results/bge_training',
                num_train_epochs=params['num_epochs'],
                per_device_train_batch_size=params['batch_size'],
                per_device_eval_batch_size=params['batch_size'],
                learning_rate=params['learning_rate'],
                warmup_steps=params['warmup_steps'],
                weight_decay=0.01,
                logging_dir='./logs/bge_training',
                logging_steps=10,
                evaluation_strategy="epoch" if data['val_dataset'] else "no",
                save_strategy="epoch",
                load_best_model_at_end=bool(data['val_dataset']),
                metric_for_best_model="f1",
                greater_is_better=True,
                fp16=self.expert_params.mixed_precision and self.device.type == 'cuda',
                dataloader_pin_memory=False,  # Compatibility
            )

            # Setup trainer
            trainer = Trainer(
                model=self.model,
                args=training_args,
                train_dataset=data['train_dataset'],
                eval_dataset=data['val_dataset'],
                compute_metrics=self._compute_bge_metrics
            )

            # Execute training
            train_result = trainer.train()

            # Gather results
            result = {
                'success': True,
                'training_time': train_result.metrics.get('train_runtime', 0),
                'final_loss': train_result.metrics.get('train_loss', 0),
                'num_train_samples': data['num_train_samples'],
                'num_val_samples': data['num_val_samples'],
                'unique_domains': data['unique_domains'],
                'model_type': 'BAAI_BGE_Reranker_Finetuned'
            }

            # Add validation results if available
            if data['val_dataset'] and hasattr(trainer, 'evaluate'):
                eval_results = trainer.evaluate()
                result.update({
                    'eval_accuracy': eval_results.get('eval_accuracy', 0),
                    'eval_f1': eval_results.get('eval_f1', 0),
                })

            return result

        except Exception as e:
            self.logger.error(f"BGE training execution failed: {e}")
            return {'error': str(e), 'success': False}

    def _compute_bge_metrics(self, eval_pred):
        """Compute metrics for BGE training evaluation"""
        try:
            predictions, labels = eval_pred
            predictions = np.argmax(predictions, axis=1)

            # Simple accuracy for now (can expand with sklearn metrics)
            accuracy = np.mean(predictions == labels)
            f1 = accuracy  # Placeholder - can implement proper F1

            return {
                'accuracy': accuracy,
                'f1': f1
            }
        except Exception as e:
            self.logger.error(f"Metrics computation failed: {e}")
            return {'accuracy': 0.0, 'f1': 0.0}

    def get_expert_parameters_template(self) -> Dict[str, Any]:
        """Get BGE-specific expert parameter tuning template"""

        return {
            "performance_tuning": {
                "learning_rate": {
                    "description": "Learning rate for fine-tuning BGE model",
                    "range": [1e-5, 5e-4],
                    "recommended": [2e-5, 3e-5, 5e-5],
                    "current": self.expert_params.learning_rate
                },
                "num_epochs": {
                    "description": "Training epochs for MBSE domain adaptation",
                    "range": [2, 10],
                    "recommended": [3, 5, 7],
                    "current": self.expert_params.num_epochs
                },
                "batch_size": {
                    "description": "Batch size for BGE training",
                    "range": [4, 32],
                    "recommended": [8, 16],
                    "current": self.expert_params.batch_size
                },
                "warmup_steps": {
                    "description": "Warmup steps for stable training",
                    "range": [100, 1000],
                    "recommended": [200, 500],
                    "current": self.expert_params.warmup_steps
                }
            },
            "inference_optimization": {
                "max_length": {
                    "description": "Maximum token length for BGE processing",
                    "range": [256, 1024],
                    "recommended": [384, 512],
                    "current": self.expert_params.max_length
                },
                "batch_inference": {
                    "description": "Enable optimized batch inference",
                    "options": [True, False],
                    "recommended": True,
                    "current": self.expert_params.batch_inference
                },
                "inference_batch_size": {
                    "description": "Batch size for inference throughput",
                    "range": [8, 64],
                    "recommended": [16, 32],
                    "current": self.expert_params.inference_batch_size
                },
                "quantization": {
                    "description": "Enable dynamic quantization for CPU inference",
                    "options": [True, False],
                    "recommended": True,
                    "current": self.expert_params.quantization
                }
            },
            "domain_optimization": {
                "sysml_boost": {
                    "description": "Boost confidence for SysML-specific relations",
                    "range": [1.0, 2.0],
                    "recommended": [1.2, 1.3, 1.4],
                    "current": self.expert_params.sysml_boost
                },
                "uml_boost": {
                    "description": "Boost confidence for UML-specific relations",
                    "range": [1.0, 2.0],
                    "recommended": [1.05, 1.1],
                    "current": self.expert_params.uml_boost
                },
                "context_window_size": {
                    "description": "Context window size for relation understanding",
                    "range": [100, 1000],
                    "recommended": [200, 300, 400],
                    "current": self.expert_params.context_window_size
                },
                "use_context_window": {
                    "description": "Include surrounding context in classification",
                    "options": [True, False],
                    "recommended": True,
                    "current": self.expert_params.use_context_window
                }
            },
            "training_enhancements": {
                "use_data_augmentation": {
                    "description": "Enable automatic training data augmentation",
                    "options": [True, False],
                    "recommended": True,
                    "current": self.expert_params.use_data_augmentation
                },
                "augmentation_factor": {
                    "description": "Multiplier for augmented training samples",
                    "range": [1.0, 3.0],
                    "recommended": [1.5, 2.0],
                    "current": self.expert_params.augmentation_factor
                },
                "validation_split": {
                    "description": "Portion of data used for validation",
                    "range": [0.1, 0.3],
                    "recommended": [0.15, 0.2],
                    "current": self.expert_params.validation_split
                }
            },
            "specific_parameters": {
                "mixed_precision": {
                    "description": "Use FP16 mixed precision for GPU training/inference",
                    "options": [True, False],
                    "recommended": True if torch.cuda.is_available() else False,
                    "current": self.expert_params.mixed_precision
                },
                "bge_model_variant": {
                    "description": "BGE model variant to use",
                    "options": ["BAAI/bge-reranker-v2-m3", "BAAI/bge-reranker-base"],
                    "recommended": "BAAI/bge-reranker-v2-m3",
                    "current": self.model_name
                }
            }
        }

    def _get_subdomain(self, relation: str, primary_domain: str) -> str:
        """Determine subdomain for a relation within primary domain"""
        relation_lower = relation.lower()

        domain_config = self.taxonomy.get(primary_domain, {})
        subdomains = domain_config.get("subdomains", {})

        for subdomain, sub_config in subdomains.items():
            keywords = sub_config.get("keywords", [])
            if any(keyword in relation_lower for keyword in keywords):
                return subdomain

        return "general"
