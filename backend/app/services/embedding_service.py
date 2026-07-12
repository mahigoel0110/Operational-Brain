import asyncio
import logging
import os
import random
from typing import List

from openai import OpenAI

from app.core.config import settings

logger = logging.getLogger(__name__)


class EmbeddingService:
    """
    Generates embeddings for document chunks.

    Features:
    - OpenAI embeddings
    - Offline fallback mode
    - Batch processing
    - Retry mechanism
    - Future-ready for local embedding models
    """

    _client = None

    DEFAULT_MODEL = "text-embedding-3-small"

    DEFAULT_DIMENSION = 1536

    BATCH_SIZE = 100

    MAX_RETRIES = 3

    @classmethod
    def get_client(cls):

        if cls._client is not None:
            return cls._client

        api_key = settings.OPENAI_API_KEY or os.getenv("OPENAI_API_KEY")

        if not api_key:

            logger.warning(
                "OPENAI_API_KEY not configured. Running in offline embedding mode."
            )

            return None

        cls._client = OpenAI(api_key=api_key)

        return cls._client

    @staticmethod
    def clean_text(text: str) -> str:
        """
        Normalize whitespace before embedding.
        """

        return " ".join(text.split())

    @classmethod
    async def get_embeddings(
        cls,
        texts: List[str],
        model: str | None = None,
    ) -> List[List[float]]:

        if not texts:
            return []

        model_name = model or settings.EMBEDDING_MODEL or cls.DEFAULT_MODEL

        texts = [cls.clean_text(t) for t in texts]

        client = cls.get_client()

        ###########################################
        # OFFLINE MODE
        ###########################################

        if client is None:
            try:
                from sentence_transformers import SentenceTransformer
                if not hasattr(cls, "_local_model") or cls._local_model is None:
                    logger.info("Loading SentenceTransformer local model...")
                    cls._local_model = SentenceTransformer("all-MiniLM-L6-v2")
                
                logger.info("Generating local embeddings using SentenceTransformer...")
                embeddings = cls._local_model.encode(texts).tolist()
                return embeddings
            except ImportError:
                logger.info("SentenceTransformer not installed. Generating mock embeddings...")

                dimension = cls.DEFAULT_DIMENSION

                if "large" in model_name.lower():
                    dimension = 3072

                embeddings = []

                random.seed(42)

                for _ in texts:

                    embeddings.append(
                        [
                            random.uniform(-0.1, 0.1)
                            for _ in range(dimension)
                        ]
                    )

                return embeddings

        ###########################################
        # OPENAI MODE
        ###########################################

        embeddings = []

        for start in range(
            0,
            len(texts),
            cls.BATCH_SIZE,
        ):

            batch = texts[
                start : start + cls.BATCH_SIZE
            ]

            result = await cls._generate_batch(
                client=client,
                batch=batch,
                model=model_name,
            )

            embeddings.extend(result)

        return embeddings

    @classmethod
    async def _generate_batch(
        cls,
        client: OpenAI,
        batch: List[str],
        model: str,
    ) -> List[List[float]]:

        delay = 1

        for attempt in range(
            1,
            cls.MAX_RETRIES + 1,
        ):

            try:

                response = await asyncio.to_thread(

                    client.embeddings.create,

                    input=batch,

                    model=model,

                )

                return [

                    item.embedding

                    for item in response.data

                ]

            except Exception as e:

                logger.warning(

                    f"Embedding attempt {attempt} failed: {e}"

                )

                if attempt == cls.MAX_RETRIES:

                    raise

                await asyncio.sleep(delay)

                delay *= 2

        return []

    @classmethod
    async def get_query_embedding(
        cls,
        query: str,
    ) -> List[float]:
        """
        Generates a single embedding for semantic search.
        """

        embeddings = await cls.get_embeddings([query])

        if embeddings:
            return embeddings[0]

        return []

    @classmethod
    def embedding_dimension(
        cls,
        model: str | None = None,
    ) -> int:

        model_name = model or settings.EMBEDDING_MODEL

        if model_name and "large" in model_name.lower():
            return 3072

        return cls.DEFAULT_DIMENSION