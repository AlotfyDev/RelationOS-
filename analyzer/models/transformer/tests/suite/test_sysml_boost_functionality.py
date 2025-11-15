#!/usr/bin/env python3
"""
Single Functionality Test: SysML Boost Validation
Tests that sysml_boost parameter actually increases confidence for MBSE relations
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from transformer import ExpertParameters, RuleBasedClassifier

def test_sysml_boost_increases_mbse_relation_confidence():
    """Verify sysml_boost=1.5 significantly increases confidence for traceability relations"""
    # Arrange
    base_params = ExpertParameters(sysml_boost=1.0)
    boosted_params = ExpertParameters(sysml_boost=1.5)

    base_classifier = RuleBasedClassifier(expert_params=base_params)
    boosted_classifier = RuleBasedClassifier(expert_params=boosted_params)

    assert base_classifier.initialize()
    assert boosted_classifier.initialize()

    # Act - Use clearly MBSE traceability relation
    relation = "satisfies system requirement"
    context = "According to the traceability matrix section 5.2"

    base_result = base_classifier.classify_relation(relation, context)
    boosted_result = boosted_classifier.classify_relation(relation, context)

    # Assert - sysml_boost should produce measurable confidence increase
    confidence_increase = boosted_result.confidence - base_result.confidence
    assert confidence_increase > 0.05, \
        f"sysml_boost should increase confidence: {base_result.confidence} → {boosted_result.confidence}"

    # Verify boost factor (should be approximately 1.5x the base scoring)
    boost_ratio = boosted_result.confidence / base_result.confidence if base_result.confidence > 0 else 1.0
    assert boost_ratio > 1.1, f"Confidence boost should be at least 10%: ratio = {boost_ratio}"

    # Verify confidence remains valid
    assert 0.0 <= boosted_result.confidence <= 1.0, \
        f"Confidence must be in [0,1]: got {boosted_result.confidence}"

def run_test():
    """Run this specific functionality test"""
    try:
        test_sysml_boost_increases_mbse_relation_confidence()
        print("✅ PASS: SysML boost significantly increases confidence for MBSE relations")
        print("   - Base confidence with sysml_boost=1.0: Calculated baseline")
        print("   - Boosted confidence with sysml_boost=1.5: Measurable increase")
        print("   - Confidence bounds maintained: Valid [0.0, 1.0] range")
        return True
    except Exception as e:
        print(f"❌ FAIL: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = run_test()
    sys.exit(0 if success else 1)
