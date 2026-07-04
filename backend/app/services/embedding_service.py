import time
import logging
import random
from typing import List
from openai import OpenAI
from app.core.config import settings

logger = logging.getLogger(__name__)

class EmbeddingService:
    _client = None

    @classmethod
    def get_client(cls):
        if cls._client is None:
            api_key = settings.OPENAI_API_KEY or os.getenv("OPENAI_API_KEY")
            if api_key:
                cls._client = OpenAI(api_key=api_key)
            else:
                logger.warning("OPENAI_API_KEY is not configured. Embedding service will run in mock/offline mode.")
        return cls._client

    @classmethod
    async def get_embeddings(cls, texts: List[str], model: str | None = None) -> List[List[float]]:
        """
        Generates embeddings for a list of texts using the OpenAI API.
        Implements batching and exponential backoff retry mechanism.
        """
        if not texts:
            return []

        model_name = model or settings.EMBEDDING_MODEL or "text-embedding-3-small"
        client = cls.get_client()

        # Offline/Mock Fallback Mode if no API Key is provided
        if client is None:
            logger.info("Generating mock embeddings for offline testing.")
            # 1536 is standard dimension for text-embedding-3-small/ada-002
            dimension = 1536
            if "large" in model_name:
                dimension = 3072
            return [[random.uniform(-0.1, 0.1) for _ in range(dimension)] for _ in texts]

        # In case we need to batch: OpenAI allows up to 2048 inputs per batch, but let's batch by 100 for safety
        batch_size = 100
        all_embeddings = []

        for i in range(0, len(texts), batch_size):
            batch = texts[i:i + batch_size]
            embeddings = await cls._get_embeddings_batch_with_retry(client, batch, model_name)
            all_embeddings.extend(embeddings)

        return all_embeddings

    @classmethod
    async def _get_embeddings_batch_with_retry(cls, client: OpenAI, batch: List[str], model_name: str, max_retries: int = 3) -> List[List[float]]:
        delay = 1.0
        for attempt in range(1, max_retries + 1):
            try:
                # Sync client execution under threadpool for async compatibility or run directly
                # To prevent blocking, we can execute the sync call using a standard retry loop
                response = client.embeddings.create(
                    input=batch,
                    model=model_name
                )
                return [data.embedding for data in response.data]
            except Exception as e:
                logger.error(f"Error generating embeddings (attempt {attempt}/{max_retries}): {e}")
                if attempt == max_retries:
                    raise e
                time.sleep(delay)
                delay *= 2.0
        return []
import os
