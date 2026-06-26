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
    async def suggest(self, ctx: commands.Context, *, suggestion: str):
        # Respond to the interaction immediately so it never times out while we
        # do the actual posting/reacting work below.
        if ctx.interaction:
            await ctx.defer(ephemeral=True)

        channel_id = storage.get_config("suggestion_channel_id")
        channel = self.bot.get_channel(channel_id) if channel_id else None
        if channel is None:
            channel = ctx.channel

        embed = discord.Embed(title="💡 New Suggestion", description=suggestion, color=discord.Color.teal())
        embed.set_footer(text=f"Suggested by {ctx.author.display_name}")
        if ctx.author.display_avatar:
            embed.set_thumbnail(url=ctx.author.display_avatar.url)

        try:
            msg = await channel.send(embed=embed)
            await msg.add_reaction("👍")
            await msg.add_reaction("👎")
        except discord.Forbidden:
            await ctx.send(
                f"I don't have permission to post or react in {channel.mention}. "
                "Ask an admin to check my permissions there (Send Messages, Embed Links, Add Reactions)."
            )
            return
        except discord.HTTPException:
            await ctx.send("Something went wrong posting that suggestion — try again in a moment.")
            return

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
