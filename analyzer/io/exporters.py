#!/usr/bin/env python3
"""
Data Export and Reporting Module for RelationOS
Handles CSV export, JSON reporting, and comprehensive analysis outputs
"""

from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional, Any
import json
import pandas as pd

from ..utils.monitoring import RelationAnalyzerMonitor


class RelationOSExporter:
    """
    Handles all export operations for RelationOS analysis results
    """

    def __init__(self, monitor: Optional[RelationAnalyzerMonitor] = None):
        self.monitor = monitor or RelationAnalyzerMonitor()

    def export_to_csv(self, df: pd.DataFrame, output_path: Optional[Path] = None) -> bool:
        """Export analysis results to CSV format"""
        self.monitor.log_operation_start("CSV Export", "Exporting analysis results to CSV format")

        if output_path is None:
            output_path = Path("analysis_results.csv")

        try:
            # Flatten analysis results for CSV export
            flattened_results = self._flatten_analysis_results(df)

            if flattened_results:
                export_df = pd.DataFrame(flattened_results)
                export_df.to_csv(output_path, index=False)

                self.monitor.log_operation_complete(
                    "✅ CSV export completed",
                    {'output_path': str(output_path), 'rows_exported': len(export_df)}
                )
                return True
            else:
                self.monitor.log_operation_complete("❌ No analysis results to export")
                return False

        except Exception as e:
            self.monitor.log_operation_complete(f"❌ CSV export failed: {str(e)}")
            return False

    def export_comprehensive_report(self, df: pd.DataFrame, output_dir: Optional[Path] = None,
                                   analysis_results: Optional[Dict] = None) -> bool:
        """Export comprehensive analysis report in multiple formats"""
        if output_dir is None:
            output_dir = Path("analysis_reports")

        output_dir.mkdir(exist_ok=True)
        self.monitor.log_operation_start("Comprehensive Report Export",
                                        f"Generating reports in {output_dir}")

        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            base_filename = f"relationos_analysis_{timestamp}"

            # Export CSV data
            csv_path = output_dir / f"{base_filename}.csv"
            success_csv = self.export_to_csv(df, csv_path)

            # Export JSON analysis results
            json_path = output_dir / f"{base_filename}_analysis.json"
            success_json = self._export_json_report(json_path, df, analysis_results)

            # Export monitoring log
            log_path = output_dir / f"{base_filename}_monitoring.log"
            success_log = self._export_monitoring_log(log_path)

            success_all = success_csv and success_json and success_log
            self.monitor.log_operation_complete(
                f"{'✅' if success_all else '⚠️'} Comprehensive report export completed"
            )
            return success_all

        except Exception as e:
            self.monitor.log_operation_complete(f"❌ Report export failed: {str(e)}")
            return False

    def _flatten_analysis_results(self, df: pd.DataFrame) -> List[Dict]:
        """Flatten nested analysis results for CSV export"""
        flattened = []

        # Schema information
        if hasattr(self, 'analysis_results') and 'schema' in self.analysis_results:
            schema = self.analysis_results['schema']
            flattened.append({
                'analysis_type': 'schema',
                'metric_name': 'column_structure',
                'metric_value': ';'.join(schema.get('columns', [])),
                'details': f"Total columns: {len(schema.get('columns', []))}"
            })

        # Technical metrics
        if hasattr(self, 'analysis_results') and 'technical' in self.analysis_results:
            tech = self.analysis_results['technical']
            if 'confidence_distribution' in tech:
                conf = tech['confidence_distribution']
                flattened.append({
                    'analysis_type': 'technical',
                    'metric_name': 'confidence_mean',
                    'metric_value': conf.get('mean', 0),
                    'details': 'Average confidence score'
                })

            if 'source_analysis' in tech:
                sources = tech['source_analysis']
                for standard, count in sources.get('relations_per_standard', {}).items():
                    flattened.append({
                        'analysis_type': 'source_distribution',
                        'metric_name': standard,
                        'metric_value': count,
                        'details': 'Relations per source standard'
                    })

        # Domain analysis
        if hasattr(self, 'analysis_results') and 'domain' in self.analysis_results:
            domain = self.analysis_results['domain']
            if 'domain_distribution' in domain:
                for domain_name, stats in domain['domain_distribution'].items():
                    flattened.append({
                        'analysis_type': 'domain_distribution',
                        'metric_name': domain_name,
                        'metric_value': stats.get('count', 0),
                        'details': f"{stats.get('percentage', 0):.1f}% | {stats.get('description', '')}"
                    })

        # Quality metrics
        if hasattr(self, 'analysis_results') and 'quality' in self.analysis_results:
            quality = self.analysis_results['quality']
            if 'confidence_quality' in quality:
                conf_qual = quality['confidence_quality']
                flattened.append({
                    'analysis_type': 'quality',
                    'metric_name': 'overall_quality_score',
                    'metric_value': conf_qual.get('overall_quality_score', 0),
                    'details': f"Grade: {conf_qual.get('quality_grade', '')}"
                })

        # If no structured analysis, add basic data preview
        if not flattened and df is not None:
            # Add sample rows
            sample_df = df.head(5)
            for idx, row in sample_df.iterrows():
                flattened.append({
                    'analysis_type': 'sample_data',
                    'metric_name': f'row_{idx}',
                    'metric_value': row.to_json() if hasattr(row, 'to_json') else str(row),
                    'details': 'Sample data row'
                })

        return flattened

    def _export_json_report(self, json_path: Path, df: pd.DataFrame,
                           analysis_results: Optional[Dict] = None) -> bool:
        """Export JSON analysis results"""
        try:
            json_data = {
                'analysis_results': analysis_results or {},
                'monitoring_report': self.monitor.generate_analysis_report(),
                'metadata': {
                    'generated_at': datetime.now().isoformat(),
                    'data_size': len(df) if df is not None else 0,
                    'analysis_version': '2.0_modular_export'
                }
            }

            with open(json_path, 'w', encoding='utf-8') as f:
                json.dump(json_data, f, indent=2, ensure_ascii=False, default=str)

            self.monitor.log_performance_metric("JSON Report Exported", str(json_path))
            return True

        except Exception as e:
            return False

    def _export_monitoring_log(self, log_path: Path) -> bool:
        """Export detailed monitoring log"""
        try:
            with open(log_path, 'w', encoding='utf-8') as f:
                f.write("=" * 80 + "\n")
                f.write("RelationOS Analysis Monitoring Log\n")
                f.write("=" * 80 + "\n\n")

                monitoring_report = self.monitor.generate_analysis_report()

                f.write(f"Analysis Duration: {monitoring_report['total_duration_seconds']:.2f} seconds\n")
                f.write(f"Operations Completed: {monitoring_report['operations_completed']}\n")
                f.write(f"Monitoring Enabled: {monitoring_report['monitoring_enabled']}\n")
                f.write(f"Generated At: {monitoring_report['analysis_timestamp']}\n\n")

                f.write("PERFORMANCE METRICS:\n")
                f.write("-" * 40 + "\n")
                for metric_name, metric_data in monitoring_report['performance_metrics'].items():
                    value = metric_data['value']
                    unit = metric_data['unit']
                    f.write(f"• {metric_name}: {value} {unit}\n")
                f.write("\n")

                f.write("OPERATION CHECKPOINTS:\n")
                f.write("-" * 40 + "\n")
                for checkpoint in monitoring_report['checkpoints']:
                    f.write(f"✓ {checkpoint['operation']}\n")
                    f.write(f"  Completed at: {checkpoint['timestamp']}\n")
                    f.write(f"  Duration: {checkpoint['duration']:.2f}s\n")
                    if checkpoint['metrics']:
                        for key, value in checkpoint['metrics'].items():
                            f.write(f"    {key}: {value}\n")
                    f.write("\n")

            return True

        except Exception as e:
            return False
