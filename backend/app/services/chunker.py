import re
import uuid
from typing import List, Dict, Any

# Industrial document types (Oil & Gas focused)
DOCUMENT_TYPES = {
    "SOP",
    "WORK INSTRUCTION",
    "MAINTENANCE",
    "MANUAL",
    "INSPECTION",
    "P&ID",
    "JSA",
    "HAZOP",
    "PERMIT TO WORK",
    "EMERGENCY RESPONSE",
}


class TextChunker:

    @staticmethod
    def chunk_text(
        text: str,
        chunk_size: int = 512,
        chunk_overlap: int = 64,
    ) -> List[Dict[str, Any]]:

        """
        Intelligent document chunking.

        - Keeps sentence boundaries.
        - Preserves slide/page numbers.
        - Detects headings.
        - Detects document type.
        - Creates overlapping chunks.
        """

        if not text or not text.strip():
            return []

        text = re.sub(r"\r\n", "\n", text)

        pattern = r"(--- Slide \d+ ---|--- Sheet: .*? ---)"

        parts = re.split(pattern, text)

        sections = []

        if len(parts) == 1:

            sections.append(
                {
                    "page": 1,
                    "text": text,
                }
            )

        else:

            current_page = 1

            i = 0

            while i < len(parts):

                part = parts[i]

                if not part:
                    i += 1
                    continue

                slide = re.match(
                    r"--- Slide (\d+) ---",
                    part,
                )

                sheet = re.match(
                    r"--- Sheet: (.*?) ---",
                    part,
                )

                if slide:

                    current_page = int(slide.group(1))

                elif sheet:

                    current_page = (i // 2) + 1

                else:

                    sections.append(
                        {
                            "page": current_page,
                            "text": part,
                        }
                    )

                i += 1

        chunks = []

        chunk_index = 0

        for section in sections:

            page_number = section["page"]

            sec_text = section["text"].strip()

            if not sec_text:
                continue

            #########################################
            # Detect Heading
            #########################################

            heading = ""

            processed_lines = []

            for line in sec_text.split("\n"):

                line = line.strip()

                if not line:
                    continue

                if len(line) < 80 and line.isupper():
                    heading = line

                processed_lines.append(line)

            sec_text = "\n".join(processed_lines)

            #########################################
            # Detect Document Type
            #########################################

            document_type = "GENERAL"

            upper = sec_text.upper()

            for doc_type in DOCUMENT_TYPES:

                if doc_type in upper:

                    document_type = doc_type

                    break

            #########################################
            # Sentence Split
            #########################################

            sentences = re.split(
                r"(?<=[.!?])\s+",
                sec_text,
            )

            current_chunk = []

            current_length = 0

            #########################################

            for sentence in sentences:

                sentence = sentence.strip()

                if not sentence:
                    continue

                words = sentence.split()

                if not words:
                    continue

                #########################################
                # Very large sentence
                #########################################

                if len(words) > chunk_size:

                    if current_chunk:

                        chunk_text = " ".join(current_chunk)

                        chunks.append(
                            {
                                "id": str(uuid.uuid4()),
                                "text": chunk_text,
                                "chunk_index": chunk_index,
                                "page_number": page_number,
                                "word_count": len(current_chunk),
                                "character_count": len(chunk_text),
                                "heading": heading,
                                "document_type": document_type,
                            }
                        )

                        chunk_index += 1

                        current_chunk = []

                        current_length = 0

                    step = chunk_size - chunk_overlap

                    if step <= 0:
                        step = chunk_size // 2

                    for start in range(
                        0,
                        len(words),
                        step,
                    ):

                        chunk_words = words[
                            start : start + chunk_size
                        ]

                        chunk_text = " ".join(chunk_words)

                        chunks.append(
                            {
                                "id": str(uuid.uuid4()),
                                "text": chunk_text,
                                "chunk_index": chunk_index,
                                "page_number": page_number,
                                "word_count": len(chunk_words),
                                "character_count": len(chunk_text),
                                "heading": heading,
                                "document_type": document_type,
                            }
                        )

                        chunk_index += 1

                    continue

                #########################################
                # Normal chunking
                #########################################

                if current_length + len(words) <= chunk_size:

                    current_chunk.extend(words)

                    current_length += len(words)

                else:

                    chunk_text = " ".join(current_chunk)

                    chunks.append(
                        {
                            "id": str(uuid.uuid4()),
                            "text": chunk_text,
                            "chunk_index": chunk_index,
                            "page_number": page_number,
                            "word_count": len(current_chunk),
                            "character_count": len(chunk_text),
                            "heading": heading,
                            "document_type": document_type,
                        }
                    )

                    chunk_index += 1

                    overlap_start = max(
                        0,
                        len(current_chunk) - chunk_overlap,
                    )

                    overlap_words = current_chunk[
                        overlap_start:
                    ]

                    current_chunk = overlap_words + words

                    current_length = len(current_chunk)

            #########################################

            if current_chunk:

                chunk_text = " ".join(current_chunk)

                chunks.append(
                    {
                        "id": str(uuid.uuid4()),
                        "text": chunk_text,
                        "chunk_index": chunk_index,
                        "page_number": page_number,
                        "word_count": len(current_chunk),
                        "character_count": len(chunk_text),
                        "heading": heading,
                        "document_type": document_type,
                    }
                )

                chunk_index += 1

        return chunks