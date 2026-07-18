import os
import logging
from datetime import datetime, UTC
from app.models.document import DocumentModel, DocumentStatus
from app.services.extractor import DocumentExtractor
from app.services.chunker import TextChunker
from app.services.embedding_service import EmbeddingService
from app.services.vector_store import VectorStoreService
from app.services.metadata_service import MetadataExtractor
from app.services.drawing_classifier import DrawingClassifier
from app.services.drawing_pipeline import DrawingPipeline
from app.services.ai.graph.graph_builder import graph_builder
from app.core.config import settings

logger = logging.getLogger(__name__)

BASE_DIR = os.path.dirname(
    os.path.dirname(
        os.path.dirname(os.path.abspath(__file__))
    )
)

class DocumentPipeline:
    @staticmethod
    async def update_status(
        document: DocumentModel,
        status: DocumentStatus,
        progress: int,
        current_step: str,
        error: str | None = None,
    ):
        doc_exists = await DocumentModel.get(document.id)
        if not doc_exists:
            raise ValueError("Document was deleted during processing.")
            
        document.status = status
        document.processing_progress = progress
        document.current_step = current_step
        document.updated_at = datetime.now(UTC)
        if error:
            document.error_message = error
        await document.save()

    @staticmethod
    async def process_document(document_id: str):
        doc = await DocumentModel.get(document_id)
        if doc is None:
            logger.error(f"Document {document_id} not found.")
            return

        try:
            logger.info(f"Pipeline started for {doc.name}")

            abs_path = os.path.join(BASE_DIR, doc.storage_path)
            if not os.path.exists(abs_path):
                raise FileNotFoundError(f"File not found: {abs_path}")

            # 1. EXTRACTION
            await DocumentPipeline.update_status(
                document=doc,
                status=DocumentStatus.EXTRACTING,
                progress=10,
                current_step="Extracting text"
            )
            logger.info("Starting extraction...")
            extraction = DocumentExtractor.extract(abs_path)

            if not extraction.success:
                raise Exception(f"Extraction failed: {extraction.error}")

            text = extraction.text
            if not text.strip():
                raise Exception("No text extracted.")

            # OCR Step (Only if used_ocr is true)
            if extraction.used_ocr:
                await DocumentPipeline.update_status(
                    document=doc,
                    status=DocumentStatus.OCR,
                    progress=25,
                    current_step="Applying OCR"
                )

            # 2. METADATA
            await DocumentPipeline.update_status(
                document=doc,
                status=DocumentStatus.METADATA,
                progress=40,
                current_step="Extracting metadata"
            )
            logger.info("Extracting metadata...")
            metadata = MetadataExtractor.extract_metadata(text, doc.name)

            # Check if Engineering Drawing
            is_drawing, drawing_type = DrawingClassifier.is_drawing(text, doc.name)
            if is_drawing:
                await DocumentPipeline.update_status(
                    document=doc,
                    status=DocumentStatus.METADATA,
                    progress=50,
                    current_step="Extracting Drawing Intelligence"
                )
                entity_chunks, metadata = DrawingPipeline.process_drawing(
                    abs_path, metadata, drawing_type, text
                )


            # 3. CHUNKING
            await DocumentPipeline.update_status(
                document=doc,
                status=DocumentStatus.CHUNKING,
                progress=55,
                current_step="Chunking document"
            )
            logger.info("Creating chunks...")
            if is_drawing:
                chunks = [{"text": c, "metadata": {}} for c in entity_chunks]
            else:
                chunks = TextChunker.chunk_text(
                    text=text,
                    chunk_size=settings.CHUNK_SIZE,
                    chunk_overlap=settings.CHUNK_OVERLAP,
                )

            if not chunks:
                raise Exception("Chunking produced 0 chunks.")
            
            doc.chunk_count = len(chunks)

            # 4. EMBEDDING
            await DocumentPipeline.update_status(
                document=doc,
                status=DocumentStatus.EMBEDDING,
                progress=75,
                current_step="Generating embeddings"
            )
            logger.info("Generating embeddings...")
            chunk_texts = [chunk["text"] for chunk in chunks]
            embeddings = await EmbeddingService.get_embeddings(chunk_texts)

            if not embeddings:
                raise Exception("Embedding generation failed.")

            doc.embedding_count = len(embeddings)

            # 5. INDEXING
            await DocumentPipeline.update_status(
                document=doc,
                status=DocumentStatus.INDEXING,
                progress=90,
                current_step="Indexing in vector store"
            )
            logger.info("Uploading vectors...")
            collection = settings.QDRANT_COLLECTION_NAME or "documents_general"
            await VectorStoreService.upsert_chunks(
                collection_name=collection,
                workspace_id=doc.workspace_id,
                document_id=str(doc.id),
                chunks=chunks,
                embeddings=embeddings,
                document_metadata=metadata,
            )

            # 6. KNOWLEDGE GRAPH
            await DocumentPipeline.update_status(
                document=doc,
                status=DocumentStatus.INDEXING,
                progress=95,
                current_step="Building Knowledge Graph"
            )
            logger.info("Building Knowledge Graph...")
            # Fire and forget graph building, or await it. Let's await it to ensure it completes before READY
            await graph_builder.build_from_chunks(
                chunks=chunks,
                document_id=str(doc.id),
                document_name=doc.name
            )

            # 7. READY
            knowledge_score = (
                metadata.get("confidence_score", 0.70)
                + metadata.get("completeness_score", 0.70)
            ) / 2

            doc.metadata = metadata
            doc.department = metadata.get("department", "General")
            doc.knowledge_score = round(knowledge_score, 2)
            doc.processing_completed_at = datetime.now(UTC)
            doc.error_message = None

            await DocumentPipeline.update_status(
                document=doc,
                status=DocumentStatus.READY,
                progress=100,
                current_step="Completed"
            )
            logger.info(f"Pipeline completed successfully for {doc.name}")

        except Exception as e:
            logger.exception(e)
            if str(e) == "Document was deleted during processing.":
                logger.info(f"Pipeline aborted: Document {document_id} was deleted.")
                return
                
            try:
                await DocumentPipeline.update_status(
                    document=doc,
                    status=DocumentStatus.FAILED,
                    progress=doc.processing_progress,
                    current_step="Failed",
                    error=str(e),
                )
            except ValueError as ve:
                if str(ve) == "Document was deleted during processing.":
                    pass