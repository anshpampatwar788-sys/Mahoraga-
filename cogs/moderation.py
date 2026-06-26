import discord
from discord.ext import commands
from discord import app_commands
from datetime import timedelta

from utils.checks import is_staff, check_hierarchy

MAX_TIMEOUT_MINUTES = 40320  # Discord's hard cap: 28 days
MAX_SLOWMODE_SECONDS = 21600  # Discord's hard cap: 6 hours


class Moderation(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.hybrid_command(name="kick", description="Kick a member from the server.")
    @app_commands.describe(member="Who to kick", reason="Why they're being kicked")
    @is_staff()
    @commands.bot_has_permissions(kick_members=True)
    async def kick(self, ctx: commands.Context, member: discord.Member, reason: str = "No reason provided."):
        error = check_hierarchy(ctx.author, member)
        if error:
            await ctx.send(f"🚫 {error}")
            return
        await member.kick(reason=reason)
        await ctx.send(f"👋 Kicked **{member.display_name}**. Reason: {reason}")

    @commands.hybrid_command(name="ban", description="Ban a member from the server.")
    @app_commands.describe(member="Who to ban", reason="Why they're being banned")
    @is_staff()
    @commands.bot_has_permissions(ban_members=True)
    async def ban(self, ctx: commands.Context, member: discord.Member, reason: str = "No reason provided."):
        error = check_hierarchy(ctx.author, member)
        if error:
            await ctx.send(f"🚫 {error}")
            return
        await member.ban(reason=reason)
        await ctx.send(f"🔨 Banned **{member.display_name}**. Reason: {reason}")

    @commands.hybrid_command(name="timeout", description="Temporarily mute a member.")
    @app_commands.describe(member="Who to time out", minutes="How many minutes (max 40320 / 28 days)", reason="Why")
    @is_staff()
    @commands.bot_has_permissions(moderate_members=True)
    async def timeout(self, ctx: commands.Context, member: discord.Member, minutes: int, reason: str = "No reason provided."):
        error = check_hierarchy(ctx.author, member)
        if error:
            await ctx.send(f"🚫 {error}")
            return
        if not (1 <= minutes <= MAX_TIMEOUT_MINUTES):
            await ctx.send(f"Minutes must be between 1 and {MAX_TIMEOUT_MINUTES} (28 days).")
            return
        await member.timeout(timedelta(minutes=minutes), reason=reason)
        await ctx.send(f"🔇 Timed out **{member.display_name}** for {minutes} minute(s). Reason: {reason}")

    @commands.hybrid_command(name="untimeout", description="Remove a member's timeout.")
    @app_commands.describe(member="Who to remove timeout from")
    @is_staff()
    @commands.bot_has_permissions(moderate_members=True)
    async def untimeout(self, ctx: commands.Context, member: discord.Member):
        error = check_hierarchy(ctx.author, member)
        if error:
            await ctx.send(f"🚫 {error}")
            return
        await member.timeout(None)
        await ctx.send(f"🔊 Removed timeout for **{member.display_name}**.")

    @commands.hybrid_command(name="clear", description="Delete a number of recent messages in this channel.")
    @app_commands.describe(amount="How many messages to delete (1-100)")
    @is_staff()
    @commands.bot_has_permissions(manage_messages=True)
    async def clear(self, ctx: commands.Context, amount: int):
        if not (1 <= amount <= 100):
            await ctx.send("Amount must be between 1 and 100.")
            return
        deleted = await ctx.channel.purge(limit=amount + 1)
        await ctx.send(f"🧹 Deleted {len(deleted) - 1} message(s).", delete_after=5)

    @commands.hybrid_command(name="slowmode", description="Set slowmode delay for this channel.")
    @app_commands.describe(seconds="Delay in seconds, 0 to disable (max 21600 / 6 hours)")
    @is_staff()
    @commands.bot_has_permissions(manage_channels=True)
    async def slowmode(self, ctx: commands.Context, seconds: int):
        if not (0 <= seconds <= MAX_SLOWMODE_SECONDS):
            await ctx.send(f"Seconds must be between 0 and {MAX_SLOWMODE_SECONDS} (6 hours).")
            return
        await ctx.channel.edit(slowmode_delay=seconds)
        if seconds == 0:
            await ctx.send("Slowmode disabled.")
        else:
            await ctx.send(f"🐌 Slowmode set to {seconds} second(s).")

    @commands.hybrid_command(name="warn", description="Warn a member (posted in-channel, not stored).")
    @app_commands.describe(member="Who to warn", reason="Why")
    @is_staff()
    async def warn(self, ctx: commands.Context, member: discord.Member, reason: str = "No reason provided."):
        error = check_hierarchy(ctx.author, member)
        if error:
            await ctx.send(f"🚫 {error}")
            return
        await ctx.send(f"⚠️ **{member.display_name}** has been warned. Reason: {reason}")
        try:
            await member.send(f"You were warned in **{ctx.guild.name}**. Reason: {reason}")
        except discord.Forbidden:
            pass

    @commands.hybrid_command(name="unban", description="Unban a user by their ID.")
    @app_commands.describe(user_id="The numeric Discord ID of the user to unban", reason="Why")
    @is_staff()
    @commands.bot_has_permissions(ban_members=True)
    async def unban(self, ctx: commands.Context, user_id: str, reason: str = "No reason provided."):
        try:
            uid = int(user_id)
        except ValueError:
            await ctx.send("That doesn't look like a valid user ID.")
            return
        try:
            user = await self.bot.fetch_user(uid)
            await ctx.guild.unban(user, reason=reason)
        except discord.NotFound:
            await ctx.send("That user isn't banned, or the ID is wrong.")
            return
        await ctx.send(f"✅ Unbanned **{user}**.")

    @commands.hybrid_command(name="nickname", description="Change a member's nickname.")
    @app_commands.describe(member="Who to rename", new_nick="New nickname (leave blank to reset)")
    @is_staff()
    @commands.bot_has_permissions(manage_nicknames=True)
    async def nickname(self, ctx: commands.Context, member: discord.Member, new_nick: str = None):
        error = check_hierarchy(ctx.author, member)
        if error:
            await ctx.send(f"🚫 {error}")
            return
        old_nick = member.display_name
        await member.edit(nick=new_nick)
        if new_nick:
            await ctx.send(f"✏️ Renamed **{old_nick}** to **{new_nick}**.")
        else:
            await ctx.send(f"✏️ Reset **{old_nick}**'s nickname.")

    @commands.hybrid_command(name="lock", description="Stop @everyone from sending messages in this channel.")
    @is_staff()
    @commands.bot_has_permissions(manage_channels=True)
    async def lock(self, ctx: commands.Context):
        overwrite = ctx.channel.overwrites_for(ctx.guild.default_role)
        overwrite.send_messages = False
        await ctx.channel.set_permissions(ctx.guild.default_role, overwrite=overwrite)
        await ctx.send("🔒 Channel locked.")

    @commands.hybrid_command(name="unlock", description="Allow @everyone to send messages in this channel again.")
    @is_staff()
    @commands.bot_has_permissions(manage_channels=True)
    async def unlock(self, ctx: commands.Context):
        overwrite = ctx.channel.overwrites_for(ctx.guild.default_role)
        overwrite.send_messages = None
        await ctx.channel.set_permissions(ctx.guild.default_role, overwrite=overwrite)
        await ctx.send("🔓 Channel unlocked.")

    @commands.hybrid_command(name="purgeuser", description="Delete a member's recent messages in this channel.")
    @app_commands.describe(member="Whose messages to delete", amount="How many recent channel messages to scan (1-200)")
    @is_staff()
    @commands.bot_has_permissions(manage_messages=True)
    async def purgeuser(self, ctx: commands.Context, member: discord.Member, amount: int = 50):
        if not (1 <= amount <= 200):
            await ctx.send("Amount must be between 1 and 200.")
            return
        deleted = await ctx.channel.purge(limit=amount, check=lambda m: m.author.id == member.id)
        await ctx.send(f"🧹 Deleted {len(deleted)} message(s) from **{member.display_name}**.", delete_after=5)

    @commands.hybrid_command(name="announce", description="Post an announcement embed to a channel.")
    @app_commands.describe(channel="Where to post it", message="The announcement text")
    @is_staff()
    @commands.bot_has_permissions(embed_links=True)
    async def announce(self, ctx: commands.Context, channel: discord.TextChannel, *, message: str):
        embed = discord.Embed(title="📢 Announcement", description=message, color=discord.Color.gold())
        embed.set_footer(text=f"Posted by {ctx.author.display_name}")
        try:
            await channel.send(embed=embed)
        except discord.Forbidden:
            await ctx.send(f"I don't have permission to post in {channel.mention}.")
            return
        await ctx.send(f"✅ Announcement posted in {channel.mention}.")


async def setup(bot: commands.Bot):
    await bot.add_cog(Moderation(bot))
