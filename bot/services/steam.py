import aiohttp

URL = "https://www.cheapshark.com/api/1.0/deals"
STEAM_STORE_ID = "1"
HEADERS = {"User-Agent": "CrowBot/1.0 (+https://github.com/willythecreator/Discord-Crow-Bot"}

async def fetch_deals(session, min_rating=70):
    params = {
        "storeID": STEAM_STORE_ID,
        "onSale": 1,
        "steamRating": min_rating,
        "upperPrice": 50,
        "pageSize": 60,
    }
    timeout = aiohttp.ClientTimeout(total=15)
    async with session.get(URL, params=params, headers=HEADERS, timeout=timeout) as resp:
        if resp.status != 200:
            raise RuntimeError(f"CheapShark {resp.status}: {(await resp.text())[:200]}")
        data = await resp.json()

    deals = []
    for d in data:
        app_id = d.get("steamAppID")
        if not app_id:
            continue
        deals.append({
            "id": d["dealID"],
            "app_id": app_id,
            "title": d["title"],
            "sale": float(d["salePrice"]),
            "normal": float(d["normalPrice"]),
            "savings": round(float(d["savings"])),
            "rating": d.get("steamRatingPercent"),
            "url": f"https://store.steampowered.com/app/{app_id}",
            "image": f"https://cdn.cloudflare.steamstatic.com/steam/apps/{app_id}/header.jpg",
        })
    return deals