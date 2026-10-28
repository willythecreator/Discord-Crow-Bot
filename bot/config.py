import os
from dotenv import load_dotenv

load_dotenv()

TOKEN = os.getenv("DISCORD_TOKEN")
DEV_GUILD_ID = int(os.getenv("DEV_GUILD_ID", "0")) or None
DB_PATH = os.getenv("DB_PATH", "data/bot.db")