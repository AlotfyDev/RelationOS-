# Training Pipeline Environment Setup Guide

## 🎯 Quick Start Installation

### **CORE DEPENDENCIES (Required for Training Pipeline)**

```bash
# Essential Python packages for training pipeline
pip install pandas>=1.5.0 pyarrow>=10.0.0 scikit-learn>=1.2.0
```

### **ENHANCED ML STACK (Optional but Recommended)**

```bash
# Full ML ecosystem for advanced models
pip install pandas pyarrow scikit-learn torch numpy matplotlib seaborn
```

---

## 📦 Detailed Package Analysis

### **Core Requirements (Minimum Viable Setup)**
| Package | Version | Purpose | Required |
|---------|---------|---------|----------|
| `pandas` | ≥1.5.0 | Data loading, manipulation | ✅ REQUIRED |
| `pyarrow` | ≥10.0.0 | Parquet file support | ✅ REQUIRED |
| `json` | Built-in | Configuration file reading | ✅ BUILT-IN |
| `pathlib` | Built-in | Path handling | ✅ BUILT-IN |
| `typing` | Built-in | Type hints | ✅ BUILT-IN |
| `logging` | Built-in | Logging | ✅ BUILT-IN |
| `gzip` | Built-in | Compressed files | ✅ BUILT-IN |

### **Enhanced ML Stack (Optional)**
| Package | Purpose | Priority |
|---------|---------|----------|
| `scikit-learn` | Classical ML models | HIGH |
| `torch` | Deep learning (PyTorch) | MEDIUM |
| `numpy` | Numerical computing | HIGH (included with pandas) |
| `matplotlib` | Data visualization | LOW |
| `seaborn` | Statistical plotting | LOW |

---

## 🔧 Installation Commands

### **Option 1: Minimal Setup (Training Pipeline Ready)**
```bash
pip install pandas pyarrow scikit-learn
```

### **Option 2: Full ML Development Environment**
```bash
pip install pandas pyarrow scikit-learn torch numpy matplotlib seaborn
```

### **Option 3: Custom Installation**
```bash
# Install only core requirements
pip install pandas pyarrow

# Test basic functionality
python -c "import pandas as pd; import pyarrow as pa; print('✅ Core setup complete')"

# Add ML capabilities if needed
pip install scikit-learn  # For sklearn models
pip install torch         # For deep learning
```

---

## ✅ Validation Commands

### **Test Environment Setup**
```bash
# 1. Test basic dependencies
python -c "import pandas as pd; import pyarrow as pa; print('✅ Core packages installed')"

# 2. Test data loading
python load_training_data.py

# 3. Test infrastructure
python demo_production_ml_infrastructure.py

# 4. Test ML imports
python -c "import sklearn; import torch; print('✅ ML packages available')"
```

---

## 🎯 Hardware-Specific Installation (Xeon X5690 Optimized)

### **Memory-Optimized Installation**
```bash
# Install with CPU-only PyTorch (saves memory)
pip install pandas pyarrow scikit-learn torch --index-url https://download.pytorch.org/whl/cpu

# Verify memory usage
python -c "
import psutil
print(f'Available RAM: {psutil.virtual_memory().available / 1024**3:.1f} GB')
import sklearn
print('✅ Sklearn loaded successfully')
"
```

---

## 🚨 Troubleshooting

### **Common Issues**

#### **1. Import Errors**
```bash
# pandas import error
pip install --upgrade pandas

# pyarrow import error
pip install --upgrade pyarrow

# sklearn import error  
pip install --upgrade scikit-learn
```

#### **2. Version Conflicts**
```bash
# Resolve version conflicts
pip install --force-reinstall pandas pyarrow scikit-learn

# Check installed versions
pip list | grep -E "pandas|pyarrow|scikit-learn"
```

#### **3. Memory Issues (Xeon X5690 with 8GB RAM)**
```bash
# Use lightweight versions
pip install pandas pyarrow --no-deps  # Avoid heavy dependencies
pip install scikit-learn --only-binary=all  # Pre-compiled wheel
```

### **Success Verification**
```bash
# Final validation script
python -c "
try:
    import pandas as pd
    import pyarrow as pa
    import sklearn
    print('✅ TRAINING PIPELINE ENVIRONMENT: READY')
    print(f'📦 pandas: {pd.__version__}')
    print(f'📦 pyarrow: {pa.__version__}')  
    print(f'📦 sklearn: {sklearn.__version__}')
except ImportError as e:
    print(f'❌ MISSING: {e}')
"
```

---

## 🎯 Next Steps After Installation

1. **Validate Setup**: Run `python demo_production_ml_infrastructure.py`
2. **Test Data Loading**: Run `python load_training_data.py`
3. **Begin Training**: Start with sklearn models for Xeon X5690
4. **Monitor Performance**: Use hardware_optimized_training.json settings

---

## 📊 Expected Performance on Xeon X5690

### **With Minimal Setup (pandas + pyarrow)**
- **Data Loading**: ~100ms for 6KB Parquet file
- **Memory Usage**: ~50MB base overhead
- **Classification**: Rule-based + keyword matching

### **With Full ML Stack (+ sklearn + torch)**
- **Data Loading**: ~150ms (slight overhead)
- **Memory Usage**: ~200MB base overhead  
- **Classification**: ML models + predictions

### **Xeon X5690 Limitations**
- **Max RAM Usage**: 1GB for sklearn, 4GB for torch
- **CPU Cores**: Optimize for 4-6 cores
- **Training Time**: 2-8 minutes (sklearn), 15-30 min (torch)