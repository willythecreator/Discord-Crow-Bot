import json
import os
from pathlib import Path

import aiosqlite

from bot import config

class Database:
    def __init__(self, path=config.DB_PATH):
        self.path = path
        self.conn = None

    async def connect(self):
        folder = os.path.dirname(self.path)
        if folder:
            os.makedirs(folder, exist_ok=True)
        self.conn = await aiosqlite.connect(self.path)
        self.conn.row_factory = aiosqlite.Row
        await self.conn.execute("PRAGMA journal_mode=WAL")
        schema = Path(__file__).with_name("schema.sql").read_text(encoding="utf-8")
        await self.conn.executescript(schema)
        await self.conn.commit()

    async def close(self):
        if self.conn:
            await self.conn.close()

    async def record_event(self, guild_id, user_id, type, channel_id=None, data=None):
        await self.conn.execute(
            "INSERT INTO events (guild_id, user_id, type, channel_id, data) "
            "VALUES (?, ?, ?, ?, ?)",
            (guild_id, user_id, type, channel_id, json.dumps(data) if data else None),
        )
        await self.conn.commit()

    async def recent_events(self, guild_id, limit=10):
        cursor = await self.conn.execute(
            "SELECT * FROM events WHERE guild_id = ? ORDER BY id DESC LIMIT ?",
            (guild_id, limit),
        )
        return await cursor.fetchall()