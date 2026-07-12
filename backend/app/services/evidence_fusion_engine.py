"""
EvidenceFusionEngine
====================
Sprint 9 — Industrial Intelligence Copilot

Reranks, deduplicates, and merges overlapping chunks before passing 
them to the Reasoning Layer. This ensures the Copilot synthesizes 
across entire documents rather than fragmented sentences.
"""

import logging
from typing import Any, Dict, List
from collections import defaultdict

logger = logging.getLogger(__name__)

class EvidenceFusionEngine:

    @staticmethod
    def fuse(chunks: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Takes raw chunks from vector store, removes duplicates, 
        and groups/merges them by document to provide cohesive context.
        """
        if not chunks:
            return []

        # 1. Deduplicate by exact text
        unique_chunks = []
        seen_texts = set()
        for chunk in chunks:
            text = chunk.get("text", "").strip()
            if not text or text in seen_texts:
                continue
            seen_texts.add(text)
            unique_chunks.append(chunk)

        # 2. Group by document
        doc_groups = defaultdict(list)
        for chunk in unique_chunks:
            doc_id = chunk.get("document_id", "unknown_doc")
            doc_groups[doc_id].append(chunk)

        fused_chunks = []
        
        # 3. Merge within each document
        for doc_id, doc_chunks in doc_groups.items():
            # Sort by page number, then by score descending
            doc_chunks.sort(key=lambda x: (int(x.get("page_number") or 0), -x.get("ranked_score", 0)))
            
            # For simplicity, we just concatenate the text for the document, 
            # taking the max score and using the first chunk's metadata as base.
            base_chunk = doc_chunks[0].copy()
            max_score = max((c.get("ranked_score", 0) for c in doc_chunks), default=base_chunk.get("ranked_score", 0))
            
            combined_texts = []
            pages = set()
            for c in doc_chunks:
                page = c.get("page_number")
                if page:
                    pages.add(str(page))
                combined_texts.append(c.get("text", ""))
                
            base_chunk["text"] = "\n...\n".join(combined_texts)
            base_chunk["ranked_score"] = max_score
            base_chunk["score"] = max(c.get("score", 0) for c in doc_chunks) # preserve raw Qdrant score
            if pages:
                # We'll keep it as the first page for integer fields, but add a string field for display if needed.
                # EvidenceService expects int for page_number, so we leave the base_chunk's page_number as is,
                # but we can add `pages_covered`.
                base_chunk["pages_covered"] = ", ".join(sorted(pages))
                
            fused_chunks.append(base_chunk)
            
        # 4. Rerank final fused chunks by highest score
        fused_chunks.sort(key=lambda x: x.get("ranked_score", 0), reverse=True)
        
        logger.info(f"[EVIDENCE FUSION] Reduced {len(chunks)} raw chunks to {len(fused_chunks)} fused document contexts.")
        return fused_chunks
