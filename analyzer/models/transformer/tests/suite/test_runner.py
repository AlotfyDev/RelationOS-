#!/usr/bin/env python3
"""
Granular Test Suite Runner
Run individual functionality tests to ensure they work independently
"""

import os
import sys
import glob
import subprocess
from pathlib import Path

def run_single_test(test_file):
    """Run a single test and return results"""
    try:
        print(f"\n🧪 Running {Path(test_file).name}...")

        # Run the test file directly
        result = subprocess.run([sys.executable, test_file],
                              capture_output=True,
                              text=True,
                              timeout=30)

        if result.returncode == 0:
            success = True
            print(f"✅ {Path(test_file).name} PASSED")
            # Don't print all output, just show it passed
        else:
            success = False
            print(f"❌ {Path(test_file).name} FAILED")
            print("STDOUT:", result.stdout)
            print("STDERR:", result.stderr)

        return success

    except subprocess.TimeoutExpired:
        print(f"⏱️ {Path(test_file).name} TIMED OUT (30s)")
        return False
    except Exception as e:
        print(f"💥 {Path(test_file).name} ERROR: {e}")
        return False

def discover_test_files(test_suite_dir):
    """Find all test files in the suite directory"""
    test_files = []
    pattern = os.path.join(test_suite_dir, "test_*.py")

    # Find all test files, excluding the runner itself
    for filepath in glob.glob(pattern):
        filename = os.path.basename(filepath)
        if filename != "test_runner.py":
            test_files.append(filepath)

    return sorted(test_files)  # Sort for consistent order

def run_all_tests(verbose=False):
    """Run the complete test suite"""
    test_suite_dir = os.path.dirname(os.path.abspath(__file__))

    print("🔬 Granular Test Suite Runner")
    print("=" * 50)

    test_files = discover_test_files(test_suite_dir)
    print(f"Found {len(test_files)} test files")

    passed = 0
    failed = 0
    total = len(test_files)

    for test_file in test_files:
        if run_single_test(test_file):
            passed += 1
        else:
            failed += 1

        # No verbose functionality needed - tests report their own results

    # Summary
    print("\n" + "=" * 50)
    print(f"🎯 TEST SUITE SUMMARY: {passed}/{total} tests passed")

    if failed > 0:
        print(f"❌ {failed} tests failed")
        return False
    else:
        print(f"🎉 ALL {total} functionality tests PASSED!")
        print("\nEach test validates specific functionality:")
        for test_file in test_files:
            with open(test_file, 'r') as f:
                content = f.read()
                lines = content.split('\n')
                for line in lines:
                    if line.strip().startswith('"""'):
                        next_line = lines[lines.index(line) + 1].strip()
                        if 'Test:' in next_line:
                            test_name = Path(test_file).name.replace('test_', '').replace('.py', '').replace('_', ' ')
                            description = next_line.replace('Single Functionality Test: ', '').replace('"""', '')
                            print(f"  • {test_name}: {description}")
                            break
        return True

def main():
    import argparse

    parser = argparse.ArgumentParser(description='Run granular functionality test suite')
    parser.add_argument('--verbose', '-v', action='store_true',
                       help='Show detailed output for each test')
    parser.add_argument('--list-only', '-l', action='store_true',
                       help='List test files without running them')

    args = parser.parse_args()

    test_suite_dir = os.path.dirname(os.path.abspath(__file__))

    if args.list_only:
        print("🔍 Available Tests:")
        test_files = discover_test_files(test_suite_dir)
        test_descriptions = {
            'test_sysml_boost_functionality.py': 'SysML Boost Validation',
            'test_domain_isolation.py': 'Domain Isolation',
            'test_confidence_bounds.py': 'Confidence Bounds Validation',
            'test_parameter_preservation.py': 'Parameter Preservation',
            'test_result_structure_completeness.py': 'Result Structure Completeness'
        }
        for test_file in test_files:
            filename = Path(test_file).name
            description = test_descriptions.get(filename, 'Unknown functionality')
            print(f"  • {filename} - {description}")
        return 0

    success = run_all_tests(args.verbose)
    return 0 if success else 1

if __name__ == "__main__":
    sys.exit(main())
