import os
import logging
from datetime import datetime, UTC
from app.models.document import DocumentModel
from app.services.extractor import DocumentExtractor
from app.services.chunker import TextChunker
from app.services.embedding_service import EmbeddingService
from app.services.vector_store import VectorStoreService
from app.services.metadata_extractor import MetadataExtractor
from app.core.config import settings

logger = logging.getLogger(__name__)

# Resolve base dir for local uploads
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

class DocumentPipeline:

    @staticmethod
    async def process_document(document_id: str):
        """
        Asynchronously runs the full Phase 2 document ingestion pipeline.
        Status transitions: uploaded -> processing -> embedding -> ready (or failed)
        """
        doc = await DocumentModel.get(document_id)
        if not doc:
            logger.error(f"Ingestion Pipeline error: Document {document_id} not found in database.")
            return

        try:
            # 1. Update status to 'processing'
            doc.status = "processing"
            doc.learning_progress = 0.2
            doc.updated_at = datetime.now(UTC)
            await doc.save()
            logger.info(f"Pipeline started for document {document_id} ({doc.name})")

            # Resolve absolute storage path
            abs_path = os.path.join(BASE_DIR, doc.storage_path)
            if not os.path.exists(abs_path):
                raise FileNotFoundError(f"Document file not found on disk at {abs_path}")

            # 2. Extract Text
            text = DocumentExtractor.extract_text(abs_path)
            if not text or not text.strip():
                raise ValueError("No text content could be extracted from document.")
            logger.info(f"Successfully extracted {len(text)} characters from {doc.name}")

            # Update progress
            doc.learning_progress = 0.4
            await doc.save()

            # 3. Intelligent Chunking
            chunks = TextChunker.chunk_text(
                text=text, 
                chunk_size=settings.CHUNK_SIZE, 
                chunk_overlap=settings.CHUNK_OVERLAP
            )
            if not chunks:
                raise ValueError("Intelligent chunker returned 0 chunks from text.")
            logger.info(f"Chunked document {doc.name} into {len(chunks)} segments.")

            # Update progress & state
            doc.status = "embedding"
            doc.learning_progress = 0.6
            doc.chunk_count = len(chunks)
            await doc.save()

            # 4. Extract Structured Metadata
            metadata = MetadataExtractor.extract_metadata(text, doc.name)
            logger.info(f"Extracted metadata keys: {list(metadata.keys())}")

            # 5. Embed Chunks
            chunk_texts = [chunk["text"] for chunk in chunks]
            embeddings = await EmbeddingService.get_embeddings(chunk_texts)
            if not embeddings:
                raise ValueError("Embedding service returned empty embeddings.")
            logger.info(f"Generated embeddings for {len(embeddings)} chunks.")

            # Update progress
            doc.learning_progress = 0.8
            await doc.save()

            # 6. Index into Qdrant Vector DB
            collection = settings.QDRANT_COLLECTION_NAME or "documents_general"
            await VectorStoreService.upsert_chunks(
                collection_name=collection,
                workspace_id=doc.workspace_id,
                document_id=str(doc.id),
                chunks=chunks,
                embeddings=embeddings,
                document_metadata=metadata
            )

            # Calculate metrics
            knowledge_score = (metadata.get("confidence_score", 0.7) + metadata.get("completeness_score", 0.7)) / 2.0

            # 7. Final Success State Update
            doc.status = "ready"
            doc.learning_progress = 1.0
            doc.embedding_count = len(embeddings)
            doc.extracted_metadata = metadata
            doc.knowledge_score = round(knowledge_score, 2)
            doc.department = metadata.get("department", "General")
            doc.error_message = None
            doc.updated_at = datetime.now(UTC)
            await doc.save()
            
            logger.info(f"Pipeline completed successfully for document {document_id}")

        except Exception as e:
            logger.error(f"Pipeline failed for document {document_id}: {str(e)}", exc_info=True)
            doc.status = "failed"
            doc.learning_progress = 0.0
            doc.error_message = str(e)
            doc.updated_at = datetime.now(UTC)
            await doc.save()
