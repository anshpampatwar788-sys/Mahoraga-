import asyncio
import discord
from discord.ext import commands
from discord import app_commands

from utils import storage

MAX_REMINDER_MINUTES = 1440  # 24 hours


class Utility(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.hybrid_command(name="serverinfo", description="Show information about this server.")
    async def serverinfo(self, ctx: commands.Context):
        guild = ctx.guild
        embed = discord.Embed(title=f"📊 {guild.name}", color=discord.Color.blurple())
        if guild.icon:
            embed.set_thumbnail(url=guild.icon.url)
        embed.add_field(name="Owner", value=str(guild.owner) if guild.owner else "Unknown", inline=True)
        embed.add_field(name="Members", value=str(guild.member_count), inline=True)
        embed.add_field(name="Roles", value=str(len(guild.roles)), inline=True)
        embed.add_field(name="Text Channels", value=str(len(guild.text_channels)), inline=True)
        embed.add_field(name="Voice Channels", value=str(len(guild.voice_channels)), inline=True)
        embed.add_field(name="Boosts", value=str(guild.premium_subscription_count or 0), inline=True)
        embed.set_footer(text=f"Created on {guild.created_at.strftime('%B %d, %Y')}")
        await ctx.send(embed=embed)

    @commands.hybrid_command(name="userinfo", description="Show information about a member.")
    @app_commands.describe(member="Whose info to show (defaults to you)")
    async def userinfo(self, ctx: commands.Context, member: discord.Member = None):
        member = member or ctx.author
        embed = discord.Embed(title=f"👤 {member.display_name}", color=member.color or discord.Color.blurple())
        embed.set_thumbnail(url=member.display_avatar.url)
        embed.add_field(name="Username", value=str(member), inline=True)
        embed.add_field(name="ID", value=str(member.id), inline=True)
        embed.add_field(name="Bot?", value="Yes" if member.bot else "No", inline=True)
        embed.add_field(name="Account created", value=member.created_at.strftime("%B %d, %Y"), inline=True)
        if member.joined_at:
            embed.add_field(name="Joined server", value=member.joined_at.strftime("%B %d, %Y"), inline=True)
        top_roles = [r.mention for r in reversed(member.roles) if r.name != "@everyone"][:5]
        embed.add_field(name="Top roles", value=", ".join(top_roles) if top_roles else "None", inline=False)
        await ctx.send(embed=embed)

    @commands.hybrid_command(name="rank", description="Show your (or someone's) position on the points leaderboard.")
    @app_commands.describe(member="Whose rank to check (defaults to you)")
    async def rank(self, ctx: commands.Context, member: discord.Member = None):
        member = member or ctx.author
        full_board = storage.get_leaderboard(limit=10_000)
        position = next((i + 1 for i, (uid, _) in enumerate(full_board) if uid == member.id), None)
        if position is None:
            await ctx.send(f"{member.display_name} doesn't have any points yet.")
            return
        balance = storage.get_balance(member.id)
        await ctx.send(f"📈 **{member.display_name}** is rank **#{position}** with **{balance}** points.")

    @commands.hybrid_command(name="remindme", description="Get a DM reminder after a set number of minutes.")
    @app_commands.describe(minutes="How many minutes from now", message="What to remind you about")
    async def remindme(self, ctx: commands.Context, minutes: int, *, message: str):
        if not (1 <= minutes <= MAX_REMINDER_MINUTES):
            await ctx.send(f"Minutes must be between 1 and {MAX_REMINDER_MINUTES} (24 hours).")
            return
        await ctx.send(f"⏰ Got it — I'll remind you in {minutes} minute(s).")
        asyncio.create_task(self._send_reminder(ctx.author, minutes, message))

    async def _send_reminder(self, user: discord.User, minutes: int, message: str):
        await asyncio.sleep(minutes * 60)
        try:
            await user.send(f"⏰ Reminder: {message}")
        except discord.Forbidden:
            pass


async def setup(bot: commands.Bot):
    await bot.add_cog(Utility(bot))
