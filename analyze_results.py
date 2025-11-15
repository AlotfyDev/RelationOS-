#!/usr/bin/env python3
"""
RelationOS Results Analysis Script
Analyzes harvested relations from MBSE specifications
"""

import pandas as pd
import numpy as np
from pathlib import Path

def analyze_harvested_relations():
    """Analyze the harvested relations data."""

    # Load the harvested data from new DataSource location
    data_file = Path("../DataSource/iso_deliverables_metadata.parquet")
    if not data_file.exists():
        print("ERROR: No harvested data found. Data should be in ../DataSource/")
        print("Available data files:")
        data_dir = Path("../DataSource")
        if data_dir.exists():
            for file in data_dir.iterdir():
                if file.is_file():
                    print(f"  {file.name} ({file.stat().st_size} bytes)")
        return

    df = pd.read_parquet(data_file)
    
    print("=" * 60)
    print("RelationOS Harvesting Results Analysis")
    print("=" * 60)
    print(f"Total Relations Extracted: {len(df)}")
    print(f"Source Standards: {df['source_standard'].nunique()}")
    print()
    
    # Relations by source standard
    print("=== Relations by Source Standard ===")
    standard_counts = df['source_standard'].value_counts()
    for standard, count in standard_counts.items():
        percentage = (count / len(df)) * 100
        print(f"{standard}: {count} relations ({percentage:.1f}%)")
    print()
    
    # Relations by domain
    print("=== Relations by Domain ===")
    domain_counts = df['domain'].value_counts()
    for domain, count in domain_counts.items():
        percentage = (count / len(df)) * 100
        print(f"{domain}: {count} relations ({percentage:.1f}%)")
    print()
    
    # Sample relations by domain
    print("=== Sample Relations by Domain ===")
    for domain in domain_counts.index[:5]:  # Top 5 domains
        domain_relations = df[df['domain'] == domain]['relation_name'].head(3).tolist()
        print(f"{domain}: {domain_relations}")
    print()
    
    # Confidence score distribution
    print("=== Confidence Score Distribution ===")
    print(f"Average Confidence: {df['confidence'].mean():.3f}")
    print(f"Min Confidence: {df['confidence'].min():.3f}")
    print(f"Max Confidence: {df['confidence'].max():.3f}")
    print()
    
    # Unique relation names
    print("=== Top 10 Most Common Relations ===")
    relation_counts = df['relation_name'].value_counts().head(10)
    for relation, count in relation_counts.items():
        print(f"{relation}: {count} occurrences")
    print()
    
    # Data schema preview
    print("=== Data Schema Preview ===")
    print("Columns:", list(df.columns))
    print("Sample row:")
    print(df.iloc[0].to_dict())
    print()
    
    # File size and performance metrics
    file_size = data_file.stat().st_size
    print(f"Output file size: {file_size / 1024 / 1024:.2f} MB")
    print(f"Average relations per PDF: {len(df) / len(df['source_standard'].unique()):.1f}")

if __name__ == "__main__":
    analyze_harvested_relations()
