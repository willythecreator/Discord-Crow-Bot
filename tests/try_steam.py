import asyncio

import aiohttp

from bot.services import steam


async def main():
    async with aiohttp.ClientSession() as session:
        for deal in (await steam.fetch_deals(session))[:10]:
            print(f"-{deal['savings']}%", deal["title"], f"${deal['sale']:.2f}", deal["url"])


asyncio.run(main())