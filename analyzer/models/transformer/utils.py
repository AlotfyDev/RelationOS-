#!/usr/bin/env python3
"""
Transformer Classifier Utilities
Common utility functions for text preprocessing, validation, and data handling
"""

import json
import logging
import re
from pathlib import Path
from typing import Dict, List, Tuple, Any, Optional, Union

from .types import ExpertParameters

def parameter_validator(params: ExpertParameters) -> List[str]:
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
    if not 0 <= params.context_window_size <= 1000:
        errors.append(f"context_window_size must be <= 1000, got {params.context_window_size}")

    # Domain boost validation
    for boost_name, boost_value in [("sysml_boost", params.sysml_boost), ("uml_boost", params.uml_boost)]:
        if not 1.0 <= boost_value <= 3.0:
            errors.append(f"{boost_name} must be between 1.0 and 3.0, got {boost_value}")

    return errors

def preprocess_text(text: str) -> str:
    """Basic text preprocessing for relation classification"""
    if not text or not isinstance(text, str):
        return ""

    # Convert to lowercase for consistent processing
    processed = text.lower().strip()

    # Remove excessive whitespace
    processed = re.sub(r'\s+', ' ', processed)

    # Remove special characters that might confuse ML models
    processed = re.sub(r'[^\w\s\-_]', '', processed)

    return processed.strip()

def postprocess_result(result: Dict[str, Any]) -> Dict[str, Any]:
    """Post-process classification result for consistency"""
    if not isinstance(result, dict):
        return {"error": "Invalid result format"}

    # Ensure confidence is within bounds
    if 'confidence' in result:
        result['confidence'] = max(0.0, min(1.0, result['confidence']))

    # Add processing timestamp if not present
    if 'processed_at' not in result:
        from datetime import datetime
        result['processed_at'] = datetime.utcnow().isoformat()

    # Validate reasoning structure
    if 'reasoning' not in result:
        result['reasoning'] = {'method': 'unknown'}

    return result

def load_json_config(filepath: Union[str, Path], default: Optional[Dict] = None) -> Dict[str, Any]:
    """Safely load JSON configuration with fallback"""
    try:
        with open(filepath, 'r') as f:
            config = json.load(f)
        return config
    except Exception as e:
        logging.warning(f"Failed to load config from {filepath}: {e}")
        return default or {}

def save_json_config(config: Dict[str, Any], filepath: Union[str, Path]) -> bool:
    """Safely save JSON configuration"""
    try:
        filepath = Path(filepath)
        filepath.parent.mkdir(parents=True, exist_ok=True)

        with open(filepath, 'w') as f:
            json.dump(config, f, indent=2, default=str)

        return True
    except Exception as e:
        logging.error(f"Failed to save config to {filepath}: {e}")
        return False

def merge_configs(base: Dict[str, Any], override: Dict[str, Any]) -> Dict[str, Any]:
    """Deep merge two configuration dictionaries"""
    merged = base.copy()

    for key, value in override.items():
        if isinstance(value, dict) and key in merged and isinstance(merged[key], dict):
            merged[key] = merge_configs(merged[key], value)
        else:
            merged[key] = value

    return merged

def get_project_root(fallback_paths: Optional[List[Path]] = None) -> Path:
    """Find project root directory with fallback detection"""
    candidates = [
        Path(__file__).parent.parent.parent,  # Go up from utils.py to RelationOS/
        Path.cwd(),
    ]

    if fallback_paths:
        candidates.extend(fallback_paths)

    # Add common fallback paths
    from pathlib import Path
    home = Path.home()
    candidates.extend([
        home / "RelationOS",
        home / "projects" / "RelationOS",
        home / "Desktop" / "RelationOS",
    ])

    for candidate in candidates:
        if candidate.exists() and (candidate / "README.md").exists():
            return candidate

    # Final fallback to current directory
    return Path.cwd()

