import re
from typing import List, Dict, Any

class TextChunker:
    @staticmethod
    def chunk_text(text: str, chunk_size: int = 512, chunk_overlap: int = 64) -> List[Dict[str, Any]]:
        """
        Intelligently splits text into chunks of roughly `chunk_size` words, 
        with `chunk_overlap` words overlap, while respecting sentence boundaries
        and tracking page/slide/sheet offsets.
        """
        if not text or not text.strip():
            return []

        # Normalize spacing
        text = re.sub(r'\r\n', '\n', text)

        # Detect virtual pages/sheets/slides from extraction markup
        # Format: --- Slide X --- or --- Sheet: Y ---
        pattern = r"(--- Slide \d+ ---|--- Sheet: .*? ---)"
        parts = re.split(pattern, text)
        
        sections = []
        if len(parts) == 1:
            sections.append({"page": 1, "text": text})
        else:
            current_page = 1
            i = 0
            while i < len(parts):
                part = parts[i]
                if not part:
                    i += 1
                    continue
                match_slide = re.match(r"--- Slide (\d+) ---", part)
                match_sheet = re.match(r"--- Sheet: (.*?) ---", part)
                if match_slide:
                    current_page = int(match_slide.group(1))
                elif match_sheet:
                    current_page = (i // 2) + 1
                else:
                    sections.append({"page": current_page, "text": part})
                i += 1

        chunks = []
        chunk_idx = 0

        for sec in sections:
            page_num = sec["page"]
            sec_text = sec["text"].strip()
            if not sec_text:
                continue

            # Split by paragraph/sentence borders
            sentences = re.split(r"(?<=[.!?])\s+", sec_text)
            current_chunk_words = []
            current_len = 0

            for sentence in sentences:
                sentence = sentence.strip()
                if not sentence:
                    continue
                words = sentence.split()
                if not words:
                    continue

                # If sentence alone exceeds the limit, split it by words
                if len(words) > chunk_size:
                    if current_chunk_words:
                        chunks.append({
                            "text": " ".join(current_chunk_words),
                            "chunk_index": chunk_idx,
                            "page_number": page_num
                        })
                        chunk_idx += 1
                        current_chunk_words = []
                        current_len = 0
                    
                    # Split the massive sentence into chunks
                    step = chunk_size - chunk_overlap
                    if step <= 0:
                        step = chunk_size // 2
                    for start in range(0, len(words), step):
                        chunk_words = words[start:start + chunk_size]
                        chunks.append({
                            "text": " ".join(chunk_words),
                            "chunk_index": chunk_idx,
                            "page_number": page_num
                        })
                        chunk_idx += 1
                    continue

                if current_len + len(words) <= chunk_size:
                    current_chunk_words.extend(words)
                    current_len += len(words)
                else:
                    # Flush the current chunk
                    chunks.append({
                        "text": " ".join(current_chunk_words),
                        "chunk_index": chunk_idx,
                        "page_number": page_num
                    })
                    chunk_idx += 1

                    # Retain the overlap
                    overlap_start = max(0, len(current_chunk_words) - chunk_overlap)
                    overlap_words = current_chunk_words[overlap_start:]
                    
                    current_chunk_words = overlap_words + words
                    current_len = len(current_chunk_words)

            if current_chunk_words:
                chunks.append({
                    "text": " ".join(current_chunk_words),
                    "chunk_index": chunk_idx,
                    "page_number": page_num
                })
                chunk_idx += 1

        return chunks
