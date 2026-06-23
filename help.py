import discord
from discord.ext import commands


class Help(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.hybrid_command(name="help", description="Show everything Mahoraga can do.")
    async def help(self, ctx: commands.Context):
        embed = discord.Embed(
            title="🌀 Mahoraga — Commands",
            description="Adapting to whatever you need. Works with `!command` or `/command`.",
            color=discord.Color.dark_purple(),
        )
        embed.add_field(name="🎉 Fun", value="`ping` `8ball` `coinflip` `roll` `joke` `avatar`", inline=False)
        embed.add_field(name="💰 Economy", value="`balance` `daily` `leaderboard` `pay`", inline=False)
        embed.add_field(name="🎲 Gambling & Games", value="`mines` `slots` `rps` `duel` `trivia`", inline=False)
        embed.add_field(name="🎂 Birthdays", value="`setbirthday` `birthday` `upcomingbirthdays`", inline=False)
        embed.add_field(name="💡 Suggestions", value="`suggest`", inline=False)
        embed.add_field(name="📊 Polls", value="`poll` — host a vote with up to 5 options", inline=False)
        embed.add_field(name="🔎 Search", value="`question` — ask Mahoraga to search the web for you", inline=False)
        embed.add_field(name="🎁 Drops", value="`drop` *(Mod/Admin only)*", inline=False)
        embed.add_field(
            name="🛠️ Moderation *(Mod/Admin only)*",
            value="`kick` `ban` `timeout` `untimeout` `clear` `slowmode` `warn` `grant` `setbirthdaychannel` `setsuggestionchannel`",
            inline=False,
        )
        embed.set_footer(text="Moderators can't act on members with an equal or higher role than them.")
        await ctx.send(embed=embed)


async def setup(bot: commands.Bot):
    await bot.add_cog(Help(bot))
