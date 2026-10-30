import asyncio
import aiohttp
from bot.services import epic

async def main():
    async with aiohttp.ClientSession() as session:
        for game in await epic.fetch_free_games(session):
            print(game["title"], "->", game["url"], "until", game["ends"])

asyncio.run(main())