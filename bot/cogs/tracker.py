import discord
from discord import app_commands
from discord.ext import commands

from bot.core import events

class Tracker(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_voice_state_update(self, member, before, after):
        if member.bot or before.channel == after.channel:
            return 

        guild_id = member.guild.id
        if before.channel is None:
            await self.bot.db.record_event(
                guild_id, member.id, events.VOICE_JOIN, after.channel.id
            )
        elif after.channel is None:
            await self.bot.db.record_event(
                guild_id, member.id, events.VOICE_LEAVE, before.channel.id
            )
        else:
            await self.bot.db.record_event(
                guild_id, member.id, events.VOICE_MOVE, after.channel.id,
                {"from": before.channel.id},
            )

    @app_commands.command(name="recent", description="Show the latest recorded events")
    @app_commands.guild_only()
    async def recent(self, interaction: discord.Interaction):
        rows = await self.bot.db.recent_events(interaction.guild.id, 10)
        if not rows:
            await interaction.response.send_message("No events recorded yet")
            return

        lines = []
        for row in rows:
            member = interaction.guild.get_member(row["user_id"])
            name = member.display_name if member else str(row["user_id"])
            lines.append(f"`{row['created_at'][11:19]}` {name}: {row['type']}")
        await interaction.response.send_message("\n".join(lines))

async def setup(bot):
    await bot.add_cog(Tracker(bot))