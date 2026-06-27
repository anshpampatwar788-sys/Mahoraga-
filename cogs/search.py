import aiohttp
import discord
from discord.ext import commands
from discord import app_commands

try:
    from ddgs import DDGS
except ImportError:
    try:
        from duckduckgo_search import DDGS
    except ImportError:
        DDGS = None

SEARCH_COOLDOWN_SECONDS = 60


class Search(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    async def _try_ddgs(self, query: str):
        """Primary search via the ddgs package. Returns a list of result dicts or None on failure."""
        if DDGS is None:
            return None
        try:
            results = await self.bot.loop.run_in_executor(
                None, lambda: list(DDGS().text(query, max_results=5))
            )
            return results or None
        except Exception as e:
            print(f"[question] DDGS search failed: {e}")
            return None

    async def _try_wikipedia(self, query: str):
        """Fallback search via Wikipedia's public REST API (no key, rarely blocked)."""
        headers = {"User-Agent": "MahoragaDiscordBot/1.0 (contact: server-owner; +https://discord.com)"}
        try:
            timeout = aiohttp.ClientTimeout(total=8)
            async with aiohttp.ClientSession(timeout=timeout, headers=headers) as session:
                params = {
                    "action": "opensearch",
                    "search": query,
                    "limit": 1,
                    "namespace": 0,
                    "format": "json",
                }
                async with session.get("https://en.wikipedia.org/w/api.php", params=params) as resp:
                    # Wikipedia sometimes serves this as text/plain instead of
                    # application/json, so skip aiohttp's strict content-type check.
                    data = await resp.json(content_type=None)
                if not data or not data[1]:
                    return None
                title = data[1][0]
                async with session.get(
                    f"https://en.wikipedia.org/api/rest_v1/page/summary/{title}"
                ) as resp:
                    if resp.status != 200:
                        return None
                    return await resp.json(content_type=None)
        except Exception as e:
            print(f"[question] Wikipedia fallback failed: {e}")
            return None

    @commands.hybrid_command(name="question", description="Ask Mahoraga to search the web for an answer.")
    @app_commands.describe(query="What do you want to search for?")
    @commands.cooldown(1, SEARCH_COOLDOWN_SECONDS, commands.BucketType.user)
    @commands.bot_has_permissions(embed_links=True)
    async def question(self, ctx: commands.Context, *, query: str):
        async with ctx.typing():
            results = await self._try_ddgs(query)

            if results:
                embed = discord.Embed(title=f"🔎 Results for: {query}", color=discord.Color.blue())
                for r in results:
                    title = (r.get("title") or "Untitled")[:256]
                    snippet = (r.get("body") or "")[:200]
                    link = r.get("href") or ""
                    embed.add_field(name=title, value=f"{snippet}\n{link}", inline=False)
                embed.set_footer(text="Results via DuckDuckGo")
                await ctx.send(embed=embed)
                return

            # Web search unavailable or blocked — fall back to Wikipedia.
            summary = await self._try_wikipedia(query)
            if summary and summary.get("extract"):
                embed = discord.Embed(
                    title=f"🔎 {summary.get('title', query)}",
                    description=summary["extract"][:1500],
                    color=discord.Color.blue(),
                )
                page_url = summary.get("content_urls", {}).get("desktop", {}).get("page")
                if page_url:
                    embed.url = page_url
                embed.set_footer(text="Results via Wikipedia (web search unavailable right now)")
                await ctx.send(embed=embed)
                return

            await ctx.send(
                f"Couldn't find anything for **{query}**. Try rephrasing it, or the search service "
                "might be temporarily unavailable."
            )


async def setup(bot: commands.Bot):
    await bot.add_cog(Search(bot))
