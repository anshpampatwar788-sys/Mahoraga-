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
        embed.add_field(
            name="🎉 Fun",
            value=(
                "`ping` `8ball` `coinflip` `roll` `joke` `avatar`\n"
                "`wouldyourather` `truth` `dare` `quote` `reverse` `choose`"
            ),
            inline=False,
        )
        embed.add_field(
            name="🛠️ Utility",
            value="`serverinfo` `userinfo` `rank` `remindme`",
            inline=False,
        )
        embed.add_field(name="💰 Economy", value="`balance` `daily` `leaderboard` `pay`", inline=False)
        embed.add_field(
            name="🛍️ Reward Shop",
            value="`/reward shop` `/reward redeem` `/reward history` *(Staff: additem, edititem, removeitem, stock, toggle, claimed, setlogchannel)*",
            inline=False,
        )
        embed.add_field(
            name="🎲 Gambling & Games",
            value=(
                "`mines` `slots` `rps` `duel` *(1hr cooldown each)*\n"
                "`trivia` *(1.5hr cooldown)*"
            ),
            inline=False,
        )
        embed.add_field(
            name="🎵 Radio",
            value="`play` `skip` `pause` `resume` `stop` `leave` `queue` `nowplaying` `volume`",
            inline=False,
        )
        embed.add_field(name="🎂 Birthdays", value="`setbirthday` `birthday` `upcomingbirthdays`", inline=False)
        embed.add_field(name="💡 Suggestions", value="`suggest`", inline=False)
        embed.add_field(name="📊 Polls", value="`poll` — host a vote with up to 5 options", inline=False)
        embed.add_field(
            name="🔎 Search",
            value="`question` — ask Mahoraga to search the web for you *(1min cooldown)*",
            inline=False,
        )
        embed.add_field(
            name="🎁 Drops",
            value="`drop` *(Mod/Admin only)* — winner gets the prize sent straight to their DMs",
            inline=False,
        )
        embed.add_field(
            name="🛠️ Moderation *(Mod/Admin only)*",
            value=(
                "`kick` `ban` `unban` `timeout` `untimeout` `clear` `purgeuser`\n"
                "`slowmode` `lock` `unlock` `nickname` `warn` `announce` `grant`\n"
                "`setbirthdaychannel` `setsuggestionchannel`"
            ),
            inline=False,
        )
        embed.add_field(
            name="👑 Owner only",
            value="`resetpoints` `resetallpoints`",
            inline=False,
        )
        embed.set_footer(text="Moderators can't act on members with an equal or higher role than them.")
        await ctx.send(embed=embed)


async def setup(bot: commands.Bot):
    await bot.add_cog(Help(bot))
