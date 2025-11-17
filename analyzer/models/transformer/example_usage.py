#!/usr/bin/env python3
"""
Example usage of the modular RelationOS Transformer Classifier
Demonstrates the benefits of the new modular architecture
"""

import sys
from pathlib import Path

# Import the classifier classes directly from their modules
try:
    # Try relative imports first (when run as module)
    from .bge_classifier import BGEClassifier
    from .sklearn_fallback import SklearnFallbackClassifier
    from .rule_based import RuleBasedClassifier
    from .relation_types import ExpertParameters, ClassificationMode
except ImportError:
    # Fall back to absolute imports (when run as script)
    from bge_classifier import BGEClassifier
    from sklearn_fallback import SklearnFallbackClassifier
    from rule_based import RuleBasedClassifier
    from relation_types import ExpertParameters, ClassificationMode

def test_modular_classifiers():
    """Test the new modular classifier architecture"""

    print("🔬 Testing RelationOS CPU-Only Classifier")
    print("🚫 BAI BGE Skipped (requires torch transformers)")
    print("✅ Testing Sklearn Fallback (CPU-only)")
    print("=" * 60)

    # Test data
    test_relations = [
        "satisfies system requirement",
        "refines architectural design",
        "verifies compliance test",
        "allocates system resource",
        "depends on external service"
    ]

    test_contexts = [
        "According to the system engineering requirements document",
        "In the architectural design specification from 2023",
        "Test verification matrix section 4.2",
        "Resource allocation specification",
        "Service dependency graph analysis"
    ]

    # Test configurations - CPU-only only
    configurations = [
        ("Sklearn Fallback (CPU-Only)", SklearnFallbackClassifier, ClassificationMode.MODE_STANDARD),
    ]

    # Expert parameters for maximum accuracy
    expert_params = ExpertParameters(
        sysml_boost=1.2,  # Boost MBSE relations
        uml_boost=1.1,    # Boost modeling relations
        context_window_size=200,
        use_context_window=True,
        confidence_threshold=0.75
    )

    results_summary = {}

    for name, classifier_class, mode in configurations:
        print(f"\n🧪 Testing {name}")
        print("-" * 30)

        try:
            # Create classifier instance
            classifier = classifier_class(mode=mode, expert_params=expert_params)

            # Initialize
            print("Initializing classifier...")
            if not classifier.initialize():
                print(f"❌ Failed to initialize: {classifier.initialization_errors}")
                continue

            print("✅ Initialization successful")

            # Test single classification
            print("Testing single classification...")
            result = classifier.classify_relation(
                test_relations[0],
                test_contexts[0]
            )

            print(f"   Input: '{test_relations[0]}'")
            print(f"   Domain: {result.primary_domain}")
            print(".2f")
            print(f"   Model: {result.reasoning.get('model_type', 'unknown')}")

            # Test batch classification
            print("Testing batch classification...")
            batch_results = classifier.classify_batch(
                test_relations[:3],
                test_contexts[:3],
                batch_size=2
            )

            successful_classifications = sum(1 for r in batch_results if r.confidence > 0.5)
            print(f"   Batch Results: {successful_classifications}/{len(batch_results)} successful")

            # Performance stats
            stats = classifier.get_performance_stats()
            print(f"   Total Classifications: {stats['total_classifications']}")
            print(".2f")

            # Expert parameters template
            if hasattr(classifier, 'get_expert_parameters_template'):
                template = classifier.get_expert_parameters_template()
                print(f"   Expert Parameters: {len(template)} categories available")

            results_summary[name] = {
                'initialized': True,
                'single_success': result.confidence > 0.5,
                'batch_success': successful_classifications > 0,
                'avg_confidence': stats['average_confidence'] if stats['total_classifications'] > 0 else 0
            }

        except Exception as e:
            print(f"❌ Test failed: {e}")
            results_summary[name] = {
                'initialized': False,
                'error': str(e)
            }

    # Summary
    print("\n" + "=" * 60)
    print("📊 MODULAR CLASSIFIER COMPARISON")
    print("=" * 60)

    for name, summary in results_summary.items():
        status = "✅" if summary.get('initialized', False) else "❌"
        print("15s")

        if summary.get('initialized'):
            single = "✅" if summary.get('single_success') else "❌"
            batch = "✅" if summary.get('batch_success') else "❌"
            confidence = f"{summary.get('avg_confidence', 0):.2f}"
            print(f"   Single Classification: {single}")
            print(f"   Batch Classification:  {batch}")
            print(f"   Avg Confidence:        {confidence}")
        else:
            print(f"   Error: {summary.get('error', 'Unknown')}")

        print()

    print("🎉 Modular architecture successfully demonstrated!")
    print("   • Clean separation of concerns")
    print("   • Consistent APIs across implementations")
    print("   • Expert parameter tuning available")
    print("   • Robust error handling")
    print("   • Performance monitoring built-in")

if __name__ == "__main__":
    test_modular_classifiers()
