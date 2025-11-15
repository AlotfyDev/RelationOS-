#!/usr/bin/env python3
"""
Single Functionality Test: Confidence Bounds Validation
Tests that confidence scores are always mathematically valid [0.0, 1.0]
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from transformer import ExpertParameters, RuleBasedClassifier

def test_confidence_bounds_always_valid():
    """Verify all confidence scores are clamped to valid [0.0, 1.0] range"""
    # Arrange
    # Test with extreme boost values to potentially push confidence bounds
    extreme_params = ExpertParameters(
        sysml_boost=2.0,  # Double boost
        uml_boost=2.0,    # Double boost
        context_window_size=500
    )

    classifier = RuleBasedClassifier(expert_params=extreme_params)
    assert classifier.initialize()

    # Act - Test various relation types with different boost scenarios
    test_relations = [
        ("satisfies requirement", "System requirements document"),  # SysML boost
        ("interacts with", "UML interaction diagram"),            # UML boost
        ("allocates resource", "General context"),                # No specific boost
        ("xyz invalid relation", ""),                             # Nonsense input
    ]

    for relation, context in test_relations:
        result = classifier.classify_relation(relation, context)

        # Assert - Confidence must always be within valid bounds
        assert 0.0 <= result.confidence <= 1.0, \
            f"Confidence must be in [0.0, 1.0] for '{relation}': got {result.confidence}"

        # Also verify it's a float
        assert isinstance(result.confidence, float), \
            f"Confidence must be float type: got {type(result.confidence)}"

def test_extreme_boosting_confidence_bounds():
    """Test that extreme boosting values don't break confidence bounds"""
    # Arrange - Use maximum boost values
    max_boost_params = ExpertParameters(
        sysml_boost=3.0,  # Maximum allowed boost
        uml_boost=3.0,
        context_window_size=1000  # Large context window
    )

    classifier = RuleBasedClassifier(expert_params=max_boost_params)
    assert classifier.initialize()

    # Act - Test with high-scoring relation that will be boosted
    relation = "satisfies functional requirement"
    context = "Requirements traceability matrix with functional allocation analysis"

    result = classifier.classify_relation(relation, context)

    # Assert - Even with maximum boosting, confidence must remain bounded
    assert 0.0 <= result.confidence <= 1.0, \
        f"Even with extreme boosting, confidence must be in [0.0, 1.0]: got {result.confidence}"

    # The relation is clear and strong, so it should have meaningful confidence even with extreme boost
    assert result.confidence > 0.1, \
        f"Clear relation should have meaningful confidence even with extreme boosting: got {result.confidence}"

def test_zero_confidence_edge_case():
    """Test that zero-confidence inputs are handled properly"""
    # Arrange - Normal parameters
    classifier = RuleBasedClassifier()
    assert classifier.initialize()

    # Act - Test with inputs that should receive very low confidence
    edge_cases = [
        "xyz ",  # Gibberish single word
        "",      # Empty input
        "   ",   # Whitespace only
        "some random words that make no sense",  # Non-domain terms
    ]

    for relation in edge_cases:
        result = classifier.classify_relation(relation, "")

        # Assert - Even low-confidence cases must be properly bounded
        assert 0.0 <= result.confidence <= 1.0, \
            f"Zero-confidence edge case '{relation}' must still be in [0.0, 1.0]: got {result.confidence}"

        # Should still return valid result structure
        assert result.primary_domain != "", \
            f"Must have valid primary domain even for edge cases"

def run_test():
    """Run this specific functionality test"""
    try:
        test_confidence_bounds_always_valid()
        test_extreme_boosting_confidence_bounds()
        test_zero_confidence_edge_case()

        print("✅ PASS: Confidence bounds properly maintained in all scenarios")
        print("   - Normal classification: Confidence in [0.0, 1.0]")
        print("   - Extreme boosting: Confidence clamped to valid range")
        print("   - Edge cases: Zero-confidence inputs handled gracefully")
        print("   - Result structure: Always complete even for problematic inputs")
        return True
    except Exception as e:
        print(f"❌ FAIL: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = run_test()
    sys.exit(0 if success else 1)
