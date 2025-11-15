#!/usr/bin/env python3
"""
Single Functionality Test: Result Structure Completeness
Tests that ClassificationResult structures are complete and properly typed
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from transformer import ExpertParameters, RuleBasedClassifier

def test_classification_result_complete_fields():
    """Verify all required fields in ClassificationResult are populated with correct types"""
    classifier = RuleBasedClassifier()
    assert classifier.initialize()

    # Test with typical MBSE relations that should produce complete results
    relation = "satisfies functional requirements"
    context = "Requirements traceability section 4.2 in the system specification document"

    result = classifier.classify_relation(relation, context)

    # Check all fields are present and properly typed
    required_fields = [
        ('confidence', float),
        ('primary_domain', str),
        ('secondary_domains', list),
        ('relationship_type', str),
        ('certainty_level', str),
        ('context_strength', float),
        ('reasoning', str),
        ('evidence_sources', list)
    ]

    for field_name, expected_type in required_fields:
        assert hasattr(result, field_name), f"Result missing required field '{field_name}'"
        field_value = getattr(result, field_name)
        assert isinstance(field_value, expected_type), \
            f"Field '{field_name}' has wrong type: expected {expected_type.__name__}, got {type(field_value).__name__}"

    # Check list fields contain appropriate types
    if isinstance(result.secondary_domains, list):
        for domain in result.secondary_domains:
            assert isinstance(domain, str), \
                f"secondary_domains should contain strings: got {type(domain)}"

    if isinstance(result.evidence_sources, list):
        for source in result.evidence_sources:
            assert isinstance(source, dict), \
                f"evidence_sources should contain dicts: got {type(source)}"

def test_result_values_make_sense():
    """Verify result field values are meaningful for strong relations"""
    classifier = RuleBasedClassifier()
    assert classifier.initialize()

    # Use clearly strong MBSE traceability relation
    relation = "satisfies system functional requirements"
    strong_context = "Requirements traceability matrix section 5.3 with functional allocation analysis"

    result = classifier.classify_relation(relation, strong_context)

    # Strong relations should have logical result values
    assert len(result.primary_domain) > 0, "Primary domain should not be empty for strong relations"
    assert result.confidence > 0.0, "Confidence should be positive for clear relations"
    assert len(result.reasoning) > 10, "Reasoning should be detailed for confidence calculations"

    # Domain should be related to MBSE
    assert 'traceability' in result.primary_domain.lower() or 'requirements' in result.primary_domain.lower(), \
        f"Primary domain should reflect traceability nature: got '{result.primary_domain}'"

    # Reasoning should mention the key terms
    reasoning_lower = result.reasoning.lower()
    assert any(keyword in reasoning_lower for keyword in ['satisfies', 'requirements', 'traceability', 'functional']), \
        f"Reasoning should refer to relation keywords: '{result.reasoning}'"

def test_result_consistency_across_calls():
    """Verify result structures are consistent across multiple calls"""
    classifier = RuleBasedClassifier()
    assert classifier.initialize()

    test_cases = [
        ("satisfies requirements", "General context"),
        ("allocates resources", "Allocation context"),
        ("interacts with", "Interaction context")
    ]

    results = []
    for relation, context in test_cases:
        result = classifier.classify_relation(relation, context)
        results.append(result)

    # All results should have same field types
    for i, result in enumerate(results):
        assert isinstance(result.confidence, float), f"Result {i} confidence not float"
        assert isinstance(result.primary_domain, str), f"Result {i} primary_domain not string"
        assert isinstance(result.secondary_domains, list), f"Result {i} secondary_domains not list"
        assert isinstance(result.reasoning, str), f"Result {i} reasoning not string"

def run_test():
    """Run this specific functionality test"""
    try:
        test_classification_result_complete_fields()
        test_result_values_make_sense()
        test_result_consistency_across_calls()

        print("✅ PASS: ClassificationResult structures are complete and properly typed")
        print("   - All required fields present with correct types")
        print("   - Result values make logical sense for strong relations")
        print("   - Field types consistent across multiple classification calls")
        print("   - List fields contain appropriately typed elements")
        return True
    except Exception as e:
        print(f"❌ FAIL: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = run_test()
    sys.exit(0 if success else 1)
