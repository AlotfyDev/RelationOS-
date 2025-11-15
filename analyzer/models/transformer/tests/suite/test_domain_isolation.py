#!/usr/bin/env python3
"""
Single Functionality Test: Domain Isolation
Tests that domain boosting is properly isolated and doesn't affect unrelated domains
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from transformer import ExpertParameters, RuleBasedClassifier

def test_sysml_boost_spares_non_traceability_domains():
    """Verify sysml_boost doesn't significantly affect non-traceability relations"""
    # Arrange
    base_params = ExpertParameters(sysml_boost=1.0)
    boosted_params = ExpertParameters(sysml_boost=1.5)  # 50% boost for SysML

    base_classifier = RuleBasedClassifier(expert_params=base_params)
    boosted_classifier = RuleBasedClassifier(expert_params=boosted_params)

    assert base_classifier.initialize()
    assert boosted_classifier.initialize()

    # Act - Use clearly NON-MSysingle resource allocation relation
    relation = "allocates system resource"
    context = "Resource allocation specification section 3.1"

    base_result = base_classifier.classify_relation(relation, context)
    boosted_result = boosted_classifier.classify_relation(relation, context)

    # Assert - Confidence difference should be minimal for non-SysML relations
    confidence_diff = abs(boosted_result.confidence - base_result.confidence)

    # Non-traceability relations should not be significantly affected by sysml_boost
    # Allow small differences due to algorithmic factors, but nothing major
    assert confidence_diff < 0.10, \
        f"Non-traceability relation should not be heavily affected by sysml_boost: diff = {confidence_diff}"

    # The result domain should also remain consistent (both should classify as similar domains)
    assert base_result.primary_domain == boosted_result.primary_domain, \
        f"Domain classification should be consistent: {base_result.primary_domain} vs {boosted_result.primary_domain}"

def run_test():
    """Run this specific functionality test"""
    try:
        test_sysml_boost_spares_non_traceability_domains()
        print("✅ PASS: SysML boost properly isolates non-traceability domains")
        print("   - Resource allocation relation unaffected by sysml_boost")
        print("   - Domain classification remains consistent")
        print("   - Confidence difference within acceptable bounds (<0.10)")
        return True
    except Exception as e:
        print(f"❌ FAIL: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = run_test()
    sys.exit(0 if success else 1)
