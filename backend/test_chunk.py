from app.services.extractor import DocumentExtractor
from app.services.chunker import TextChunker
import json

file_path = "uploads/6a46a471f2dc6443864b4b46/1783457786_Pump_P101_Manual.pdf"

extraction = DocumentExtractor.extract(file_path)
print(f"Extraction success: {extraction.success}")
print(f"Extracted characters: {len(extraction.text)}")
print(f"Extracted words: {len(extraction.text.split())}")

from app.core.config import settings

chunks = TextChunker.chunk_text(
    extraction.text, 
    chunk_size=settings.CHUNK_SIZE, 
    chunk_overlap=settings.CHUNK_OVERLAP
)
print(f"Number of chunks: {len(chunks)}")
if chunks:
    print(f"First chunk length: {len(chunks[0]['text'])}")
    print(f"First chunk text: {chunks[0]['text'][:200]}")
