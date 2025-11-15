# RelationOS Advanced Analyzer & Detector

## 🎯 **Purpose**
Advanced ML-based relation classification system to replace regex-only extraction with intelligent semantic understanding.

## 📁 **Folder Structure**
```
analyzer/
├── README.md                    # This file
├── config/
│   ├── classifier_config.json   # ML model configuration
│   ├── domain_taxonomy.json     # Hierarchical domain definitions
│   └── sysml_patterns.json     # SysML-specific patterns
├── models/
│   ├── classifier.py           # Main ML classifier
│   ├── domain_hierarchy.py     # Hierarchical domain classification
│   ├── contextual_analyzer.py  # NLP contextual analysis
│   └── relation_validator.py   # Semantic validation
├── utils/
│   ├── text_preprocessing.py   # Text cleaning and normalization
│   ├── feature_extraction.py   # Feature engineering for ML
│   ├── nlp_processor.py        # NLP pipeline integration
│   └── confidence_scorer.py    # Advanced confidence scoring
├── training/
│   ├── sysml_dataset.py        # Training data preparation
│   ├── domain_samples.json     # Hand-labeled domain examples
│   ├── validation_set.json     # Validation data
│   └── metrics_tracker.py      # Training metrics
└── pipeline/
    ├── enhanced_harvester.py   # ML-enhanced harvesting pipeline
    ├── batch_processor.py      # Batch processing with ML
    ├── quality_assesor.py      # Quality assessment and filtering
    └── report_generator.py     # Detailed analysis reports
```

## 🔧 **Technical Architecture**

### **1. Multi-Layer Classification System**
```
Layer 1: Pattern Recognition (Enhanced Regex)
  ↓
Layer 2: Feature Extraction (NLP)
  ↓
Layer 3: Contextual Analysis (Semantic Understanding)
  ↓
Layer 4: ML Classification (Domain & Type)
  ↓
Layer 5: Validation & Scoring (Confidence Assessment)
```

### **2. Advanced Features**
- **Contextual Window**: Extract surrounding text around relations
- **Semantic Embeddings**: Use pre-trained models for understanding
- **Hierarchical Domains**: Multi-level domain classification
- **Confidence Thresholds**: Adaptive quality control
- **Learning Feedback**: Continuous improvement from corrections

## 🚀 **Implementation Priority**

### **Phase 1: Core ML Classifier**
- Text preprocessing and normalization
- Feature extraction (TF-IDF, word embeddings)
- Basic ML classification (Random Forest, SVM)
- Domain taxonomy implementation

### **Phase 2: Enhanced NLP**
- Contextual analysis with sliding windows
- Semantic similarity matching
- Relation validation patterns
- Advanced confidence scoring

### **Phase 3: SysML Specialization**
- SysML-specific training data
- Domain expert validation
- Pattern refinement for MBSE terminology
- Performance optimization

## 📊 **Expected Improvements**
- **Current**: 90.9% Uncategorized → **Target**: < 20% Uncategorized
- **Current**: Generic word matching → **Target**: Semantic relation understanding
- **Current**: 85% confidence → **Target**: > 95% confidence with ML scoring
- **Current**: No context awareness → **Target**: Full contextual understanding