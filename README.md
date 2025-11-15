# RelationOS  
**Unified Relation Ontology for Model-Based Systems & Software Engineering**  

## Vision (November 2025)  
Building the first comprehensive meta-ontology and software for all types of relationships in:  
SysML v2 • UML • OWL • OSLC • ReqIF • AP243 • Cameo • Rhapsody • Capella  

## Goal  
Fill all gaps + unify language + 100% automated tracking + semantic queries + AI support  

## Structure
RelationOS/
├── README.md                       ← This documentation
├── LICENSE (MIT)                  ← Open source MIT license
├── .gitignore                      ← Git ignore rules
├── DataSource/                     ← Official MBSE specifications & data
│   ├── *.pdf                       ← SysML, UML, ReqIF specifications
│   ├── iso_deliverables_metadata.csv    ← Analysis datasets
│   ├── iso_deliverables_metadata.parquet ← Optimized data format
│   └── README.md                   ← Data documentation
├── analyzer/                       ← Modern ML classification system
│   └── models/transformer/         ← BGE transformer analyzer
│       ├── base_classifier.py      ← Classification interface
│       ├── bge_classifier.py       ← BAAI BGE integration
│       ├── rule_based.py          ← Domain-specific logic
│       ├── types.py               ← Expert parameters
│       └── tests/                 ← Comprehensive test suite
├── scripts/                        ← Python processing scripts
└── *.py                           ← Analysis & utility scripts

## Quick Start
```bash
# Place PDF specifications in DataSource/ directory
# Official MBSE standards available in DataSource/
python scripts/harvest.py                    # Run data harvesting pipeline
python analyze_results.py                   # Analyze extracted relationships

# Run the modern transformer analyzer
cd analyzer/models/transformer/
python example_usage.py                     # See advanced usage examples

# Run granular functionality tests
cd tests/suite/
python test_runner.py                       # Run all validation tests
```

## Progress (15 November 2025)
- SysML v2          → 0 / ~2800 relations
- UML 2.5.1        → 0 / ~1200
- OSLC Core         → 0 / ~380
- OWL 2 + Top 50   → 0 / ~900

## Contributing
Open Issue or PR – every line here will change the future of MBSE in the Arab world and worldwide.
"Software is not code, it is a system that needs a real ontology"
– RelationOS Contributors, 15 November 2025

## Technical Documentation
See [docs/](docs/) for detailed technical documentation.
