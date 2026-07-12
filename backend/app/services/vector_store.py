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
            
            if exists:
                try:
                    col_info = client.get_collection(collection_name)
                    # For Qdrant client >= 1.7.0, vectors config might be accessed differently, 
                    # but typically col_info.config.params.vectors.size is available.
                    # Or col_info.config.params.vectors is a VectorParams object.
                    current_size = -1
                    if hasattr(col_info.config.params, 'vectors') and hasattr(col_info.config.params.vectors, 'size'):
                        current_size = col_info.config.params.vectors.size
                    elif isinstance(col_info.config.params.vectors, dict) and 'size' in col_info.config.params.vectors:
                        current_size = col_info.config.params.vectors['size']
                        
                    if current_size != -1 and current_size != vector_size:
                        logger.warning(f"Collection {collection_name} dimension mismatch: expected {vector_size}, got {current_size}. Recreating collection.")
                        client.delete_collection(collection_name)
                        exists = False
                except Exception as e:
                    logger.warning(f"Failed to check collection dimension for {collection_name}: {e}")

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
                col_info = client.get_collection(collection_name)
                # Check dimension fallback
                current_size = -1
                if hasattr(col_info.config.params, 'vectors') and hasattr(col_info.config.params.vectors, 'size'):
                    current_size = col_info.config.params.vectors.size
                
                if current_size != -1 and current_size != vector_size:
                    logger.warning(f"Collection {collection_name} dimension mismatch (fallback): expected {vector_size}, got {current_size}. Recreating collection.")
                    client.delete_collection(collection_name)
                    client.create_collection(
                        collection_name=collection_name,
                        vectors_config=models.VectorParams(size=vector_size, distance=models.Distance.COSINE)
                    )
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
            point_id = chunk.get("id") or str(uuid.uuid4())
            
            payload = {
                "workspace_id": str(workspace_id),
                "document_id": str(document_id),
                "chunk_id": point_id,
                "page": chunk.get("page_number", 1),
                "department": document_metadata.get("department", "General"),
                "heading": chunk.get("heading", ""),
                "document_type": chunk.get("document_type", "GENERAL"),
                "metadata": document_metadata,
                "text": chunk["text"]
            }

            points.append(
                models.PointStruct(
                    id=point_id,
                    vector=embeddings[idx],
                    payload=payload
                )
            )

        print("\n========== UPLOAD PAYLOAD ==========")
        if points:
            print(points[0].payload)
        print("===================================\n")
        
        try:

            client.upsert(
                collection_name=collection_name,
                points=points
            )

        except Exception as e:

            logger.exception(e)

            raise
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

        search_response = client.query_points(
            collection_name=collection_name,
            query=query_vector,
            query_filter=workspace_filter,
            limit=limit,
            with_payload=True
        )
        search_results = search_response.points

        print("\n========== QDRANT COLLECTION INFO ==========")
        try:
            info = client.get_collection(collection_name)
            print(f"points_count = {info.points_count}")
            vectors = info.config.params.vectors
            size = vectors.size if hasattr(vectors, 'size') else vectors.get('size') if isinstance(vectors, dict) else 'Unknown'
            print(f"vector size = {size}")
        except Exception as e:
            print(f"Error getting collection info: {e}")
            
        print("\n========== RAW SEARCH ==========")
        print("Workspace:", workspace_id)
        print("Hits:", len(search_results))

        for hit in search_results:
            print(
                hit.score,
                hit.payload.get("document_id"),
                hit.payload.get("text", "")[:100]
            )
        print("===============================\n")

        results = []
        for hit in search_results:
            payload = hit.payload
            
            results.append({

                "id":hit.id,
                "score":hit.score,
                "text":payload.get("text", ""),
                "document_id":payload.get("document_id", ""),
                "chunk_id":payload.get("chunk_id", ""),
                "page_number":payload.get("page", 1),
                "heading":payload.get("heading", ""),
                "department":payload.get("department", "General"),
                "document_type":payload.get("document_type", "General"),
                "equipment":payload.get("metadata", {}).get("machines", []),
                "title":payload.get("metadata", {}).get("title", "")

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

   