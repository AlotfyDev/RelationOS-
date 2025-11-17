#!/usr/bin/env python3
"""
Progress Tracking Module for RelationOS
Handles real-time progress monitoring during analysis operations
"""

import time
import logging
from typing import Dict, Any

logger = logging.getLogger(__name__)


class ProgressTracker:
    """
    Handles detailed progress tracking with real-time updates
    Shows processed lines, pages, and relations to users
    """

    def __init__(self):
        # Core progress counters
        self.processed_lines = 0
        self.processed_pages = 0
        self.detected_relations = 0
        self.total_target_pages = 0

        # Update throttling
        self.last_progress_update = 0
        self.progress_update_interval = 0.1  # Update every 100ms

        # UI state
        self.enable_detailed_logging = True

    def initialize_tracking(self, total_pages: int):
        """Initialize progress tracking with estimated totals"""
        self.total_target_pages = total_pages
        self.processed_lines = 0
        self.processed_pages = 0
        self.detected_relations = 0

        if self.enable_detailed_logging:
            logger.info(f"📊 Analysis Target: {total_pages:,} pages ({self.total_target_pages:,} total)")
            self._display_progress_header()

    def update_progress(self, lines_processed: int = 0, pages_processed: int = 0, relations_found: int = 0):
        """Update detailed progress metrics and display real-time progress"""
        self.processed_lines += lines_processed
        self.processed_pages += pages_processed
        self.detected_relations += relations_found

        # Throttle progress updates to avoid spam
        current_time = time.time()
        if current_time - self.last_progress_update > self.progress_update_interval:
            self._display_progress_update()
            self.last_progress_update = current_time

    def _display_progress_header(self):
        """Display the progress tracking header"""
        logger.info("🔄 Progress Tracking Started:")
        logger.info(f"   Target: {self.total_target_pages:,} pages to process")
        logger.info("   Progress: |░░░░░░░░░░░░░░░░░░░░| Lines: 0 | Pages: 0/0 | Relations: 0")
        logger.info("")  # Empty line for spacing

    def _display_progress_update(self):
        """Display real-time progress update"""
        if not self.enable_detailed_logging or self.total_target_pages == 0:
            return

        # Calculate progress percentage
        progress_ratio = min(1.0, self.processed_pages / self.total_target_pages)
        progress_bar_width = 20
        filled_width = int(progress_ratio * progress_bar_width)
        bar = "█" * filled_width + "░" * (progress_bar_width - filled_width)

        # Format numbers with commas for readability
        lines_str = f"{self.processed_lines:,}"
        pages_str = f"{self.processed_pages}/{self.total_target_pages:,}"
        relations_str = f"{self.detected_relations:,}"

        # Calculate rates (avoid division by zero)
        start_time = getattr(self, 'analysis_start_time', time.time())
        elapsed = time.time() - start_time
        if elapsed > 0:
            relations_per_second = self.detected_relations / elapsed
            pages_per_second = self.processed_pages / elapsed
        else:
            relations_per_second = 0
            pages_per_second = 0

        # Create progress string (overwrite previous line)
        progress_str = (f"\r🔄 Progress: |{bar}| "
                       f"Lines: {lines_str} | "
                       f"Pages: {pages_str} ({progress_ratio:.1%}) | "
                       f"Relations: {relations_str} ({relations_per_second:.0f}/sec)")

        print(progress_str, end="", flush=True)

        # If completed, add a newline
        if self.processed_pages >= self.total_target_pages:
            print("")  # New line for completion

    def finalize_progress(self):
        """Finalize progress tracking with summary"""
        if self.enable_detailed_logging and self.processed_pages > 0:
            start_time = getattr(self, 'analysis_start_time', time.time())
            elapsed = time.time() - start_time
            if elapsed > 0:
                relations_per_second = self.detected_relations / elapsed
                pages_per_second = self.processed_pages / elapsed
                lines_per_second = self.processed_lines / elapsed

                logger.info("✅ Analysis Complete!")
                logger.info(f"   📊 Relations Found: {self.detected_relations:,} ({relations_per_second:.1f}/sec)")
                logger.info(f"   📄 Pages Processed: {self.processed_pages:,} ({pages_per_second:.1f}/sec)")
                logger.info(f"   📝 Lines Processed: {self.processed_lines:,} ({lines_per_second:.1f}/sec)")

    def get_progress_summary(self) -> Dict[str, Any]:
        """Get current progress summary for APIs"""
        start_time = getattr(self, 'analysis_start_time', time.time())
        elapsed = time.time() - start_time
        progress_ratio = 0.0
        if self.total_target_pages > 0:
            progress_ratio = min(1.0, self.processed_pages / self.total_target_pages)

        rates = {}
        if elapsed > 0:
            rates = {
                'relations_per_second': self.detected_relations / elapsed,
                'pages_per_second': self.processed_pages / elapsed,
                'lines_per_second': self.processed_lines / elapsed
            }

        return {
            'processed_lines': self.processed_lines,
            'processed_pages': self.processed_pages,
            'detected_relations': self.detected_relations,
            'total_target_pages': self.total_target_pages,
            'progress_ratio': progress_ratio,
            'elapsed_seconds': elapsed,
            'rates': rates
        }

    def reset(self):
        """Reset all progress counters"""
        self.processed_lines = 0
        self.processed_pages = 0
        self.detected_relations = 0
        self.total_target_pages = 0
        self.last_progress_update = 0

    def enable_logging(self, enabled: bool = True):
        """Enable or disable detailed progress logging"""
        self.enable_detailed_logging = enabled
