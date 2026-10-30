import logging
from datetime import datetime

import aiohttp
import discord
from discord import app_commands
from discord.ext import commands, tasks

from bot.services import epic, steam

log = logging.getLogger(__name__)

SETTING = "alert_channel"
DEALS_CHANNEL = "deals_channel"
MIN_DISCOUNT = "deals_min_discount"
DEFAULT_MIN_DISCOUNT = 75
MAX_PER_RUN = 5


class GameAlerts(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.session = None

    async def cog_load(self):
        self.session = aiohttp.ClientSession()
        self.check_epic.start()
        self.check_steam.start()

    async def cog_unload(self):
        self.check_epic.cancel()
        self.check_steam.cancel()
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

    def make_deal_embed(self, deal):
        embed = discord.Embed(title=deal["title"], url=deal["url"], color=0x1B2838)
        embed.add_field(
            name="Price",
            value=f"~~${deal['normal']:.2f}~~ **${deal['sale']:.2f}**",
            inline=True,
        )
        embed.add_field(name="Discount", value=f"-{deal['savings']}%", inline=True)
        if deal["rating"]:
            embed.add_field(name="Reviews", value=f"{deal['rating']}% positive", inline=True)
        embed.set_image(url=deal["image"])
        embed.set_footer(text="Steam via CheapShark (prices in USD)")
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

    @tasks.loop(hours=6)
    async def check_steam(self):
        try:
            deals = await steam.fetch_deals(self.session)
        except Exception:
            log.exception("Could not fetch Steam deals")
            return

        for row in await self.bot.db.guilds_with_setting(DEALS_CHANNEL):
            guild_id = row["guild_id"]
            channel = self.bot.get_channel(int(row["value"]))
            if channel is None:
                continue
            minimum = int(await self.bot.db.get_setting(guild_id, MIN_DISCOUNT, DEFAULT_MIN_DISCOUNT))
            picks = [d for d in deals if d["savings"] >= minimum][:MAX_PER_RUN]
            for deal in picks:
                deal_id = f"steam:{deal['app_id']}:{deal['sale']:.2f}"
                if not await self.bot.db.mark_posted(guild_id, deal_id):
                    continue
                try:
                    await channel.send(embed=self.make_deal_embed(deal))
                except discord.HTTPException:
                    log.exception("Could not post in channel %s", channel.id)

    @check_steam.before_loop
    async def before_check_steam(self):
        await self.bot.wait_until_ready()

    @app_commands.command(name="alerts-channel", description="Choose where free game alerts are posted")
    @app_commands.guild_only()
    @app_commands.checks.has_permissions(manage_guild=True)
    async def alerts_channel(self, interaction: discord.Interaction, channel: discord.TextChannel):
        await self.bot.db.set_setting(interaction.guild.id, SETTING, channel.id)
        await interaction.response.send_message(f"Free game alerts will go to {channel.mention}.")

    @app_commands.command(name="deals-channel", description="Choose where Steam deals are posted")
    @app_commands.guild_only()
    @app_commands.checks.has_permissions(manage_guild=True)
    async def deals_channel(self, interaction: discord.Interaction, channel: discord.TextChannel):
        await self.bot.db.set_setting(interaction.guild.id, DEALS_CHANNEL, channel.id)
        await interaction.response.send_message(f"Steam deals will go to {channel.mention}.")

    @app_commands.command(name="steam-deals", description="Set the minimum discount for Steam deal alerts")
    @app_commands.describe(minimum="Minimum discount in percent")
    @app_commands.guild_only()
    @app_commands.checks.has_permissions(manage_guild=True)
    async def steam_deals(self, interaction: discord.Interaction, minimum: app_commands.Range[int, 10, 95]):
        await self.bot.db.set_setting(interaction.guild.id, MIN_DISCOUNT, minimum)
        await interaction.response.send_message(f"Steam deals will only be posted at {minimum}% off or more.")

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

    @app_commands.command(name="deals", description="Show the best Steam deals right now")
    @app_commands.guild_only()
    async def deals(self, interaction: discord.Interaction):
        await interaction.response.defer()
        try:
            found = await steam.fetch_deals(self.session)
        except Exception:
            log.exception("Could not fetch Steam deals")
            await interaction.followup.send("Couldn't reach CheapShark right now. Try again in a bit.")
            return
        minimum = int(await self.bot.db.get_setting(interaction.guild.id, MIN_DISCOUNT, DEFAULT_MIN_DISCOUNT))
        picks = [d for d in found if d["savings"] >= minimum][:MAX_PER_RUN]
        if not picks:
            await interaction.followup.send(f"No Steam deals at {minimum}% off or more right now.")
            return
        await interaction.followup.send(embeds=[self.make_deal_embed(d) for d in picks])


async def setup(bot):
    await bot.add_cog(GameAlerts(bot))