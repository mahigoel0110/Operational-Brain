import asyncio

from app.db.database import database


async def test():
    print(await database.list_collection_names())


asyncio.run(test())