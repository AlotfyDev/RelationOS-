#!/usr/bin/env python3
"""
Core Data Analysis Engine for RelationOS
Handles all MBSE relation analysis operations
"""

import json
import time
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional, Any, Tuple
import pandas as pd

from ..utils.monitoring import RelationAnalyzerMonitor


class EnhancedRelationAnalyzer:
    """
    Enhanced RelationOS analyzer with CSV output and human monitoring
    """

    def __init__(self, output_formats: List[str] = None, monitor: RelationAnalyzerMonitor = None):
        self.output_formats = output_formats or ['console']
        self.monitor = monitor or RelationAnalyzerMonitor()
        self.df = None
        self.analysis_results = {}

    def find_data_source(self) -> Optional[Path]:
        """Find the most appropriate data source with detailed logging"""
        self.monitor.log_operation_start("Data Source Detection", "Looking for harvested relation data")

        # Check for recently harvested data
        recent_data_file = Path("data/relations_harvested.parquet")
        original_data_file = Path("../DataSource/iso_deliverables_metadata.parquet")

        data_sources = [
            (recent_data_file, "Recent harvest data"),
            (original_data_file, "Original MBSE dataset")
        ]

        for file_path, description in data_sources:
            if file_path.exists():
                file_size_mb = file_path.stat().st_size / (1024 * 1024)
                self.monitor.log_operation_complete(
                    f"✓ Found {description}",
                    {'file_path': str(file_path), 'size_mb': f"{file_size_mb:.2f}"}
                )
                return file_path

        # No data found - provide detailed guidance
        self.monitor.log_operation_complete("❌ No data sources found")

        return None

    def load_and_analyze_data(self, data_file: Path) -> bool:
        """Load data and perform comprehensive analysis"""
        self.monitor.log_operation_start("Data Loading", f"Loading from {data_file}")

        try:
            # Load the data
            self.df = pd.read_parquet(data_file)

            # Basic data validation
            if len(self.df) == 0:
                self.monitor.log_operation_complete("❌ Data loading failed - empty dataset")
                return False

            # Log loading success
            file_size_mb = data_file.stat().st_size / (1024 * 1024)
            self.monitor.log_operation_complete(
                "✅ Data loaded successfully",
                {
                    'rows_loaded': len(self.df),
                    'columns': len(self.df.columns),
                    'file_size_mb': f"{file_size_mb:.2f}",
                    'memory_usage_mb': f"{self.df.memory_usage(deep=True).sum() / (1024*1024):.2f}"
                }
            )

            # Initialize progress tracking with estimated page count
            estimated_pages = len(self.df) // 10  # Rough estimate: 1 page per 10 relations
            self.monitor.initialize_progress_tracking(max(estimated_pages, 10))

            # Analyze data structure
            self.analyze_data_structure()
            self.monitor.update_progress(pages_processed=1)

            # Perform comprehensive analysis with progress updates
            self.perform_technical_analysis()
            self.monitor.update_progress(pages_processed=2)

            self.perform_domain_analysis()
            self.monitor.update_progress(pages_processed=2)

            self.perform_quality_analysis()
            self.monitor.update_progress(pages_processed=2)

            # Finalize progress tracking
            self.monitor.finalize_progress()

            return True

        except Exception as e:
            self.monitor.log_operation_complete(f"❌ Data loading failed: {str(e)}")
            return False

    def analyze_data_structure(self):
        """Analyze and report on data structure"""
        self.monitor.log_operation_start("Data Structure Analysis", "Understanding dataset schema and characteristics")

        # Schema analysis
        schema_info = {
            'columns': list(self.df.columns),
            'dtypes': self.df.dtypes.to_dict(),
            'total_rows': len(self.df)
        }

        # Data quality check
        missing_data = self.df.isnull().sum()
        has_missing = missing_data.sum() > 0

        if has_missing:
            schema_info['missing_data'] = True
            schema_info['columns_with_missing'] = missing_data[missing_data > 0].to_dict()

        self.monitor.log_data_insight(
            f"Dataset contains {len(self.df.columns)} columns with {len(self.df)} relationships",
            "info"
        )

        if has_missing:
            self.monitor.log_data_insight(
                f"Warning: {len(schema_info['columns_with_missing'])} columns contain missing values",
                "warning"
            )

        self.analysis_results['schema'] = schema_info
        self.monitor.log_operation_complete("✅ Data structure analyzed")

    def perform_technical_analysis(self):
        """Perform technical analysis of harvesting performance"""
        self.monitor.log_operation_start("Technical Performance Analysis", "Analyzing harvesting efficiency and data quality")

        # File size analysis
        data_file = self.df.iloc[0]['extraction_method'] if 'extraction_method' in self.df.columns else None
        analysis_result = {}

        # Confidence analysis
        if 'confidence' in self.df.columns:
            confidence_stats = {
                'mean': self.df['confidence'].mean(),
                'std': self.df['confidence'].std(),
                'min': self.df['confidence'].min(),
                'max': self.df['confidence'].max(),
                'high_confidence_ratio': (self.df['confidence'] >= 0.8).mean()
            }

            analysis_result['confidence_distribution'] = confidence_stats
            self.monitor.log_performance_metric(
                "Average Confidence Score",
                f"{confidence_stats['mean']:.3f}",
                "%"
            )
            self.monitor.log_performance_metric(
                "High Confidence Relations (>80%)",
                f"{confidence_stats['high_confidence_ratio']:.1%}",
                "ratio"
            )

        # Source analysis
        if 'source_standard' in self.df.columns:
            source_analysis = {
                'total_standards': self.df['source_standard'].nunique(),
                'standards_list': self.df['source_standard'].unique().tolist(),
                'relations_per_standard': self.df.groupby('source_standard').size().to_dict()
            }
            analysis_result['source_analysis'] = source_analysis

        analysis_result['technical_metrics'] = {
            'total_relations': len(self.df),
            'unique_relations': self.df['relation_name'].nunique() if 'relation_name' in self.df.columns else 0,
            'average_relation_length': self.df['relation_name'].str.len().mean() if 'relation_name' in self.df.columns else 0,
            'extraction_timestamp': datetime.now().isoformat()
        }

        self.analysis_results['technical'] = analysis_result
        self.monitor.log_operation_complete("✅ Technical analysis completed")

    def perform_domain_analysis(self):
        """Analyze domain distribution and patterns"""
        self.monitor.log_operation_start("Domain Analysis", "Analyzing relation distribution across MBSE domains")

        domain_analysis = {}
        domain_counts = self.df['domain'].value_counts()
        total_relations = len(self.df)

        # Domain distribution
        domain_distribution = {}
        for domain, count in domain_counts.items():
            percentage = (count / total_relations) * 100
            domain_distribution[domain] = {
                'count': int(count),
                'percentage': percentage,
                'description': self.get_domain_description(domain)
            }

        # Find most common relations by domain
        domain_top_relations = {}
        for domain in domain_counts.index[:3]:  # Top 3 domains
            domain_relations = self.df[self.df['domain'] == domain]['relation_name'].value_counts().head(5)
            domain_top_relations[domain] = domain_relations.to_dict()

        domain_analysis.update({
            'domain_distribution': domain_distribution,
            'top_relations_by_domain': domain_top_relations,
            'domain_diversity_index': len(domain_counts) / total_relations
        })

        # Log domain insights
        self.monitor.log_data_insight(
            f"Dataset spans {len(domain_counts)} unique domains with diversity index {domain_analysis['domain_diversity_index']:.3f}",
            "info"
        )
        self.monitor.log_data_insight(f"Most populated domain: {domain_counts.index[0]} with {domain_counts.iloc[0]} relations", "success")

        if 'Uncategorized' in domain_counts.index:
            uncategorized_ratio = (domain_counts['Uncategorized'] / total_relations) * 100
            if uncategorized_ratio > 70:
                self.monitor.log_data_insight(f"{uncategorized_ratio:.1f}% of relations are uncategorized - significant classification gap", "warning")
            elif uncategorized_ratio > 50:
                self.monitor.log_data_insight(f"{uncategorized_ratio:.1f}% of relations are uncategorized - moderate classification gap", "warning")
            else:
                self.monitor.log_data_insight(f"{uncategorized_ratio:.1f}% of relations are uncategorized - acceptable level", "info")
        self.analysis_results['domain'] = domain_analysis
        self.monitor.log_operation_complete("✅ Domain analysis completed")

    def perform_quality_analysis(self):
        """Analyze data quality metrics"""
        self.monitor.log_operation_start("Quality Analysis", "Evaluating data quality and extraction fidelity")

        quality_metrics = {}

        # Duplication analysis
        if len(self.df) > 0:
            # Check for exact duplicates
            duplicate_count = self.df.duplicated().sum()
            duplicate_ratio = duplicate_count / len(self.df)

            quality_metrics['duplication'] = {
                'exact_duplicates': int(duplicate_count),
                'duplicate_ratio': duplicate_ratio,
                'description': f"{'High' if duplicate_ratio > 0.1 else 'Low'} duplication rate"
            }

            if duplicate_count > 0:
                self.monitor.log_data_insight(f"Found {duplicate_count} duplicate relations ({duplicate_ratio:.1%})", "warning")

        # Length distribution analysis
        if 'relation_name' in self.df.columns:
            relation_lengths = self.df['relation_name'].str.len()
            length_stats = {
                'mean_length': relation_lengths.mean(),
                'median_length': relation_lengths.median(),
                'min_length': relation_lengths.min(),
                'max_length': relation_lengths.max(),
                'std_length': relation_lengths.std()
            }
            quality_metrics['relation_length_distribution'] = length_stats

        # Confidence quality assessment
        if 'confidence' in self.df.columns:
            confidence_quality = {
                'low_confidence_ratio': (self.df['confidence'] < 0.5).mean(),
                'high_confidence_ratio': (self.df['confidence'] >= 0.8).mean(),
                'medium_confidence_ratio': ((self.df['confidence'] >= 0.5) & (self.df['confidence'] < 0.8)).mean()
            }

            # Quality score calculation
            quality_score = confidence_quality['high_confidence_ratio'] * 1.0 + \
                          confidence_quality['medium_confidence_ratio'] * 0.5 + \
                          confidence_quality['low_confidence_ratio'] * 0.0

            quality_metrics['confidence_quality'] = {
                **confidence_quality,
                'overall_quality_score': quality_score,
                'quality_grade': self.get_quality_grade(quality_score)
            }

            self.monitor.log_data_insight(f"{confidence_quality['high_confidence_ratio']:.1%} relations have high confidence (>80%)", "info")
            self.monitor.log_data_insight(f"Data quality assessment: {self.get_quality_grade(quality_score)}", "quality")

        self.analysis_results['quality'] = quality_metrics
        self.monitor.log_operation_complete("✅ Quality analysis completed")

    def get_domain_description(self, domain: str) -> str:
        """Get human-readable description for MBSE domains"""
        descriptions = {
            'Uncategorized': 'Advanced or complex relations requiring specialized classification',
            'Traceability': 'Requirements, verification, and dependency relationships',
            'Structural': 'Composition, aggregation, and architectural relationships',
            'Behavioral': 'Process, activity, and interaction relationships',
            'Interface': 'Port, connector, and system boundary relationships',
            'Safety': 'Risk, hazard, and mitigation relationships',
            'Security': 'Authentication, authorization, and protection relationships',
            'Temporal': 'Time-based, sequencing, and scheduling relationships'
        }
        return descriptions.get(domain.lower(), 'Custom domain classification')

    def get_quality_grade(self, quality_score: float) -> str:
        """Convert quality score to human-understandable grade"""
        if quality_score >= 0.9:
            return '⭐ Exceptional Quality'
        elif quality_score >= 0.8:
            return '✅ Excellent Quality'
        elif quality_score >= 0.7:
            return '👍 Good Quality'
        elif quality_score >= 0.6:
            return '⚠️ Satisfactory Quality'
        elif quality_score >= 0.5:
            return '👎 Needs Improvement'
        else:
            return '❌ Poor Quality - Review Required'

    def generate_console_report(self):
        """Generate the original console-style report with enhanced monitoring"""
        if self.df is None:
            return

        self.monitor.log_operation_start("Console Report Generation", "Creating human-readable analysis summary")

        print("=" * 80)
        print("🤖 RELATIONOS HUMAN-MONITORED ANALYSIS REPORT")
        print("=" * 80)
        print(f"📊 Total Relations Processed: {len(self.df)}")
        print(f"📚 Source Standards: {self.df['source_standard'].nunique()}")
        analysis_report = self.monitor.generate_analysis_report()
        total_duration = analysis_report.get('comprehensive_report', {}).get('total_duration_seconds', 0)
        print(f"⚡ Analysis Duration: {total_duration:.2f} seconds")
        print()

        # Data quality insights
        if 'quality' in self.analysis_results and 'confidence_quality' in self.analysis_results['quality']:
            quality = self.analysis_results['quality']['confidence_quality']
            print("🔍 QUALITY INSIGHTS:")
            print(f"• High Confidence (>80%): {quality['high_confidence_ratio']:.1%}")
            print(f"• Medium Confidence (50-80%): {quality['medium_confidence_ratio']:.1%}")
            print(f"• Low Confidence (<50%): {quality['low_confidence_ratio']:.1%}")
            print(f"• Overall Quality Grade: {quality['quality_grade']}")
            print()

        print("📈 RELATIONS BY SOURCE STANDARD:")
        standard_counts = self.df['source_standard'].value_counts()
        for standard, count in standard_counts.items():
            percentage = (count / len(self.df)) * 100
            print(f"• {standard}: {count:,} relations ({percentage:.1f}%)")
        print()

        print("🔬 RELATIONS BY DOMAIN:")
        domain_counts = self.df['domain'].value_counts()
        for domain, count in domain_counts.items():
            percentage = (count / len(self.df)) * 100
            description = self.get_domain_description(domain)
            print(f"• {domain}: {count:,} relations ({percentage:.1f}%)")
            print(f"  └─ {description}")
        print()

        print("🎯 TOP RELATIONS BY DOMAIN:")
        for domain in domain_counts.index[:3]:
            print(f"├─ {domain}:")
            domain_relations = self.df[self.df['domain'] == domain]['relation_name'].value_counts().head(3)
            for i, (relation, count) in enumerate(domain_relations.items()):
                connector = "├─" if i < len(domain_relations) - 1 else "└─"
                print(f"│  {connector} '{relation}' ({count} occurrences)")
        print()

        print("📊 CONFIDENCE ANALYSIS:")
        if 'confidence' in self.df.columns:
            conf_stats = self.df['confidence'].describe()
            print(f"• Mean: {conf_stats['mean']:.3f}")
            print(f"• Std Dev: {conf_stats['std']:.3f}")
            print(f"• Min: {conf_stats['min']:.3f}")
            print(f"• Max: {conf_stats['max']:.3f}")
        print()

        print("🏆 DATA EFFICIENCY METRICS:")
        file_size = 0
        for file_path in [Path("data/relations_harvested.parquet"), Path("../DataSource/iso_deliverables_metadata.parquet")]:
            if file_path.exists():
                file_size = file_path.stat().st_size
                break

        if file_size > 0:
            file_size_mb = file_size / (1024 * 1024)
            avg_relations_per_mb = len(self.df) / file_size_mb
            print(f"• Parquet file size: {file_size_mb:.6f} MB")
            print(f"• Relations per MB: {avg_relations_per_mb:.0f}")
            print(f"• Total extracted relations: {len(self.df)}")
        print()

        print("📋 DATA SCHEMA:")
        print(f"• Columns: {', '.join(self.df.columns.tolist())}")
        print(f"• Sample Relation ID: {self.df.iloc[0]['id'] if len(self.df) > 0 else 'N/A'}")
        print(f"• Data Types: {len(self.df.dtypes)} field types")
        print()

        print("🎉 ANALYSIS COMPLETED SUCCESSFULLY!")
        print("=" * 80)

        self.monitor.log_operation_complete("✅ Console report generation completed")

    def export_to_csv(self, output_path: Optional[Path] = None) -> bool:
        """Export analysis results to CSV format"""
        self.monitor.log_operation_start("CSV Export", "Exporting analysis results to CSV format")

        if output_path is None:
            output_path = Path("analysis_results.csv")

        try:
            # Get the exporter
            from ..io.exporters import RelationOSExporter
            exporter = RelationOSExporter(monitor=self.monitor)

            # Flatten analysis results for CSV export
            flattened_results = self._flatten_analysis_results()

            if flattened_results:
                exporter.export_to_csv(pd.DataFrame(flattened_results), output_path)
                self.monitor.log_operation_complete("✅ CSV export completed", {'output_path': str(output_path)})
                return True
            else:
                self.monitor.log_operation_complete("❌ No analysis results to export")
                return False

        except Exception as e:
            self.monitor.log_operation_complete(f"❌ CSV export failed: {str(e)}")
            return False

    def export_comprehensive_report(self, output_dir: Optional[Path] = None, analysis_results: Optional[Dict] = None) -> bool:
        """Export comprehensive analysis report"""
        if output_dir is None:
            output_dir = Path("analysis_reports")

        self.monitor.log_operation_start("Comprehensive Report Export", f"Generating reports in {output_dir}")

        try:
            # Get the exporter
            from ..io.exporters import RelationOSExporter
            exporter = RelationOSExporter(monitor=self.monitor)

            success = exporter.export_comprehensive_report(
                self.df, output_dir, analysis_results if analysis_results else self.analysis_results
            )
            return success

        except Exception as e:
            self.monitor.log_operation_complete(f"❌ Report export failed: {str(e)}")
            return False

    def _flatten_analysis_results(self) -> List[Dict]:
        """Flatten nested analysis results for CSV export"""
        flattened = []

        # Schema information
        if 'schema' in self.analysis_results:
            schema = self.analysis_results['schema']
            flattened.append({
                'analysis_type': 'schema',
                'metric_name': 'column_structure',
                'metric_value': ';'.join(schema.get('columns', [])),
                'details': f"Total columns: {len(schema.get('columns', []))}"
            })

        # Technical metrics
        if 'technical' in self.analysis_results:
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
        if 'domain' in self.analysis_results:
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
        if 'quality' in self.analysis_results:
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
        if not flattened and self.df is not None:
            # Add sample rows
            sample_df = self.df.head(5)
            for idx, row in sample_df.iterrows():
                flattened.append({
                    'analysis_type': 'sample_data',
                    'metric_name': f'row_{idx}',
                    'metric_value': row.to_json() if hasattr(row, 'to_json') else str(row),
                    'details': 'Sample data row'
                })

        return flattened
