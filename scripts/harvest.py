#!/usr/bin/env python3
"""
RelationOS Harvester v2.0 – Enhanced Edition
Supports PyMuPDF + pandas + parquet with robust error handling
"""

import os
import sys
import re
import json
import logging
import hashlib
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Optional
from concurrent.futures import ThreadPoolExecutor, as_completed
import pandas as pd
import fitz  # PyMuPDF

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class PDFHarvester:
    def __init__(self, config_path: str = "../config/harvester_config.json"):
        self.config = self._load_config(config_path)
        self.data_dir = Path("../data")
        self.harvest_dir = Path("../docs/harvesting")
        self.output_file = self.data_dir / "relations_harvested.parquet"
        
        # Pre-compiled regex patterns
        self.patterns = [
            re.compile(r'«([\w]+)»', re.IGNORECASE),
            re.compile(r'([A-Z][\w]*)\s+(relationship|relation)', re.IGNORECASE),
            re.compile(r'(satisfies|refines|allocates|verifies|derives|traces\s*to|composes|aggregates|calls)\s+([\w]+)', re.IGNORECASE),
        ]
        
        # Domain patterns
        self.domain_patterns = {
            'traceability': ["satisfies", "refines", "allocates", "verifies", "derives", "traces"],
            'structural': ["composition", "aggregation", "association", "generalization"],
            'behavioral': ["calls", "sends", "flow", "precedes"],
            'interface': ["connects", "implements", "realizes"],
            'safety': ["prevents", "causes", "mitigates"],
            'security': ["authenticate", "authorize", "encrypt"],
            'temporal': ["before", "after", "during", "concurrent"]
        }

    def _load_config(self, config_path: str) -> Dict:
        """Load harvester configuration."""
        try:
            with open(config_path, 'r') as f:
                return json.load(f)
        except Exception:
            return {
                'confidence_threshold': 0.85,
                'batch_size': 1000,
                'max_file_size_mb': 500,
                'parallel_processing': True
            }

    def validate_pdf(self, pdf_path: Path) -> bool:
        """Validate PDF file before processing."""
        if not pdf_path.exists():
            logger.error(f"PDF file not found: {pdf_path}")
            return False
            
        if pdf_path.stat().st_size > self.config['max_file_size_mb'] * 1024 * 1024:
            logger.warning(f"PDF file too large: {pdf_path} ({pdf_path.stat().st_size / 1024 / 1024:.1f}MB)")
            
        try:
            doc = fitz.open(pdf_path)
            if len(doc) == 0:
                logger.error(f"Empty PDF: {pdf_path}")
                return False
            doc.close()
            return True
        except Exception as e:
            logger.error(f"Invalid PDF {pdf_path}: {e}")
            return False

    def classify_domain(self, relation_name: str) -> str:
        """Classify relation into appropriate domain."""
        name_lower = relation_name.lower()
        for domain, keywords in self.domain_patterns.items():
            if any(keyword in name_lower for keyword in keywords):
                return domain.title()
        return "Uncategorized"

    def extract_relations_from_page(self, page_text: str, page_num: int, pdf_name: str) -> List[Dict]:
        """Extract relations from a single page."""
        relations = []
        
        for pattern in self.patterns:
            try:
                for match in pattern.finditer(page_text):
                    if match.groups():
                        rel_name = match.group(1) if len(match.groups()) >= 1 else match.group(0)
                        rel_name = rel_name.strip('«»').title()
                        
                        # Generate unique ID
                        content_hash = hashlib.md5(f"{pdf_name}_{page_num}_{rel_name}".encode()).hexdigest()[:8]
                        
                        relation = {
                            'id': f"{pdf_name}_{content_hash}",
                            'source_standard': pdf_name.replace('.pdf', ''),
                            'source_document': pdf_name,
                            'relation_name': rel_name,
                            'domain': self.classify_domain(rel_name),
                            'page': page_num + 1,
                            'confidence': self.config['confidence_threshold'],
                            'harvested_at': datetime.now().isoformat(),
                            'extraction_method': 'regex_pattern'
                        }
                        relations.append(relation)
            except Exception as e:
                logger.warning(f"Pattern matching failed on page {page_num}: {e}")
                continue
                
        return relations

    def process_single_pdf(self, pdf_path: Path) -> List[Dict]:
        """Process a single PDF file with error handling."""
        if not self.validate_pdf(pdf_path):
            return []
            
        logger.info(f"Processing: {pdf_path.name}")
        relations = []
        
        try:
            with fitz.open(pdf_path) as doc:
                for page_num in range(len(doc)):
                    try:
                        page = doc.load_page(page_num)
                        text = page.get_text("text")
                        if text.strip():
                            page_relations = self.extract_relations_from_page(text, page_num, pdf_path.stem)
                            relations.extend(page_relations)
                    except Exception as e:
                        logger.warning(f"Failed to process page {page_num} in {pdf_path.name}: {e}")
                        continue
                        
        except Exception as e:
            logger.error(f"Failed to process PDF {pdf_path.name}: {e}")
            
        logger.info(f"Extracted {len(relations)} relations from {pdf_path.name}")
        return relations

    def save_relations(self, relations: List[Dict]) -> bool:
        """Save relations to Parquet with deduplication."""
        if not relations:
            logger.info("No relations to save")
            return True
            
        try:
            new_df = pd.DataFrame(relations)
            
            if self.output_file.exists():
                old_df = pd.read_parquet(self.output_file)
                # Deduplicate based on source document, relation name, and page
                combined_df = pd.concat([old_df, new_df], ignore_index=True)
                deduplicated_df = combined_df.drop_duplicates(
                    subset=['source_document', 'relation_name', 'page'], 
                    keep='first'
                )
            else:
                deduplicated_df = new_df
                
            # Create data directory if it doesn't exist
            self.data_dir.mkdir(exist_ok=True)
            
            deduplicated_df.to_parquet(self.output_file, index=False)
            logger.info(f"Saved {len(deduplicated_df)} total relations to {self.output_file}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to save relations: {e}")
            return False

    def run_harvest(self) -> bool:
        """Main harvesting process."""
        logger.info("Starting RelationOS harvesting process...")
        
        pdf_files = list(self.harvest_dir.glob("*.pdf"))
        if not pdf_files:
            logger.error("No PDF files found in docs/harvesting/")
            return False
            
        logger.info(f"Found {len(pdf_files)} PDF files to process")
        
        all_relations = []
        
        if self.config['parallel_processing']:
            # Parallel processing
            with ThreadPoolExecutor(max_workers=4) as executor:
                future_to_pdf = {
                    executor.submit(self.process_single_pdf, pdf_path): pdf_path 
                    for pdf_path in pdf_files
                }
                
                for future in as_completed(future_to_pdf):
                    pdf_path = future_to_pdf[future]
                    try:
                        relations = future.result()
                        all_relations.extend(relations)
                    except Exception as e:
                        logger.error(f"Failed to process {pdf_path.name}: {e}")
        else:
            # Sequential processing
            for pdf_path in pdf_files:
                relations = self.process_single_pdf(pdf_path)
                all_relations.extend(relations)
        
        success = self.save_relations(all_relations)
        
        if success:
            logger.info("RelationOS harvesting completed successfully!")
        else:
            logger.error("RelationOS harvesting failed!")
            
        return success

if __name__ == "__main__":
    harvester = PDFHarvester()
    success = harvester.run_harvest()
    sys.exit(0 if success else 1)