def setup_logging(log_level: str = "INFO", log_file: Optional[str] = None) -> logging.Logger:
    """Configure logging for transformer classifier"""
    logger = logging.getLogger("RelationOS.Transformer")

    # Clear existing handlers to avoid duplicates
    logger.handlers.clear()

    logger.setLevel(getattr(logging, log_level.upper(), logging.INFO))

    # Console handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.DEBUG)
    console_formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    console_handler.setFormatter(console_formatter)

    # File handler if specified
    if log_file:
        try:
            file_handler = logging.FileHandler(log_file)
            file_handler.setLevel(logging.DEBUG)
            file_handler.setFormatter(console_formatter)
            logger.addHandler(file_handler)
        except Exception as e:
            print(f"Failed to create log file: {e}")

    logger.addHandler(console_handler)
    return logger

def calculate_text_similarity(text1: str, text2: str) -> float:
    """Calculate simple text similarity score"""
    if not text1 or not text2:
        return 0.0

    # Simple Jaccard similarity on words
    words1 = set(preprocess_text(text1).split())
    words2 = set(preprocess_text(text2).split())

    if not words1 or not words2:
        return 0.0

    intersection = len(words1.intersection(words2))
    union = len(words1.union(words2))

    return intersection / union if union > 0 else 0.0

def batch_process_texts(texts: List[str],
                       batch_size: int = 32,
                       processor_func=None) -> List[Any]:
    """Process texts in batches for memory efficiency"""
    if not processor_func:
        processor_func = lambda x: x  # Identity function

    results = []
    for i in range(0, len(texts), batch_size):
        batch = texts[i:i+batch_size]
        batch_results = [processor_func(text) for text in batch]
        results.extend(batch_results)

    return results

def format_classification_summary(results: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Generate summary statistics from classification results"""
    if not results:
        return {"error": "No results to summarize"}

    total_results = len(results)
    high_confidence = sum(1 for r in results if r.get('confidence', 0) > 0.8)
    low_confidence = sum(1 for r in results if r.get('confidence', 0) < 0.5)

    # Domain distribution
    domains = {}
    for result in results:
        domain = result.get('primary_domain', 'unknown')
        domains[domain] = domains.get(domain, 0) + 1

    # Average confidence by domain
    domain_confidence = {}
    for domain in domains.keys():
        domain_results = [r for r in results if r.get('primary_domain') == domain]
        if domain_results:
            avg_confidence = sum(r.get('confidence', 0) for r in domain_results) / len(domain_results)
            domain_confidence[domain] = round(avg_confidence, 3)

    return {
        "total_classifications": total_results,
        "high_confidence_ratio": high_confidence / total_results if total_results > 0 else 0,
        "low_confidence_ratio": low_confidence / total_results if total_results > 0 else 0,
        "domain_distribution": domains,
        "average_confidence_by_domain": domain_confidence,
        "overall_average_confidence": sum(r.get('confidence', 0) for r in results) / total_results if total_results > 0 else 0
    }

def get_system_info() -> Dict[str, Any]:
    """Get information about the current system for troubleshooting"""
    try:
        import sys
        import platform
        import torch

        return {
            "python_version": sys.version,
            "platform": platform.platform(),
            "architecture": platform.machine(),
            "torch_available": hasattr(torch, 'cuda') and torch.cuda.is_available(),
            "cuda_version": torch.version.cuda if hasattr(torch, 'version') and torch.version.cuda else "N/A",
            "gpu_count": torch.cuda.device_count() if torch.cuda.is_available() else 0,
            "cpu_count": platform.processor() or "Unknown",
        }
    except Exception as e:
        return {"error": f"Failed to get system info: {e}"}

def create_error_result(error_message: str,
                       relation_name: str = "",
                       additional_context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """Create standardized error result"""
    result = {
        "relation_name": relation_name,
        "primary_domain": "Uncategorized",
        "subdomain": "error",
        "confidence": 0.0,
        "alternative_domains": [],
        "reasoning": {
            "error": True,
            "error_message": error_message
        },
        "feature_contributions": {},
        "processing_details": {}
    }

    if additional_context:
        result["reasoning"].update(additional_context)

    return result
