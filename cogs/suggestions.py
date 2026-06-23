import discord
from discord.ext import commands
from discord import app_commands

from utils import storage
from utils.checks import is_staff


class Suggestions(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.hybrid_command(name="suggest", description="Submit a suggestion for the server.")
    @app_commands.describe(suggestion="What's your idea?")
    @commands.bot_has_permissions(send_messages=True, add_reactions=True, embed_links=True)
    async def suggest(self, ctx: commands.Context, *, suggestion: str):
        channel_id = storage.get_config("suggestion_channel_id")
        channel = self.bot.get_channel(channel_id) if channel_id else ctx.channel
        if channel is None:
            channel = ctx.channel

        embed = discord.Embed(title="💡 New Suggestion", description=suggestion, color=discord.Color.teal())
        embed.set_footer(text=f"Suggested by {ctx.author.display_name}")
        if ctx.author.display_avatar:
            embed.set_thumbnail(url=ctx.author.display_avatar.url)

        msg = await channel.send(embed=embed)
        await msg.add_reaction("👍")
        await msg.add_reaction("👎")

        await ctx.send(f"✅ Suggestion submitted in {channel.mention}!")

    @commands.hybrid_command(name="setsuggestionchannel", description="[Staff] Set the channel where suggestions are posted.")
    @app_commands.describe(channel="Channel for suggestions (defaults to here)")
    @is_staff()
    async def setsuggestionchannel(self, ctx: commands.Context, channel: discord.TextChannel = None):
        channel = channel or ctx.channel
        storage.set_config("suggestion_channel_id", channel.id)
        await ctx.send(f"💡 Suggestions will now be posted in {channel.mention}.")


async def setup(bot: commands.Bot):
    await bot.add_cog(Suggestions(bot))
