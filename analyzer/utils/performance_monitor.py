#!/usr/bin/env python3
"""
Performance Monitoring Module for RelationOS
Handles performance tracking, metrics collection, and operation reporting
"""

import time
import logging
from datetime import datetime
from typing import Dict, List, Optional, Any

logger = logging.getLogger(__name__)


class PerformanceMonitor:
    """
    Handles performance tracking and operation monitoring
    Records operation durations, metrics, and checkpoints
    """

    def __init__(self):
        self.start_time = time.time()
        self.operations_completed = 0
        self.performance_metrics = {}
        self.checkpoints = []
        self.enable_detailed_logging = True

    def log_operation_start(self, operation: str, details: str = ""):
        """Log the start of an analysis operation with human-readable context"""
        if self.enable_detailed_logging:
            logger.info(f"🔄 Starting: {operation}")
            if details:
                logger.info(f"   📋 {details}")

    def log_operation_complete(self, operation: str, metrics: Dict[str, Any] = None):
        """Log completion with performance metrics"""
        duration = time.time() - self.start_time
        self.operations_completed += 1

        logger.info(f"✅ {operation} completed in {duration:.2f}s")

        if metrics:
            for key, value in metrics.items():
                logger.debug(f"   📊 {key}: {value}")

        self.checkpoints.append({
            'operation': operation,
            'timestamp': datetime.now().isoformat(),
            'duration': duration,
            'metrics': metrics or {},
            'progress_at_completion': {},  # Will be populated by main monitor
            'operation_sequence': self.operations_completed
        })

    def log_performance_metric(self, metric_name: str, value: Any, unit: str = ""):
        """Log specific performance metrics for human monitoring"""
        self.performance_metrics[metric_name] = {'value': value, 'unit': unit}

        if isinstance(value, (int, float)) and unit:
            logger.info(f"📈 {metric_name}: {value} {unit}")
        else:
            logger.info(f"📈 {metric_name}: {value}")

    def log_data_insight(self, insight: str, category: str = "info"):
        """Log human-interesting insights about the data"""
        emoji_map = {
            'info': '💡',
            'warning': '⚠️',
            'error': '❌',
            'success': '🎯',
            'quality': '⭐'
        }

        emoji = emoji_map.get(category.lower(), '💡')
        logger.info(f"{emoji} {insight}")

    def get_performant_operations(self) -> List[Dict[str, Any]]:
        """Get list of operations sorted by performance"""
        sorted_checkpoints = sorted(self.checkpoints,
                                  key=lambda x: x.get('duration', 0),
                                  reverse=True)

        slow_operations = []
        for checkpoint in sorted_checkpoints[:5]:  # Top 5 slowest
            duration = checkpoint.get('duration', 0)
            if duration > 1.0:  # Only show operations taking more than 1 second
                slow_operations.append({
                    'operation': checkpoint['operation'],
                    'duration_seconds': duration,
                    'timestamp': checkpoint['timestamp'],
                    'sequence': checkpoint.get('operation_sequence', 0)
                })

        return slow_operations

    def get_performance_summary(self) -> Dict[str, Any]:
        """Get comprehensive performance summary"""
        total_duration = time.time() - self.start_time

        # Calculate operation statistics
        durations = [cp.get('duration', 0) for cp in self.checkpoints if 'duration' in cp]

        performance_stats = {}
        if durations:
            performance_stats = {
                'total_operations': len(durations),
                'average_duration': sum(durations) / len(durations) if durations else 0,
                'longest_operation': max(durations) if durations else 0,
                'shortest_operation': min(durations) if durations else 0,
                'total_operation_time': sum(durations)
            }

        # Performance efficiency calculation
        if total_duration > 0:
            performance_stats['operation_efficiency'] = performance_stats.get('total_operation_time', 0) / total_duration
            performance_stats['overhead_ratio'] = (total_duration - performance_stats.get('total_operation_time', 0)) / total_duration

        return {
            'total_analysis_duration': total_duration,
            'operations_completed': self.operations_completed,
            'performance_stats': performance_stats,
            'top_slow_operations': self.get_performant_operations(),
            'performance_metrics': self.performance_metrics
        }

    def generate_checkpoint_report(self) -> Dict[str, Any]:
        """Generate detailed checkpoint analysis"""
        if not self.checkpoints:
            return {'message': 'No checkpoints recorded'}

        # Operation sequence analysis
        sequence_analysis = []
        for i, checkpoint in enumerate(self.checkpoints):
            if i > 0:
                prev_time = datetime.fromisoformat(self.checkpoints[i-1]['timestamp'])
                curr_time = datetime.fromisoformat(checkpoint['timestamp'])
                time_gap = (curr_time - prev_time).total_seconds()

                sequence_analysis.append({
                    'from_operation': self.checkpoints[i-1]['operation'],
                    'to_operation': checkpoint['operation'],
                    'time_gap_seconds': time_gap,
                    'sequence_position': i
                })

        # Time distribution analysis
        total_time = sum(cp.get('duration', 0) for cp in self.checkpoints)
        if total_time > 0:
            time_distribution = []
            for checkpoint in self.checkpoints:
                duration = checkpoint.get('duration', 0)
                percentage = (duration / total_time) * 100
                time_distribution.append({
                    'operation': checkpoint['operation'],
                    'duration': duration,
                    'percentage': percentage
                })

            time_distribution.sort(key=lambda x: x['percentage'], reverse=True)
        else:
            time_distribution = []

        return {
            'total_checkpoints': len(self.checkpoints),
            'sequence_analysis': sequence_analysis,
            'time_distribution': time_distribution,
            'checkpoints_timeline': self.checkpoints
        }

    def enable_logging(self, enabled: bool = True):
        """Enable or disable detailed logging"""
        self.enable_detailed_logging = enabled

    def add_checkpoint(self, operation: str, timestamp: str, duration: float, metrics: Dict[str, Any] = None):
        """Add a manual checkpoint (used by main monitor)"""
        self.checkpoints.append({
            'operation': operation,
            'timestamp': timestamp,
            'duration': duration,
            'metrics': metrics or {},
            'progress_at_completion': {},
            'manual_entry': True
        })

    def reset(self):
        """Reset all performance data"""
        self.start_time = time.time()
        self.operations_completed = 0
        self.performance_metrics = {}
        self.checkpoints = []
