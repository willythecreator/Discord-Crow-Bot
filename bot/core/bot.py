import logging

import discord
from discord.ext import commands

from bot import config
from bot.db.database import Database

log = logging.getLogger(__name__)

EXTENSIONS = [
    "bot.cogs.general",
    "bot.cogs.tracker",
    "bot.cogs.game_alerts",
]

class CrowBot(commands.Bot):
    def __init__(self):
        intents = discord.Intents.default()
        intents.members = True
        intents.presences = True
        intents.message_content = True
        super().__init__(command_prefix="!", intents=intents)
        self.db = Database()

    async def setup_hook(self):
        await self.db.connect()

        for ext in EXTENSIONS:
            await self.load_extension(ext)
            log.info("Loaded %s", ext)

        self.tree.on_error = self.on_app_command_error

        if config.DEV_GUILD_ID:
            guild = discord.Object(id=config.DEV_GUILD_ID)
            self.tree.copy_global_to(guild=guild)
            await self.tree.sync(guild=guild)
        else:
            await self.tree.sync()

    async def on_app_command_error(self, interaction, error):
        if isinstance(error, discord.app_commands.MissingPermissions):
            msg = "You need the Manage Server permission for that."
        else:
            log.exception("Command error", exc_info=error)
            msg = "Something went wrong. Check the bot console."
        if interaction.response.is_done():
            await interaction.folloup.send(msg, ephemeral=True)
        else:
            await interaction.response.send_message(msg, ephemeral=True)

    async def on_ready(self):
        log.info("Logged in as %s (%s)", self.user, self.user.id)

    async def close(self):
        await self.db.close()
        await super().close()