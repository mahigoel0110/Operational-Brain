import os
import logging
from typing import Dict, Any, Tuple, List

from app.services.vision_detector import VisionDetector
from app.services.drawing_ocr import DrawingOCR
from app.services.relationship_extractor import RelationshipExtractor
from app.services.drawing_metadata_service import DrawingMetadataService

logger = logging.getLogger(__name__)

class DrawingPipeline:
    @staticmethod
    def process_drawing(abs_path: str, base_metadata: Dict[str, Any], drawing_type: str, initial_text: str) -> Tuple[List[str], Dict[str, Any]]:
        logger.info(f"Starting DrawingIntelligence for {abs_path}")
        
        output_dir = os.path.dirname(abs_path)
        
        # 1. Image Extraction (if PDF)
        image_paths = [abs_path]
        if abs_path.lower().endswith(".pdf"):
            logger.info("Extracting images from PDF...")
            image_paths = VisionDetector.extract_images_from_pdf(abs_path, output_dir)
            
        # 2. OCR (Full Drawing OCR fallback/addition)
        logger.info("Applying EasyOCR (Full text pass)...")
        ocr_text = DrawingOCR.extract_text(image_paths)
        
        combined_text = initial_text + "\n" + ocr_text
        
        # 3. Vision Symbol Detection
        logger.info("Detecting Industrial Symbols with OpenCV...")
        symbols = VisionDetector.detect_symbols(image_paths)
        
        # 4. Relationship Extraction
        logger.info("Extracting Relationships...")
        relationships = RelationshipExtractor.extract_relationships(combined_text, symbols)
        
        # 5. Metadata Merging & Dual Output
        logger.info("Generating Dual Output (JSON + Narratives)...")
        rich_metadata, entity_chunks = DrawingMetadataService.format_metadata(
            base_metadata=base_metadata,
            drawing_type=drawing_type,
            text=combined_text,
            symbols=symbols,
            relationships=relationships
        )
        
        return entity_chunks, rich_metadata
