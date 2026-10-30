import asyncio

import aiohttp

URL = "https://www.cheapshark.com/api/1.0/deals"
BASE = {"storeID": 1, "pageSize": 5}
EXTRA = [
    {},
    {"onSale": 1},
    {"steamRating": 70},
    {"upperPrice": 50},
    {"pageSize": 60},
]


async def main():
    async with aiohttp.ClientSession() as session:
        for extra in EXTRA:
            params = {**BASE, **extra}
            async with session.get(URL, params=params) as resp:
                body = (await resp.text())[:150]
                print(resp.status, params, body)


asyncio.run(main())