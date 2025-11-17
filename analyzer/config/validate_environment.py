#!/usr/bin/env python3
"""
Environment Validation Script for Training Pipeline
Tests all required dependencies and provides setup guidance
"""

import sys
import os
from pathlib import Path
from typing import Dict, List, Tuple

def check_python_version() -> Tuple[bool, str]:
    """Check Python version compatibility"""
    version = sys.version_info
    if version.major >= 3 and version.minor >= 8:
        return True, f"Python {version.major}.{version.minor}.{version.micro} ✅"
    else:
        return False, f"Python {version.major}.{version.minor}.{version.micro} ❌ (requires ≥3.8)"

def check_core_dependencies() -> Dict[str, Tuple[bool, str, str]]:
    """Check core Python packages"""
    dependencies = {
        'pandas': {
            'required': True,
            'min_version': '1.5.0',
            'purpose': 'Data loading and manipulation',
            'install_cmd': 'pip install pandas'
        },
        'pyarrow': {
            'required': True, 
            'min_version': '10.0.0',
            'purpose': 'Parquet file support',
            'install_cmd': 'pip install pyarrow'
        },
        'sklearn': {
            'required': False,
            'min_version': '1.2.0',
            'purpose': 'Machine learning models',
            'install_cmd': 'pip install scikit-learn'
        },
        'torch': {
            'required': False,
            'min_version': '2.0.0',
            'purpose': 'Deep learning (optional)',
            'install_cmd': 'pip install torch'
        }
    }
    
    results = {}
    
    for package, info in dependencies.items():
        try:
            if package == 'sklearn':
                import sklearn
                module = sklearn
            elif package == 'torch':
                import torch
                module = torch
            else:
                module = __import__(package)
            
            version = getattr(module, '__version__', 'unknown')
            status = f"{package} {version} ✅"
            
            # Simple version check (could be more sophisticated)
            if info['required']:
                results[package] = (True, status, info['purpose'])
            else:
                results[package] = (True, status, info['purpose'])
                
        except ImportError:
            status = f"{package} ❌ MISSING"
            results[package] = (False, status, f"{info['purpose']} ({info['install_cmd']})")
    
    return results

def check_builtin_modules() -> Dict[str, bool]:
    """Check built-in Python modules"""
    builtins = {
        'json': 'Configuration file handling',
        'pathlib': 'Path handling',
        'typing': 'Type hints',
        'logging': 'Logging',
        'gzip': 'Compressed file support'
    }
    
    results = {}
    for module, purpose in builtins.items():
        try:
            __import__(module)
            results[module] = True
        except ImportError:
            results[module] = False
    
    return results

def check_project_files() -> Dict[str, bool]:
    """Check if required project files exist"""
    required_files = {
        'domain_taxonomy.json': 'MBSE domain definitions',
        'classifier_config.json': 'ML model configuration',
        'hardware_optimized_training.json': 'Hardware optimization config',
        'load_training_data.py': 'Data loading pipeline',
        'demo_production_ml_infrastructure.py': 'Infrastructure demo',
        'create_parquet_optimized.py': 'Parquet creation utility'
    }
    
    current_dir = Path('.')
    results = {}
    
    for file, purpose in required_files.items():
        results[file] = (current_dir / file).exists()
    
    return results

def generate_setup_commands(deps_status: Dict[str, Tuple[bool, str, str]]) -> List[str]:
    """Generate installation commands for missing dependencies"""
    commands = []
    
    for package, (installed, status, purpose) in deps_status.items():
        if not installed:
            if package == 'sklearn':
                commands.append('pip install scikit-learn')
            elif package == 'torch':
                commands.append('pip install torch')
            elif package == 'pyarrow':
                commands.append('pip install pyarrow')
            elif package == 'pandas':
                commands.append('pip install pandas')
    
    return commands

def main():
    """Main validation function"""
    print("🔍 TRAINING PIPELINE ENVIRONMENT VALIDATION")
    print("=" * 60)
    
    # Check Python version
    print("\n🐍 PYTHON VERSION:")
    py_ok, py_status = check_python_version()
    print(f"   {py_status}")
    
    # Check core dependencies
    print("\n📦 CORE DEPENDENCIES:")
    deps_status = check_core_dependencies()
    
    required_missing = []
    optional_missing = []
    
    for package, (installed, status, purpose) in deps_status.items():
        print(f"   {status} - {purpose}")
        if not installed:
            # Determine if required or optional
            if package in ['pandas', 'pyarrow']:
                required_missing.append(package)
            else:
                optional_missing.append(package)
    
    # Check built-in modules
    print("\n🔧 BUILT-IN MODULES:")
    builtins = check_builtin_modules()
    for module, available in builtins.items():
        status = "✅" if available else "❌"
        print(f"   {module} {status}")
    
    # Check project files
    print("\n📄 PROJECT FILES:")
    files = check_project_files()
    for file, exists in files.items():
        status = "✅" if exists else "❌"
        print(f"   {file} {status}")
    
    # Generate setup recommendations
    print("\n🛠️ SETUP RECOMMENDATIONS:")
    
    if required_missing:
        print("   REQUIRED PACKAGES (missing):")
        for package in required_missing:
            if package == 'pandas':
                print("   pip install pandas")
            elif package == 'pyarrow':
                print("   pip install pyarrow")
    
    if optional_missing:
        print("   OPTIONAL PACKAGES (for ML capabilities):")
        for package in optional_missing:
            if package == 'sklearn':
                print("   pip install scikit-learn")
            elif package == 'torch':
                print("   pip install torch")
    
    # Overall assessment
    print("\n🎯 ENVIRONMENT STATUS:")
    
    if py_ok and not required_missing:
        if not optional_missing:
            print("   ✅ FULLY READY - All dependencies installed")
            print("   🎉 TRAINING PIPELINE: OPERATIONAL")
        else:
            print("   ✅ CORE READY - Basic functionality available")
            print("   💡 Consider installing optional ML packages for enhanced capabilities")
    elif py_ok and required_missing:
        print("   ⚠️ PARTIAL - Install required packages for basic functionality")
        print(f"   📋 Missing required: {', '.join(required_missing)}")
    else:
        print("   ❌ NOT READY - Missing critical components")
    
    print("\n" + "=" * 60)
    print("For detailed setup instructions, see: ENVIRONMENT_SETUP.md")
    print("=" * 60)

if __name__ == "__main__":
    main()