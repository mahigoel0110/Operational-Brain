import os
import uuid
import logging
from typing import List, Dict, Any
from qdrant_client import QdrantClient
from qdrant_client.http import models
from app.core.config import settings

logger = logging.getLogger(__name__)

# Resolve base dir for local vector storage
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

class VectorStoreService:
    _client = None

    @classmethod
    def get_client(cls) -> QdrantClient:
        if cls._client is None:
            qdrant_url = settings.QDRANT_URL or os.getenv("QDRANT_URL")
            if qdrant_url:
                logger.info(f"Connecting to Qdrant server at: {qdrant_url}")
                cls._client = QdrantClient(url=qdrant_url)
            else:
                db_path = os.path.join(BASE_DIR, "qdrant_db")
                logger.info(f"QDRANT_URL not set. Initializing local disk Qdrant database at: {db_path}")
                cls._client = QdrantClient(path=db_path)
        return cls._client

    @classmethod
    def ensure_collection(cls, collection_name: str, vector_size: int):
        client = cls.get_client()
        try:
            exists = client.collection_exists(collection_name)
            if not exists:
                logger.info(f"Creating Qdrant collection: {collection_name} with vector size {vector_size}")
                client.create_collection(
                    collection_name=collection_name,
                    vectors_config=models.VectorParams(
                        size=vector_size,
                        distance=models.Distance.COSINE
                    )
                )
        except Exception as e:
            # Fallback check for older clients if collection_exists is not available
            try:
                client.get_collection(collection_name)
            except Exception:
                logger.info(f"Creating Qdrant collection (fallback path): {collection_name}")
                client.create_collection(
                    collection_name=collection_name,
                    vectors_config=models.VectorParams(
                        size=vector_size,
                        distance=models.Distance.COSINE
                    )
                )

    @classmethod
    async def upsert_chunks(
        cls,
        collection_name: str,
        workspace_id: str,
        document_id: str,
        chunks: List[Dict[str, Any]],
        embeddings: List[List[float]],
        document_metadata: Dict[str, Any]
    ):
        """
        Upserts document chunks and their embeddings into the Qdrant collection.
        Uses payload isolation for workspace workspace_id.
        """
        if not chunks or not embeddings:
            return

        client = cls.get_client()
        vector_size = len(embeddings[0])
        cls.ensure_collection(collection_name, vector_size)

        points = []
        for idx, chunk in enumerate(chunks):
            # Generate a consistent or unique ID
            point_id = str(uuid.uuid4())
            
            payload = {
                "workspace_id": str(workspace_id),
                "document_id": str(document_id),
                "text": chunk["text"],
                "chunk_index": chunk["chunk_index"],
                "page_number": chunk.get("page_number", 1),
                "title": document_metadata.get("title", ""),
                "department": document_metadata.get("department", ""),
                "file_type": document_metadata.get("file_type", ""),
            }

            points.append(
                models.PointStruct(
                    id=point_id,
                    vector=embeddings[idx],
                    payload=payload
                )
            )

        client.upsert(
            collection_name=collection_name,
            points=points
        )
        logger.info(f"Successfully upserted {len(points)} chunks for document {document_id} into Qdrant collection {collection_name}")

    @classmethod
    async def search_workspace(
        cls,
        collection_name: str,
        workspace_id: str,
        query_vector: List[float],
        limit: int = 5
    ) -> List[Dict[str, Any]]:
        """
        Searches workspace-isolated vectors in Qdrant.
        """
        client = cls.get_client()
        
        # Verify collection exists, if not return empty results
        try:
            client.get_collection(collection_name)
        except Exception:
            return []

        # Filter by workspace_id
        workspace_filter = models.Filter(
            must=[
                models.FieldCondition(
                    key="workspace_id",
                    match=models.MatchValue(value=str(workspace_id))
                )
            ]
        )

        search_results = client.search(
            collection_name=collection_name,
            query_vector=query_vector,
            query_filter=workspace_filter,
            limit=limit,
            with_payload=True
        )

        results = []
        for hit in search_results:
            results.append({
                "id": hit.id,
                "score": hit.score,
                "text": hit.payload.get("text", ""),
                "document_id": hit.payload.get("document_id", ""),
                "page_number": hit.payload.get("page_number", 1),
                "title": hit.payload.get("title", ""),
                "department": hit.payload.get("department", ""),
            })
        
        return results

    @classmethod
    async def delete_document_vectors(cls, collection_name: str, document_id: str):
        """
        Deletes all vectors belonging to a specific document.
        """
        client = cls.get_client()
        try:
            client.get_collection(collection_name)
        except Exception:
            return

        client.delete(
            collection_name=collection_name,
            points_selector=models.FilterSelector(
                filter=models.Filter(
                    must=[
                        models.FieldCondition(
                            key="document_id",
                            match=models.MatchValue(value=str(document_id))
                        )
                    ]
                )
            )
        )
        logger.info(f"Deleted vectors for document {document_id} from collection {collection_name}")
