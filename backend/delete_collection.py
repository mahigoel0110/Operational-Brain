import asyncio
from app.services.vector_store import VectorStoreService
from app.core.config import settings

async def run():
    client = VectorStoreService.get_client()
    collection_name = settings.QDRANT_COLLECTION_NAME or "documents_general"
    try:
        client.delete_collection(collection_name=collection_name)
        print(f"Collection {collection_name} deleted successfully.")
    except Exception as e:
        print(f"Failed to delete collection: {e}")

if __name__ == "__main__":
    asyncio.run(run())
