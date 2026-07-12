import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
from beanie import init_beanie
from app.models.document import DocumentModel

async def main():
    import os
    from dotenv import load_dotenv
    load_dotenv()
    db_uri = os.environ.get("MONGODB_URI", "mongodb://localhost:27017")
    client = AsyncIOMotorClient(db_uri)
    await init_beanie(database=client['operational_brain'], document_models=[DocumentModel])
    doc = await DocumentModel.find_one(sort=[('_id', -1)])
    if doc:
        print("LAST DOC ERROR:", doc.error_message)
        print("LAST DOC STATUS:", doc.status)
        print("LAST DOC STEP:", doc.current_step)
    else:
        print("No doc")

if __name__ == "__main__":
    asyncio.run(main())
