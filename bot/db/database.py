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

    async def set_setting(self, guild_id, key, value):
        await self.conn.execute(
            "INSERT INTO guild_settings (guild_id, key, value) VALUES (?, ?, ?) "
            "ON CONFLICT(guild_id, key) DO UPDATE SET value = excluded.value",
            (guild_id, key, str(value)),
        )
        await self.conn.commit()

    async def get_setting(self, guild_id, key, default=None):
        cursor = await self.conn.execute(
            "SELECT value FROM guild_settings WHERE guild_id = ? AND key = ?",
            (guild_id, key),
        )
        row = await cursor.fetchone()
        return row["value"] if row else default

    async def guilds_with_setting(self, key):
        cursor = await self.conn.execute(
            "SELECT guild_id, value FROM guild_settings WHERE key = ?", (key,)
        )
        return await cursor.fetchall()

    async def mark_posted(self, guild_id, deal_id):
        cursor = await self.conn.execute(
            "INSERT OR IGNORE INTO posted_deals (guild_id, deal_id) VALUES (?, ?)",
            (guild_id, deal_id),
        )
        await self.conn.commit()
        return cursor.rowcount == 1