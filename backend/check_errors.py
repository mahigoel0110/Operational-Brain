import asyncio
from motor.motor_asyncio import AsyncIOMotorClient

async def run():
    client = AsyncIOMotorClient("mongodb://127.0.0.1:27017")
    db = client["operational_brain"]
    collection = db["documents"]
    
    docs = await collection.find({"status": "FAILED"}).to_list(None)
    for doc in docs:
        print(f"Doc {doc.get('name')} failed with error: {doc.get('error_message')}")

if __name__ == "__main__":
    asyncio.run(run())
