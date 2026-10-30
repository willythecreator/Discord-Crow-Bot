import logging
from datetime import datetime

import aiohttp
import discord 
from discord import app_commands
from discord.ext import commands, tasks

from bot.services import epic

log = logging.getLogger(__name__)

SETTING = "alert_channel"

class GameAlerts(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.session = None

    async def cog_load(self):
        self.session = aiohttp.ClientSession()
        self.check_epic.start()

    async def cog_unload(self):
        self.check_epic.cancel()
        await self.session.close()

    def make_embed(self, game):
        embed = discord.Embed(
            title=game["title"],
            url=game["url"],
            description=game["description"][:300],
            color=0x7289DA,
        )
        ends = datetime.fromisoformat(game["ends"].replace("Z", "+00:00"))
        embed.add_field(name="Normally", value=game["normal_price"] or "Paid", inline=True)
        embed.add_field(name="Free until", value=f"<t:{int(ends.timestamp())}:R>", inline=True)
        if game["image"]:
            embed.set_image(url=game["image"])
        embed.set_footer(text="Epic Games Store")
        return embed

    @tasks.loop(hours=3)
    async def check_epic(self):
        try:
            games = await epic.fetch_free_games(self.session)
        except Exception:
            log.exception("Could not fetch Epic free games")
            return

        for row in await self.bot.db.guilds_with_setting(SETTING):
            channel = self.bot.get_channel(int(row["value"]))
            if channel is None:
                continue
            for game in games:
                deal_id = f"epic:{game['id']}:{game['ends']}"
                if not await self.bot.db.mark_posted(row["guild_id"], deal_id):
                    continue
                try:
                    await channel.send(embed=self.make_embed(game))
                except discord.HTTPException:
                    log.exception("Could not post in channel %s", channel.id)

    @check_epic.before_loop
    async def before_check_epic(self):
        await self.bot.wait_until_ready()

    @app_commands.command(name="alerts-channel", description="Choose where free game alerts are posted")
    @app_commands.guild_only()
    @app_commands.checks.has_permissions(manage_guild=True)
    async def alerts_channel(self, interaction: discord.Interaction, channel: discord.TextChannel):
        await self.bot.db.set_setting(interaction.guild.id, SETTING, channel.id)
        await interaction.response.send_message(f"free game alerts will go to {channel.mention}.")

    @app_commands.command(name="freegames", description="Show the games that are free on Epic right now")
    async def freegames(self, interaction: discord.Interaction):
        await interaction.response.defer()
        try:
            games = await epic.fetch_free_games(self.session)
        except Exception:
            log.exception("Could not fetch Epic free games")
            await interaction.followup.send("Couldn't reach Epic right now. Try again in a bit.")
            return
        if not games:
            await interaction.followup.send("No free games on Epic right now.")
            return
        await interaction.followup.send(embeds=[self.make_embed(g) for g in games[:10]])

async def setup(bot):
    await bot.add_cog(GameAlerts(bot))