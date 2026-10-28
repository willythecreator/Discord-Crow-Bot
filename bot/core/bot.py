import logging

import discord
from discord.ext import commands

from bot import config

log = logging.getLogger(__name__)

EXTENSIONS = [
    "bot.cogs.general",
]

class CrowBot(commands.Bot):
    def __init__(self):
        intents = discord.Intents.default()
        intents.members = True
        intents.presences = True
        intents.message_content = True
        super().__init__(command_prefix="!", intents=intents)

    async def setup_hook(self):
        for ext in EXTENSIONS:
            await self.load_extension(ext)
            log.info("Loaded %s", ext)

        if config.DEV_GUILD_ID:
            guild = discord.Object(id=config.DEV_GUILD_ID)
            self.tree.copy_global_to(guild=guild)
            await self.tree.sync(guild=guild)
        else:
            await self.tree.sync()

    async def on_ready(self):
        log.info("Logged in as %s (%s)", self.user, self.user.id)