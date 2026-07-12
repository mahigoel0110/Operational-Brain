import logging
from typing import Tuple, Optional

logger = logging.getLogger(__name__)

class DrawingClassifier:
    DRAWING_KEYWORDS = [
        "P&ID", "PFD", "PIPING", "INSTRUMENTATION", 
        "DRAWING", "DWG", "LINE NUMBER", "REVISION", 
        "SCHEMATIC", "FLOW DIAGRAM", "PUMP", "VALVE"
    ]

    @staticmethod
    def is_drawing(text: str, filename: str) -> Tuple[bool, Optional[str]]:
        filename_upper = filename.upper()
        
        # Fast path via filename
        if "P&ID" in filename_upper or "PID" in filename_upper:
            return True, "P&ID"
        if "PFD" in filename_upper:
            return True, "PFD"
        if filename_upper.endswith((".DWG", ".DXF")):
            return True, "CAD Drawing"
            
        # Check text content from initial extraction
        text_upper = text.upper()
        keyword_count = sum(1 for kw in DrawingClassifier.DRAWING_KEYWORDS if kw in text_upper)
        
        if keyword_count >= 2:
            if "P&ID" in text_upper or "PIPING AND INSTRUMENTATION" in text_upper:
                return True, "P&ID"
            if "PFD" in text_upper or "PROCESS FLOW" in text_upper:
                return True, "PFD"
            return True, "Engineering Drawing"
            
        return False, None
