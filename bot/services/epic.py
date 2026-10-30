import aiohttp

URL = "https://store-site-backend-static-ipv4.ak.epicgames.com/freeGamesPromotions"

def _slug(element):
    for mapping in element.get("offerMappings") or []:
        if mapping.get("pageSlug"):
            return mapping["pageSlug"]
    for mapping in (element.get("catalogNs") or {}).get("mappings") or []:
        if mapping.get("pageSlug"):
            return mapping["pageSlug"]
    return element.get("productSlug") or element.get("urSlug")

def _image(element):
    images = {i.get("type"): i.get("url") for i in element.get("keyImages") or []}
    return images.get("OfferImageWide") or images.get("Thumbnail") or next(iter(images.values()), None)

async def fetch_free_games(session, country="ES", locale="en-US"):
    params = {"locale": locale, "country": country, "allowCountries": country}
    timeout = aiohttp.ClientTimeout(total=15)
    async with session.get(URL, params=params, timeout=timeout) as resp:
        resp.raise_for_status()
        data = await resp.json()

    elements = data["data"]["Catalog"]["searchStore"]["elements"]
    games = []
    for el in elements:
        price = (el.get("price") or {}).get("totalPrice") or {}

        # Only games that normally cost money and are free right now
        if price.get("originalPrice", 0) <= 0 or price.get("discountPrice") != 0:
            continue

        blocks = (el.get("promotions") or {}).get("promotionalOffers") or []
        offers = [o for block in blocks for o in block.get("promotionalOffers", [])]
        slug = _slug(el)
        if not offers or not slug:
            continue

        games.append({
            "id": el["id"],
            "title": el["title"],
            "description": el.get("description") or "",
            "image": _image(el),
            "url": f"https://store.epicgames.com/en-US/p/{slug}",
            "normal_price": (price.get("fmtPrice") or {}).get("originalPrice", ""),
            "ends": offers[0]["endDate"],
        })
    return games