import asyncio
from motor.motor_asyncio import AsyncIOMotorClient

async def run():
    client = AsyncIOMotorClient("mongodb://127.0.0.1:27017")
    db = client["operational_brain"]
    collection = db["documents"]
    
    docs = await collection.find({}).to_list(None)
    for doc in docs:
        updates = {}
        if "status" in doc:
            if isinstance(doc["status"], str) and doc["status"].islower():
                new_status = doc["status"].upper()
                if new_status == "PROCESSING":
                    new_status = "EXTRACTING"
                updates["status"] = new_status
        if "extracted_metadata" in doc and "metadata" not in doc:
            updates["metadata"] = doc["extracted_metadata"]
        
        if updates:
            await collection.update_one({"_id": doc["_id"]}, {"$set": updates})
            print(f"Updated doc {doc['_id']} with {updates}")
        else:
            print(f"Doc {doc['_id']} requires no update")

if __name__ == "__main__":
    asyncio.run(run())
