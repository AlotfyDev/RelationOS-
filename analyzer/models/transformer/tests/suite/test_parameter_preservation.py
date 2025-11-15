#!/usr/bin/env python3
"""
Single Functionality Test: Parameter Preservation
Tests that expert parameters are properly stored and accessible for future use
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from transformer import ExpertParameters, RuleBasedClassifier

def test_expert_parameters_persist_across_calls():
    """Verify expert parameters maintain their values across multiple classification calls"""
    # Arrange - Custom parameter values
    custom_params = ExpertParameters(
        learning_rate=2.5e-5,
        batch_size=12,
        num_epochs=7,
        max_length=384,
        sysml_boost=1.8
    )

    classifier = RuleBasedClassifier(expert_params=custom_params)
    assert classifier.initialize()

    # Act - Make multiple classification calls
    test_cases = [
        ("satisfies requirement", "SysML context"),
        ("verifies compliance", "Verification context"),
        ("allocates resource", "Allocation context")
    ]

    for relation, context in test_cases:
        result = classifier.classify_relation(relation, context)
        # Verify each result is valid (but our focus is parameter preservation)
        assert 0.0 <= result.confidence <= 1.0

    # Assert - Parameters should maintain their custom values
    params = classifier.expert_params

    assert abs(params.learning_rate - 2.5e-5) < 1e-10, \
        f"learning_rate should be preserved: expected 2.5e-5, got {params.learning_rate}"

    assert params.batch_size == 12, \
        f"batch_size should be preserved: expected 12, got {params.batch_size}"

    assert params.num_epochs == 7, \
        f"num_epochs should be preserved: expected 7, got {params.num_epochs}"

    assert params.max_length == 384, \
        f"max_length should be preserved: expected 384, got {params.max_length}"

    assert abs(params.sysml_boost - 1.8) < 0.001, \
        f"sysml_boost should be preserved: expected 1.8, got {params.sysml_boost}"

def test_parameter_template_access():
    """Verify expert parameter templates provide meaningful tuning guidance"""
    classifier = RuleBasedClassifier()
    assert classifier.initialize()

    # Get parameter template
    template = classifier.get_expert_parameters_template()

    # Should have template structure
    assert isinstance(template, dict)
    assert len(template) > 0

    # Should include different tuning categories
    expected_categories = ["performance_tuning", "domain_optimization", "training_enhancements"]
    for category in expected_categories:
        assert category in template, f"Template should include '{category}' category"

    # Template values should include current classifier values
    if 'domain_optimization' in template and 'sysml_boost' in template['domain_optimization']:
        current_value = template['domain_optimization']['sysml_boost']['current']
        expected_value = classifier.expert_params.sysml_boost

        assert abs(current_value - expected_value) < 0.001, \
            f"Template should reflect current sysml_boost value: template={current_value}, actual={expected_value}"

def test_parameter_bounds_and_defaults():
    """Test that parameters work within expected bounds and handle edge values"""
    # Test default parameters
    default_classifier = RuleBasedClassifier()  # Should use default ExpertParameters()
    assert default_classifier.initialize()

    assert default_classifier.expert_params.sysml_boost == 1.2, \
        f"Default sysml_boost should be 1.2, got {default_classifier.expert_params.sysml_boost}"

    # Test explicit zero context window
    zero_context_params = ExpertParameters(context_window_size=0, use_context_window=False)
    zero_context_classifier = RuleBasedClassifier(expert_params=zero_context_params)
    assert zero_context_classifier.initialize()

    assert zero_context_classifier.expert_params.context_window_size == 0, \
        f"Zero context window should be preserved"

    assert zero_context_classifier.expert_params.use_context_window == False, \
        f"False use_context_window should be preserved"

def run_test():
    """Run this specific functionality test"""
    try:
        test_expert_parameters_persist_across_calls()
        test_parameter_template_access()
        test_parameter_bounds_and_defaults()

        print("✅ PASS: Expert parameters properly preserved and accessible")
        print("   - Custom parameter values maintained across multiple calls")
        print("   - Parameter templates provide accurate current values")
        print("   - Edge parameter values (like 0) handled correctly")
        print("   - Default parameters work as expected")
        return True
    except Exception as e:
        print(f"❌ FAIL: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = run_test()
    sys.exit(0 if success else 1)
