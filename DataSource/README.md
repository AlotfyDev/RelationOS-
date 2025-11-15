# DataSource Directory

## 📊 **RelationOS Data Repository**

This directory contains **MBSE (Model-Based Systems Engineering) data sources** used for RelationOS relation extraction and analysis.

## 📁 **Contents**

### **📄 Data Files**
- **iso_deliverables_metadata.csv** - CSV export of ISO deliverables relationship analysis
- **iso_deliverables_metadata.parquet** - Parquet-optimized version for analytics
- **Metadata file sizes**: ~57GB total (significant dataset for MBSE analysis)

### **📖 Source Documents**
- **SysML_formal-25-09-03.pdf** (18MB) - Official SysML specification document
- **UML_formal-17-12-05.pdf** (18MB) - Official UML specification document
- **RequirementsInterchangeFormat_formal-16-07-02.pdf** (680KB) - ReqIF standard specification
- **Nis_STATUTE-130-Pg2969.pdf** (346KB) - Additional MBSE standards documentation

## 🎯 **Purpose**

### **Training Data**
- **Primary source** for ML model training and relation extraction algorithms
- **MBSE standards corpus** for language models and pattern recognition
- **Cross-standard analysis** enabling SysML/UML/ReqIF relation mapping

### **System Testing**
- **Reference documents** for validating relation extraction accuracy
- **Benchmark dataset** for measuring classifier performance
- **Quality assurance** corpus for confidence scoring validation

### **Research & Development**
- **Standard specifications** for MBSE ontology development
- **Industry corpus** for academic research and tooling validation
- **Baseline dataset** for algorithm improvement and parameter tuning

## 📊 **Dataset Characteristics**

`python
# Approximate statistics
standards_covered = ["SysML", "UML", "ReqIF"]
total_documents = 4
total_size_mb = 180  # Total specification documents
data_points_estimated = 50000+  # Relations extracted/analysis points
`

## 🔧 **Usage**

### **Access Pattern**
`python
# Example data access (assuming relative paths)
data_dir = Path("../DataSource")
specs = [
    data_dir / "SysML_formal-25-09-03.pdf",
    data_dir / "UML_formal-17-12-05.pdf"
]
`

### **Integration Notes**
- **Original location**: Previously stored in docs/harvesting/
- **Renamed for clarity**: "harvesting" → "DataSource" (more professional naming)
- **Root-level placement**: Direct access alongside other project components

## 📚 **Data Sources**

### **Official Standards**
- **SysML Specification v2.0** - Systems Modeling Language standards
- **UML Specification v2.5** - Unified Modeling Language standards
- **ReqIF Specification** - Requirements Interchange Format standards

### **Analysis Data**
- **ISO Deliverables metadata** - Cross-reference analysis results
- **Standards corpus** - Curated collection for MBSE research

## 🎓 **Academic & Research Value**

This dataset provides:
- ✅ **Industry-standard specifications** for academic MBSE research
- ✅ **Reference implementation** corpus for tool validation
- ✅ **Benchmark dataset** for algorithm comparison
- ✅ **Standards compliance** test suite for MBSE tooling

---

**DataSource Directory** | **Professional MBSE Data Repository** | **Root-level access for all RelationOS components** 🚀
