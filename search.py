import discord
from discord.ext import commands
from discord import app_commands

try:
    from duckduckgo_search import DDGS
except ImportError:
    DDGS = None


class Search(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.hybrid_command(name="question", description="Ask Mahoraga to search the web for an answer.")
    @app_commands.describe(query="What do you want to search for?")
    async def question(self, ctx: commands.Context, *, query: str):
        if DDGS is None:
            await ctx.send(
                "Search isn't set up yet. Run `pip install duckduckgo-search` and restart the bot."
            )
            return

        async with ctx.typing():
            try:
                results = await self.bot.loop.run_in_executor(
                    None, lambda: list(DDGS().text(query, max_results=5))
                )
            except Exception:
                await ctx.send("Search failed — try again in a moment.")
                return

        if not results:
            await ctx.send(f"No results found for **{query}**.")
            return

        embed = discord.Embed(title=f"🔎 Results for: {query}", color=discord.Color.blue())
        for r in results:
            title = (r.get("title") or "Untitled")[:256]
            snippet = (r.get("body") or "")[:200]
            link = r.get("href") or ""
            embed.add_field(name=title, value=f"{snippet}\n{link}", inline=False)
        embed.set_footer(text="Results via DuckDuckGo")
        await ctx.send(embed=embed)


async def setup(bot: commands.Bot):
    await bot.add_cog(Search(bot))
