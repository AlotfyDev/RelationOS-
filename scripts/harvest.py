#!/usr/bin/env python3
"""
RelationOS ML-Powered Harvester v3.0 – Smart Semantic Classification
Uses ML classifiers instead of primitive regex patterns for superior accuracy
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

# ML Classifiers - REPLACING regex with intelligent semantic analysis
try:
    from analyzer.models.transformer.sklearn_fallback import SklearnFallbackClassifier
    from analyzer.models.transformer.relation_types import ExpertParameters, ClassificationMode
    ML_AVAILABLE = True
except ImportError:
    ML_AVAILABLE = False
    logger.warning("⚠️ ML classifiers not available - falling back to regex patterns")

class PDFHarvester:
    def __init__(self, config_path: str = None):
        if config_path is None:
            # Get script directory and calculate project root
            script_dir = Path(__file__).parent
            project_root = script_dir.parent
            config_path = str(project_root / "config" / "harvester_config.json")

        self.config = self._load_config(config_path)

        # Calculate paths from script location
        script_dir = Path(__file__).parent
        project_root = script_dir.parent
        self.data_dir = project_root / "data"
        self.harvest_dir = project_root / "docs" / "harvesting"
        self.output_file = self.data_dir / "relations_harvested.parquet"

        # 🚀 ML CLASSIFIERS - DEFAULT APPROACH INSTEAD OF REGEX
        self.ml_classifier = None
        if ML_AVAILABLE:
            # Initialize ML classifier with expert parameters for maximum accuracy
            expert_params = ExpertParameters(
                sysml_boost=1.3,      # Boost MBSE-specific relations
                uml_boost=1.1,        # Boost modeling relations
                context_window_size=300,  # Larger context window for better understanding
                use_context_window=True,
                confidence_threshold=0.8    # High accuracy threshold
            )

            logger.info("🎯 Initializing ML classifier - replacing primitive regex patterns")
            try:
                self.ml_classifier = SklearnFallbackClassifier(
                    mode=ClassificationMode.MODE_STANDARD,
                    expert_params=expert_params
                )

                if self.ml_classifier.initialize():
                    logger.info("✅ ML classifier initialized - intelligent semantic analysis ready!")
                else:
                    logger.warning("⚠️ ML classifier failed to initialize - using fallback methods")
                    self.ml_classifier = None

            except Exception as e:
                logger.warning(f"⚠️ ML classifier initialization failed: {e} - using fallback methods")
                self.ml_classifier = None

        else:
            logger.warning("❌ ML classifiers not available - regex fallback in use")

        # Fallback patterns only if ML is not available
        if self.ml_classifier is None:
            logger.warning("🔄 Using primitive regex patterns due to ML unavailability")
            self.patterns = [
                re.compile(r'«([\w]+)»', re.IGNORECASE),
                re.compile(r'([A-Z][\w]*)\s+(relationship|relation)', re.IGNORECASE),
                re.compile(r'(satisfies|refines|allocates|verifies|derives|traces\s*to|composes|aggregates|calls)\s+([\w]+)', re.IGNORECASE),
            ]

            # Domain patterns (legacy fallback)
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
        """Extract relations intelligently using ML classifier instead of primitive regex."""
        relations = []

        # 🌟 USE ML CLASSIFIER - DEFAULT EXTRACTION METHOD 🌟
        if self.ml_classifier and self.ml_classifier.is_ready_for_inference():
            try:
                logger.info(f"🎯 Using ML classifier for page {page_num + 1} - intelligent semantic analysis")

                # Strategy: Find potential relation entities first, then classify them
                # This replaces primitive regex pattern matching with semantic understanding

                # 1. Split page text into sentence/context fragments
                sentences = self._split_text_into_contexts(page_text, window_size=300)
                logger.info(f"   📄 Processing {len(sentences)} text fragments for semantic analysis")

                relations_found = []

                # 2. Process each context fragment with ML classification
                for i, context in enumerate(sentences):
                    logger.info(f"   🔬 Fragment {i+1}/{len(sentences)}: '{context[:50]}...'")

                    # Extract potential relations from this context using ML
                    context_relations = self._extract_relations_from_context_ml(
                        context, page_num, pdf_name, f"ctx_{i}"
                    )
                    relations_found.extend(context_relations)

                    if i > 0 and i % 10 == 0:  # Progress indication
                        logger.info(f"   📊 Processed {i}/{len(sentences)} fragments - {len(relations_found)} relations found")

                relations.extend(relations_found)
                logger.info(f"   ✅ ML extraction complete: {len(relations)} relations from page {page_num + 1}")

            except Exception as e:
                logger.warning(f"⚠️ ML extraction failed for page {page_num}, falling back to regex: {e}")
                return self._extract_relations_fallback_regex(page_text, page_num, pdf_name)

        # 🔄 FALLBACK: Use primitive regex patterns if ML unavailable
        else:
            logger.warning(f"♻️ Using regex fallback for page {page_num + 1}")
            relations = self._extract_relations_fallback_regex(page_text, page_num, pdf_name)

        return relations

    def _split_text_into_contexts(self, text: str, window_size: int = 300) -> List[str]:
        """Split text into context fragments for ML analysis."""
        if not text.strip():
            return []

        # Split by sentences/paragraphs
        import re
        sentences = re.split(r'(?<=[.!?\n])\s+', text)

        contexts = []
        current_context = ""
        current_length = 0

        for sentence in sentences:
            if current_length + len(sentence) <= window_size:
                current_context += sentence + " "
                current_length += len(sentence) + 1
            else:
                if current_context.strip():
                    contexts.append(current_context.strip())
                current_context = sentence + " "
                current_length = len(sentence) + 1

        if current_context.strip():
            contexts.append(current_context.strip())

        return contexts if contexts else [text]  # Fallback to full text

    def _extract_relations_from_context_ml(self, context: str, page_num: int, pdf_name: str, context_id: str) -> List[Dict]:
        """Use ML classifier to extract relations from text context."""
        relations = []

        try:
            # Strategy: Search for potential relation keywords and entities
            # Then use ML classifier for intelligent validation

            relation_words = [
                "satisfies", "refines", "allocates", "verifies", "derives", "traces",
                "composes", "aggregates", "calls", "connects", "implements", "realizes",
                "prevents", "causes", "mitigates", "authenticates", "authorizes", "encrypts",
                "before", "after", "during", "concurrent"
            ]

            # Find potential relation mentions
            context_lower = context.lower()
            found_relations = []

            for word in relation_words:
                if word in context_lower:
                    # Extract phrase around the relation word
                    start = max(0, context_lower.find(word) - 50)
                    end = min(len(context), context_lower.find(word) + len(word) + 50)
                    phrase = context[start:end].strip()

                    found_relations.append({
                        'text': phrase,
                        'relation_word': word,
                        'context': context
                    })

            # Also extract text in angle brackets «relation»
            angle_matches = re.findall(r'«([\w\s]+)»', context)
            for angle_match in angle_matches:
                if any(word in angle_match.lower() for word in relation_words):
                    found_relations.append({
                        'text': angle_match,
                        'relation_word': None,
                        'context': context
                    })

            # Use ML classifier to validate and classify each found relation
            for found in found_relations:
                try:
                    # Classify the relation using ML
                    result = self.ml_classifier.classify_relation(
                        found['text'],
                        found['context']
                    )

                    # Only include high-confidence classifications
                    if result.confidence >= self.config['confidence_threshold']:
                        # Generate unique ID
                        content_hash = hashlib.md5(
                            f"{pdf_name}_{page_num}_{found['text']}_{context_id}".encode()
                        ).hexdigest()[:8]

                        relation_data = {
                            'id': f"{pdf_name}_{content_hash}",
                            'source_standard': pdf_name.replace('.pdf', ''),
                            'source_document': pdf_name,
                            'relation_name': found['text'],
                            'domain': result.primary_domain,
                            'page': page_num + 1,
                            'confidence': result.confidence,
                            'harvested_at': datetime.now().isoformat(),
                            'extraction_method': 'ml_intelligence',  # ✨ NEW: ML classification instead of regex!
                            'relation_word': found['relation_word'],
                            'context_snippet': found['context'][:200] + "..." if len(found['context']) > 200 else found['context'],
                            'alternative_domains': result.alternative_domains,
                            'feature_contributions': result.feature_contributions
                        }

                        relations.append(relation_data)

                except Exception as e:
                    logger.debug(f"ML classification failed for '{found['text'][:50]}...': {e}")
                    continue

        except Exception as e:
            logger.warning(f"ML extraction failed for context: {e}")

        return relations

    def _extract_relations_fallback_regex(self, page_text: str, page_num: int, pdf_name: str) -> List[Dict]:
        """Fallback: Use primitive regex patterns when ML is unavailable."""
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
                            'extraction_method': 'regex_fallback'  # Indicates fallback usage
                        }
                        relations.append(relation)
            except Exception as e:
                logger.warning(f"Pattern matching failed on page {page_num}: {e}")

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
