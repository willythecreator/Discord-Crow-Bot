CREATE TABLE IF NOT EXISTS events (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    guild_id INTEGER NOT NULL,
    user_id INTEGER NOT NULL,
    type TEXT NOT NULL,
    channel_id INTEGER,
    data TEXT,
    created_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:fZ', 'now'))
);

CREATE INDEX IF NOT EXISTS idx_event_guild_type_time
    ON events (guild_id, type, created_at);

CREATE INDEX IF NOT EXISTS idx_event_guild_user_time
    ON events (guild_id, user_id, created_at);

CREATE TABLE IF NOT EXISTS guild_settings (
    guild_id INTEGER NOT NULL,
    key TEXT NOT NULL,
    value TEXT NOT NULL,
    PRIMARY KEY (guild_id, key)
);