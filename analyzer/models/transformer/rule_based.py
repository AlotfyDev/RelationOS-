#!/usr/bin/env python3
"""
Rule-Based Classifier
Enhanced rule-based approach using domain taxonomy and keyword matching
Provides reliable fallback when ML models are unavailable
"""

import re
from typing import Dict, List, Tuple, Any, Optional
import logging

from .base_classifier import BaseClassifier, register_classifier
from .relation_types import *

@register_classifier("rules")
class RuleBasedClassifier(BaseClassifier):
    """
    Enhanced rule-based classifier using domain taxonomy and keyword patterns.
    Provides context-aware classification with configurable scoring and boosting.
    """

    def __init__(self,
                 mode: ClassificationMode = ClassificationMode.MODE_EXPRESS,
                 expert_params: Optional[ExpertParameters] = None,
                 config_path: Optional[str] = None):

        super().__init__(mode, expert_params, config_path)

        # Rule-based specific attributes
        self.model_name = "rule_based_enhanced"
        self.taxonomy = {}
        self.compiled_patterns = {}

        self.logger.info(f"Rule-Based Classifier initialized in {self.mode.value} mode")

    def initialize(self) -> bool:
        """Initialize rule-based classifier with taxonomy and patterns"""

        try:
            # Load domain taxonomy
            if not self._load_taxonomy():
                error_msg = "Failed to load domain taxonomy"
                self.initialization_errors.append(error_msg)
                return False

            # Compile regex patterns
            if not self._compile_patterns():
                error_msg = "Failed to compile patterns"
                self.initialization_errors.append(error_msg)
                return False

            self.is_initialized = True
            self.logger.info(f"Rule-Based classifier initialized with {len(self.taxonomy)} domains and {len(self.compiled_patterns)} patterns")
            return True

        except Exception as e:
            error_msg = f"Rule-Based initialization failed: {e}"
            self.logger.error(error_msg)
            self.initialization_errors.append(error_msg)
            return False

    def _load_taxonomy(self) -> bool:
        """Load domain taxonomy for rule-based classification"""
        try:
            with open("analyzer/config/domain_taxonomy.json", 'r') as f:
                config = json.load(f)

            self.taxonomy = config.get("primary_domains", {})
            patterns = config.get("patterns", {})
            self.compiled_patterns = {k: re.compile(v, re.IGNORECASE) for k, v in patterns.items()}

            self.logger.info(f"Loaded {len(self.taxonomy)} domain categories and {len(self.compiled_patterns)} patterns")
            return True

        except Exception as e:
            self.logger.error(f"Failed to load taxonomy: {e}")
            return False

    def _compile_patterns(self) -> bool:
        """Compile regex patterns from taxonomy"""
        try:
            # Compile primary domain patterns
            for domain_name, domain_config in self.taxonomy.items():
                subdomains = domain_config.get("subdomains", {})

                for sub_name, sub_config in subdomains.items():
                    keywords = sub_config.get("keywords", [])
                    patterns = sub_config.get("patterns", [])

                    # Compile keyword patterns (case-insensitive)
                    for keyword in keywords:
                        pattern_key = f"{domain_name}_{sub_name}_{keyword}"
                        try:
                            self.compiled_patterns[pattern_key] = re.compile(
                                rf'\b{re.escape(keyword)}\b',
                                re.IGNORECASE
                            )
                        except re.error:
                            pass  # Skip invalid patterns

                    # Compile regex patterns
                    for pattern in patterns:
                        pattern_key = f"{domain_name}_{sub_name}_pattern_{len(patterns)}"
                        try:
                            self.compiled_patterns[pattern_key] = re.compile(pattern, re.IGNORECASE)
                        except re.error:
                            pass  # Skip invalid patterns

            self.logger.debug(f"Compiled {len(self.compiled_patterns)} total patterns")
            return True

        except Exception as e:
            self.logger.error(f"Pattern compilation failed: {e}")
            return False

    def is_ready_for_inference(self) -> bool:
        """Check if rule-based classifier is ready for inference"""
        return self.is_initialized and bool(self.taxonomy) and bool(self.compiled_patterns)

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
                reasoning={"error": "Rule-Based classifier not ready for inference"},
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

            # Perform rule-based classification
            result = self._classify_with_rules(relation, context)
            self._update_performance_stats(result)

            return result

        except Exception as e:
            self.logger.error(f"Rule-based classification failed for '{relation}': {e}")
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
                reasoning={"error": "Rule-Based classifier not ready"},
                feature_contributions={}
            ) for rel in relations]

        # Process all relations at once (rule-based is fast)
        contexts = contexts or [''] * len(relations)
        results = []

        for relation, context in zip(relations, contexts):
            result = self.classify_relation(relation, context)
            results.append(result)

        return results

    def _classify_with_rules(self, relation: str, context: str = "") -> ClassificationResult:
        """Perform rule-based classification using patterns and taxonomy"""

        # Prepare full text for matching
        full_text = f"{relation} {context}".strip()
        relation_lower = relation.lower()
        context_lower = (context or "").lower()
        combined_text = f"{relation_lower} {context_lower}"

        # Score each domain based on keyword matches and patterns
        domain_scores = self._calculate_domain_scores(relation_lower, context_lower, combined_text)

        if not domain_scores:
            # No matches found
            return ClassificationResult(
                relation_name=relation,
                primary_domain="Uncategorized",
                subdomain="general",
                confidence=0.4,
                alternative_domains=[],
                reasoning={
                    'method': 'enhanced_rule_based',
                    'match_score': 0.0,
                    'context_analyzed': bool(context)
                },
                feature_contributions={
                    'keyword_matches': 0,
                    'pattern_matches': 0,
                    'context_boost_applied': False
                }
            )

        # Get best domain
        best_domain, best_score = max(domain_scores.items(), key=lambda x: x[1])

        # Calculate confidence with domain-specific boosting
        raw_confidence = min(best_score / 10.0, 0.95)  # Normalize score
        confidence = self._apply_domain_boosting(raw_confidence, best_domain)

        # Get alternative domains
        sorted_domains = sorted(domain_scores.items(), key=lambda x: x[1], reverse=True)
        alternative_domains = [
            (domain, score) for domain, score in sorted_domains[1:4] if score > 0
        ]

        # Determine subdomain
        subdomain = self._get_subdomain(relation, best_domain)

        # Detailed reasoning
        total_matches = sum(domain_scores.values())
        keyword_matches, pattern_matches = self._count_match_types(relation_lower, context_lower)

        reasoning = {
            'method': 'enhanced_rule_based',
            'domain_scores': domain_scores,
            'total_score': best_score,
            'total_matches': total_matches,
            'context_analyzed': bool(context),
            'confidence_calculation': 'score/10 with domain boosting'
        }

        # Feature contributions
        feature_contributions = {
            'keyword_matches': keyword_matches,
            'pattern_matches': pattern_matches,
            'domain_specific_matches': len([d for d, s in domain_scores.items() if s > 0]),
            'context_boost_applied': bool(context) and self.expert_params.use_context_window,
            'domain_boost_applied': confidence > raw_confidence
        }

        processing_details = {
            'model_used': self.model_name,
            'pattern_count': len(self.compiled_patterns),
            'domain_count': len(self.taxonomy),
            'rule_based_confidence': raw_confidence,
            'final_confidence': confidence
        }

        return ClassificationResult(
            relation_name=relation,
            primary_domain=best_domain,
            subdomain=subdomain,
            confidence=confidence,
            alternative_domains=alternative_domains,
            reasoning=reasoning,
            feature_contributions=feature_contributions,
            processing_details=processing_details
        )

    def _calculate_domain_scores(self, relation_lower: str, context_lower: str, combined_text: str) -> Dict[str, float]:
        """Calculate scores for each domain based on keyword and pattern matches"""

        domain_scores = {}

        for domain_name, domain_config in self.taxonomy.items():
            score = 0.0
            subdomains = domain_config.get("subdomains", {})

            for sub_name, sub_config in subdomains.items():
                keywords = sub_config.get("keywords", [])
                patterns = sub_config.get("patterns", [])

                # Score keywords (with context weighting)
                for keyword in keywords:
                    keyword_lower = keyword.lower()

                    # Check in relation and context separately
                    rel_match = keyword_lower in relation_lower
                    ctx_match = context_lower and keyword_lower in context_lower

                    if rel_match or ctx_match:
                        # Keywords in relation are more important
                        base_score = 2.0 if rel_match else 1.0

                        # Context boost if applicable
                        if ctx_match and self.expert_params.use_context_window:
                            base_score *= 1.2  # Context boost

                        score += base_score

                # Score patterns
                for pattern in patterns:
                    try:
                        if re.search(pattern, combined_text, re.IGNORECASE):
                            score += 3.0  # Patterns are more specific
                    except re.error:
                        pass  # Skip invalid patterns

            if score > 0:
                # Apply domain-specific boosting
                score = self._apply_domain_boosting_score(score, domain_name)
                domain_scores[domain_name] = score

        return domain_scores

    def _apply_domain_boosting_score(self, score: float, domain: str) -> float:
        """Apply domain-specific boosting to raw scores"""
        boost = 1.0

        domain_lower = domain.lower()
        if 'traceability' in domain_lower or 'requirement' in domain_lower:
            boost = self.expert_params.sysml_boost
        elif 'structural' in domain_lower or 'component' in domain_lower:
            boost = 1.1
        elif 'behavioral' in domain_lower or 'function' in domain_lower:
            boost = 1.05

        return score * boost

    def _count_match_types(self, relation_lower: str, context_lower: str) -> Tuple[int, int]:
        """Count keyword and pattern matches for feature contributions"""
        keyword_matches = 0
        pattern_matches = 0

        combined_text = f"{relation_lower} {context_lower}"

        for domain_name, domain_config in self.taxonomy.items():
            subdomains = domain_config.get("subdomains", {})

            for sub_name, sub_config in subdomains.items():
                keywords = sub_config.get("keywords", [])
                patterns = sub_config.get("patterns", [])

                # Count keyword matches
                for keyword in keywords:
                    if keyword.lower() in combined_text:
                        keyword_matches += 1

                # Count pattern matches
                for pattern in patterns:
                    try:
                        if re.search(pattern, combined_text, re.IGNORECASE):
                            pattern_matches += 1
                    except re.error:
                        pass

        return keyword_matches, pattern_matches

    def _apply_domain_boosting(self, confidence: float, domain: str) -> float:
        """Apply domain-specific confidence boosting"""
        score = confidence * 10  # Convert back to score
        boosted_score = self._apply_domain_boosting_score(score, domain)
        return min(boosted_score / 10, 1.0)  # Convert back to confidence

    def train(self, training_data, training_parameters: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Rule-based classifier training is pattern/configuration based - no traditional ML training"""

        if not self.is_initialized:
            return {'error': 'Classifier not initialized', 'success': False}

        # Rule-based doesn't require traditional training
        # Could potentially learn new patterns from labeled data
        return {
            'success': True,
            'message': 'Rule-based classifier uses static patterns - no training required',
            'model_type': 'rule_based',
            'patterns_loaded': len(self.compiled_patterns),
            'domains_configured': len(self.taxonomy)
        }

    def get_expert_parameters_template(self) -> Dict[str, Any]:
        """Get rule-based specific expert parameter tuning template"""

        return {
            "rule_customization": {
                "context_window_size": {
                    "description": "Context window size for pattern matching",
                    "range": [50, 500],
                    "recommended": [100, 200],
                    "current": self.expert_params.context_window_size
                },
                "use_context_window": {
                    "description": "Include context in pattern matching",
                    "options": [True, False],
                    "recommended": True,
                    "current": self.expert_params.use_context_window
                }
            },
            "domain_optimization": {
                "sysml_boost": {
                    "description": "Boost confidence for SysML-specific patterns",
                    "range": [1.0, 3.0],
                    "recommended": [1.2, 1.4, 1.6],
                    "current": self.expert_params.sysml_boost
                },
                "uml_boost": {
                    "description": "Boost confidence for UML-specific patterns",
                    "range": [1.0, 3.0],
                    "recommended": [1.0, 1.1],
                    "current": self.expert_params.uml_boost
                }
            },
            "pattern_matching": {
                "keyword_case_sensitive": {
                    "description": "Case-sensitive keyword matching",
                    "options": [True, False],
                    "recommended": False,
                    "current": False  # Always case-insensitive in this implementation
                },
                "pattern_scoring_weight": {
                    "description": "Relative weight for regex patterns vs keywords",
                    "range": [1.0, 5.0],
                    "recommended": [3.0, 4.0],
                    "current": 3.0  # Patterns worth 3x keywords
                }
            }
        }

    def _get_subdomain(self, relation: str, primary_domain: str) -> str:
        """Determine subdomain for rule-based classification"""
        relation_lower = relation.lower()

        domain_config = self.taxonomy.get(primary_domain, {})
        subdomains = domain_config.get("subdomains", {})

        for subdomain, sub_config in subdomains.items():
            keywords = sub_config.get("keywords", [])
            if any(keyword.lower() in relation_lower for keyword in keywords):
                return subdomain

        return "general"
