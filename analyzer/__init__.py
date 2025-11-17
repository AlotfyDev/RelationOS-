"""
RelationOS Analysis Package
Human-in-the-loop monitoring and analysis of MBSE relations

This package provides a modular, well-structured approach to analyzing
MBSE relation data with comprehensive monitoring, export capabilities,
and command-line interfaces.

Modules:
    - monitoring: Human-in-the-loop progress monitoring
    - data_analyzer: Core analysis functionality
    - exporters: CSV and report export capabilities
    - cli: Command-line interface and argument parsing
    - main: Entry point for the analysis tool
"""

__version__ = "2.0.0"
__author__ = "RelationOS Team"
__description__ = "Modular MBSE Relation Analysis Tool with Human Monitoring"

from .utils.monitoring import RelationAnalyzerMonitor
from .core.data_analyzer import EnhancedRelationAnalyzer
from .io.exporters import RelationOSExporter
from .commands.cli import RelationOSCLI
from .main import main

__all__ = [
    'RelationAnalyzerMonitor',
    'EnhancedRelationAnalyzer',
    'RelationOSExporter',
    'RelationOSCLI',
    'main'
]
