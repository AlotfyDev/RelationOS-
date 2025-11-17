#!/usr/bin/env python3
"""
Command Line Interface for RelationOS Analysis
Handles argument parsing, configuration, and execution flow
"""

import argparse
import sys
from pathlib import Path
from typing import List, Optional

from ..core.data_analyzer import EnhancedRelationAnalyzer
from ..io.exporters import RelationOSExporter
from ..utils.monitoring import RelationAnalyzerMonitor


class RelationOSCLI:
    """
    Command Line Interface for RelationOS analysis operations
    """

    def __init__(self):
        self.args = None
        self.parser = argparse.ArgumentParser(
            description="RelationOS Human-Monitored Analysis Tool",
            formatter_class=argparse.RawDescriptionHelpFormatter,
            epilog="""
Examples:
  # Basic analysis
  python analyze_results.py

  # Export to CSV with detailed monitoring
  python analyze_results.py --csv --csv-path my_analysis.csv

  # Generate comprehensive reports
  python analyze_results.py --reports --reports-dir ./my_reports/

  # Quiet mode for automation
  python analyze_results.py --quiet --reports

  # Custom CSV and reports
  python analyze_results.py --csv-path analysis.csv --reports-dir reports/
            """
        )
        self._setup_arguments()

    def _setup_arguments(self):
        """Configure command line arguments"""

        # Output format options
        self.parser.add_argument(
            '--csv', nargs='?', const=True,
            help='Export to CSV format (specify path or use default)'
        )

        self.parser.add_argument(
            '--csv-path', type=str,
            help='Specific path for CSV export'
        )

        self.parser.add_argument(
            '--reports', nargs='?', const=True,
            help='Generate comprehensive reports directory'
        )

        self.parser.add_argument(
            '--reports-dir', type=str,
            help='Directory for comprehensive reports'
        )

        # Monitoring options
        self.parser.add_argument(
            '--quiet', '--silent', action='store_true',
            help='Reduce logging verbosity (disable detailed monitoring)'
        )

        self.parser.add_argument(
            '--no-monitor', action='store_true',
            help='Disable detailed monitoring'
        )

        # Analysis options
        self.parser.add_argument(
            '--max-domains', type=int, default=3,
            help='Maximum number of domains to show in detail (default: 3)'
        )

        self.parser.add_argument(
            '--confidence-threshold', type=float, default=0.8,
            help='Confidence threshold for high confidence relations (default: 0.8)'
        )

        # Data source options
        self.parser.add_argument(
            '--data-file', type=str,
            help='Specific data file to analyze (default: auto-detect)'
        )

        self.parser.add_argument(
            '--data-dir', type=str, default='data',
            help='Directory to search for data files (default: data)'
        )

        # Debug options
        self.parser.add_argument(
            '--verbose', '-v', action='store_true',
            help='Enable verbose output for debugging'
        )

        self.parser.add_argument(
            '--dry-run', action='store_true',
            help='Validate configuration without running analysis'
        )

    def parse_arguments(self, args: Optional[List[str]] = None) -> bool:
        """Parse command line arguments"""
        try:
            self.args = self.parser.parse_args(args)

            # Validation
            if self.args.csv_path and not self.args.csv:
                self.parser.error("--csv-path requires --csv")

            if self.args.reports_dir and not self.args.reports:
                self.parser.error("--reports-dir requires --reports")

            if self.args.confidence_threshold < 0 or self.args.confidence_threshold > 1:
                self.parser.error("--confidence-threshold must be between 0 and 1")

            return True

        except SystemExit:
            return False

    def get_monitor_config(self) -> RelationAnalyzerMonitor:
        """Get configured monitor instance"""
        enable_monitoring = not self.args.quiet and not self.args.no_monitor
        return RelationAnalyzerMonitor(enable_detailed_logging=enable_monitoring)

    def get_output_formats(self) -> List[str]:
        """Determine which output formats to generate"""
        formats = ['console']  # Always include console

        if self.args.csv or self.args.csv_path:
            formats.append('csv')

        if self.args.reports or self.args.reports_dir:
            formats.append('reports')

        return formats

    def get_export_paths(self):
        """Get configured export paths"""
        return {
            'csv_path': Path(self.args.csv_path) if self.args.csv_path else None,
            'reports_dir': Path(self.args.reports_dir) if self.args.reports_dir else None
        }

    def execute_analysis(self) -> int:
        """Execute the RelationOS analysis workflow"""
        if not self.args:
            print("Error: Arguments not parsed")
            return 1

        if self.args.dry_run:
            print("🔍 Dry run mode - validating configuration")
            self._print_configuration()
            return 0

        # Setup components
        monitor = self.get_monitor_config()
        output_formats = self.get_output_formats()

        monitor.log_operation_start("RelationOS Analysis", f"Output formats: {', '.join(output_formats)}")

        # Initialize analyzer
        analyzer = EnhancedRelationAnalyzer(
            output_formats=output_formats,
            monitor=monitor
        )

        # Initialize exporter
        exporter = RelationOSExporter(monitor=monitor)

        # Find and validate data source
        data_file = Path(self.args.data_file) if self.args.data_file else analyzer.find_data_source()
        if not data_file or not data_file.exists():
            print(f"No data source found. Please ensure data files exist or specify --data-file")
            return 1

        # Perform comprehensive analysis
        if not analyzer.load_and_analyze_data(data_file):
            print("DATA LOADING OR ANALYSIS FAILED")
            return 1

        # Generate console report (always done)
        analyzer.generate_console_report()

        # Handle optional exports
        paths = self.get_export_paths()

        if 'csv' in output_formats:
            csv_path = paths.get('csv_path') or Path("relationos_analysis.csv")
            csv_path.parent.mkdir(parents=True, exist_ok=True)
            success = exporter.export_to_csv(analyzer.df, csv_path)
            if success:
                print(f"📄 CSV exported to: {csv_path}")
            else:
                print("❌ CSV export failed")

        if 'reports' in output_formats:
            reports_dir = paths.get('reports_dir') or Path("relationos_analysis_reports")
            success = exporter.export_comprehensive_report(
                analyzer.df, reports_dir, analyzer.analysis_results
            )
            if success:
                print(f"📊 Comprehensive reports generated in: {reports_dir}")
            else:
                print("❌ Report generation failed")

        monitor.log_operation_complete("🎉 RelationOS Analysis Complete")
        return 0

    def _print_configuration(self):
        """Print current configuration for dry-run validation"""
        print("\n🔧 Current Configuration:")
        print(f"  Output formats: {self.get_output_formats()}")
        print(f"  Monitoring: {'enabled' if not self.args.no_monitor and not self.args.quiet else 'disabled'}")
        print(f"  Max domains: {self.args.max_domains}")
        print(f"  Confidence threshold: {self.args.confidence_threshold}")

        paths = self.get_export_paths()
        if paths['csv_path']:
            print(f"  CSV path: {paths['csv_path']}")
        if paths['reports_dir']:
            print(f"  Reports directory: {paths['reports_dir']}")

        if self.args.data_file:
            print(f"  Data file: {self.args.data_file}")
        print(f"  Data directory: {self.args.data_dir}")

        print("\n✅ Configuration validation passed")


def main(args: Optional[List[str]] = None) -> int:
    """Main entry point for RelationOS CLI"""
    cli = RelationOSCLI()

    if not cli.parse_arguments(args):
        return 1

    return cli.execute_analysis()


if __name__ == "__main__":
    sys.exit(main())
