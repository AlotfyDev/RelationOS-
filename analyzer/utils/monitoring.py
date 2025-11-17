#!/usr/bin/env python3
"""
Human-in-the-Loop Monitoring System for RelationOS Analysis
Provides real-time feedback and performance monitoring with detailed progress tracking

This module has been refactored into separate components for better maintainability:
- progress_tracker.py: Handles progress bar display and counters
- performance_monitor.py: Handles operation timing and metrics
"""

import time
import logging
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional, Any

# Import specialized monitoring components
from .progress_tracker import ProgressTracker
from .performance_monitor import PerformanceMonitor

logger = logging.getLogger(__name__)


class RelationAnalyzerMonitor:
    """
    Main monitoring coordinator that combines progress tracking and performance monitoring
    Provides a unified interface for human-in-the-loop analysis monitoring

    This class delegates to specialized components:
    - ProgressTracker: Real-time progress display and counters
    - PerformanceMonitor: Operation timing and performance metrics
    """

    def __init__(self, enable_detailed_logging: bool = True):
        self.enable_detailed_logging = enable_detailed_logging

        # Initialize specialized components
        self.progress_tracker = ProgressTracker()
        self.performance_monitor = PerformanceMonitor()

        self.progress_tracker.enable_logging(enable_detailed_logging)
        self.performance_monitor.enable_logging(enable_detailed_logging)

    def initialize_progress_tracking(self, total_pages: int):
        """Initialize detailed progress tracking with estimated totals"""
        self.progress_tracker.initialize_tracking(total_pages)

        # Set analysis start time in progress tracker for rate calculations
        self.progress_tracker.analysis_start_time = time.time()

    def update_progress(self, lines_processed: int = 0, pages_processed: int = 0, relations_found: int = 0):
        """Update detailed progress metrics and display real-time progress"""
        self.progress_tracker.update_progress(lines_processed, pages_processed, relations_found)

    def finalize_progress(self):
        """Finalize progress tracking with summary"""
        self.progress_tracker.finalize_progress()

    def log_operation_start(self, operation: str, details: str = ""):
        """Log the start of an analysis operation with human-readable context"""
        self.performance_monitor.log_operation_start(operation, details)

    def log_operation_complete(self, operation: str, metrics: Optional[Dict[str, Any]] = None):
        """Log completion with performance metrics and progress snapshot"""
        progress_snapshot = self.progress_tracker.get_progress_summary()

        # Merge progress info with operation metrics
        enhanced_metrics = metrics or {}
        enhanced_metrics['progress_snapshot'] = progress_snapshot

        self.performance_monitor.log_operation_complete(operation, enhanced_metrics)

        # Update checkpoint with progress information
        if hasattr(self.performance_monitor, 'checkpoints') and self.performance_monitor.checkpoints:
            self.performance_monitor.checkpoints[-1]['progress_at_completion'] = progress_snapshot

    def log_performance_metric(self, metric_name: str, value: Any, unit: str = ""):
        """Log specific performance metrics for human monitoring"""
        self.performance_monitor.log_performance_metric(metric_name, value, unit)

    def log_data_insight(self, insight: str, category: str = "info"):
        """Log human-interesting insights about the data"""
        self.performance_monitor.log_data_insight(insight, category)

    def get_progress_summary(self) -> Dict[str, Any]:
        """Get current progress summary for APIs"""
        return self.progress_tracker.get_progress_summary()

    def get_performance_summary(self) -> Dict[str, Any]:
        """Get comprehensive performance summary"""
        return self.performance_monitor.get_performance_summary()

    def generate_checkpoint_report(self) -> Dict[str, Any]:
        """Generate detailed checkpoint analysis"""
        return self.performance_monitor.generate_checkpoint_report()

    def generate_analysis_report(self) -> Dict[str, Any]:
        """Generate comprehensive analysis report for human review"""
        # Get reports from both components
        progress_report = self.progress_tracker.get_progress_summary()
        performance_report = self.performance_monitor.get_performance_summary()
        checkpoint_report = self.performance_monitor.generate_checkpoint_report()

        return {
            'monitoring_enabled': self.enable_detailed_logging,
            'progress_summary': progress_report,
            'performance_summary': performance_report,
            'checkpoint_analysis': checkpoint_report,
            'comprehensive_report': {
                'total_duration_seconds': performance_report.get('total_analysis_duration', 0),
                'operations_completed': performance_report.get('operations_completed', 0),
                'performance_metrics': performance_report.get('performance_metrics', {}),
                'checkpoints': checkpoint_report.get('checkpoints_timeline', []),
                'analysis_timestamp': datetime.now().isoformat(),
                'progress_details': progress_report
            }
        }

    def enable_logging(self, enabled: bool = True):
        """Enable or disable detailed logging across all components"""
        self.enable_detailed_logging = enabled
        self.progress_tracker.enable_logging(enabled)
        self.performance_monitor.enable_logging(enabled)

    def reset(self):
        """Reset all monitoring state"""
        if hasattr(self.progress_tracker, 'reset'):
            self.progress_tracker.reset()
        if hasattr(self.performance_monitor, 'reset'):
            self.performance_monitor.reset()
