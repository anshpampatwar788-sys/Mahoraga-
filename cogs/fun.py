import random
import discord
from discord.ext import commands
from discord import app_commands

JOKES = [
    "Why did the developer go broke? Because they used up all their cache.",
    "I'd tell you a UDP joke, but you might not get it.",
    "There are 10 types of people: those who understand binary and those who don't.",
    "Why do programmers prefer dark mode? Because light attracts bugs.",
    "I told my computer I needed a break, and now it won't stop sending me KitKats.",
]

EIGHT_BALL_RESPONSES = [
    "It is certain.", "Without a doubt.", "Yes, definitely.", "You may rely on it.",
    "Ask again later.", "Cannot predict now.", "Concentrate and ask again.",
    "Don't count on it.", "My reply is no.", "Outlook not so good.",
]


class Fun(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.hybrid_command(name="ping", description="Check Mahoraga's response time.")
    async def ping(self, ctx: commands.Context):
        await ctx.send(f"Adapting... 🏓 {round(self.bot.latency * 1000)}ms")

    @commands.hybrid_command(name="8ball", description="Ask Mahoraga a yes/no question.")
    @app_commands.describe(question="The question you want answered")
    async def eight_ball(self, ctx: commands.Context, *, question: str):
        await ctx.send(f"🎱 **{question}**\n{random.choice(EIGHT_BALL_RESPONSES)}")

    @commands.hybrid_command(name="coinflip", description="Flip a coin.")
    async def coinflip(self, ctx: commands.Context):
        await ctx.send(f"The coin landed on **{random.choice(['Heads', 'Tails'])}**.")

    @commands.hybrid_command(name="roll", description="Roll a dice, e.g. 2d6.")
    @app_commands.describe(dice="Format: NdM, e.g. 2d6 for two six-sided dice")
    async def roll(self, ctx: commands.Context, dice: str = "1d6"):
        try:
            count, sides = map(int, dice.lower().split("d"))
            if count < 1 or sides < 2 or count > 100:
                raise ValueError
        except ValueError:
            await ctx.send("Format must be NdM, like `2d6`.")
            return
        rolls = [random.randint(1, sides) for _ in range(count)]
        await ctx.send(f"🎲 Rolled {dice}: {', '.join(map(str, rolls))} (total: {sum(rolls)})")

    @commands.hybrid_command(name="joke", description="Get a random joke.")
    async def joke(self, ctx: commands.Context):
        await ctx.send(random.choice(JOKES))

    @commands.hybrid_command(name="avatar", description="Show a user's avatar.")
    @app_commands.describe(member="The member whose avatar to show (defaults to you)")
    async def avatar(self, ctx: commands.Context, member: discord.Member = None):
        member = member or ctx.author
        embed = discord.Embed(title=f"{member.display_name}'s avatar")
        embed.set_image(url=member.display_avatar.url)
        await ctx.send(embed=embed)


async def setup(bot: commands.Bot):
    await bot.add_cog(Fun(bot))
