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

WOULD_YOU_RATHER = [
    "be able to fly or be invisible?",
    "have unlimited tacos for life or unlimited pizza for life?",
    "always be 10 minutes late or always be 20 minutes early?",
    "know when you'll die or how you'll die?",
    "lose your sense of smell or your sense of taste?",
    "live without music or live without movies?",
    "be famous but poor or unknown but rich?",
    "fight one horse-sized duck or 100 duck-sized horses?",
]

TRUTHS = [
    "What's the most embarrassing thing you've done in front of a crowd?",
    "What's a secret talent nobody knows about?",
    "What's the worst gift you've ever received?",
    "What's something you pretend to understand but don't?",
    "What's the weirdest dream you remember?",
]

DARES = [
    "Type your next message using only emojis.",
    "Send a voice message singing the chorus of any song.",
    "Let the channel pick your profile picture for the next hour.",
    "Text the last person you messaged 'I know what you did.'",
    "Speak in rhymes for your next 3 messages.",
]

QUOTES = [
    "The best time to plant a tree was 20 years ago. The second best time is now.",
    "Done is better than perfect.",
    "Small steps every day add up to big change.",
    "You don't have to see the whole staircase, just take the first step.",
    "Discipline is choosing between what you want now and what you want most.",
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

    @commands.hybrid_command(name="wouldyourather", description="Get a random would-you-rather prompt.")
    async def wouldyourather(self, ctx: commands.Context):
        await ctx.send(f"🤔 Would you rather {random.choice(WOULD_YOU_RATHER)}")

    @commands.hybrid_command(name="truth", description="Get a random truth prompt.")
    async def truth(self, ctx: commands.Context):
        await ctx.send(f"💬 Truth: {random.choice(TRUTHS)}")

    @commands.hybrid_command(name="dare", description="Get a random dare prompt.")
    async def dare(self, ctx: commands.Context):
        await ctx.send(f"🔥 Dare: {random.choice(DARES)}")

    @commands.hybrid_command(name="quote", description="Get a random motivational quote.")
    async def quote(self, ctx: commands.Context):
        await ctx.send(f"📜 *{random.choice(QUOTES)}*")

    @commands.hybrid_command(name="reverse", description="Reverse some text.")
    @app_commands.describe(text="The text to reverse")
    async def reverse(self, ctx: commands.Context, *, text: str):
        await ctx.send(text[::-1])

    @commands.hybrid_command(name="choose", description="Let Mahoraga pick between options for you.")
    @app_commands.describe(options="Separate options with commas, e.g. pizza, tacos, sushi")
    async def choose(self, ctx: commands.Context, *, options: str):
        choices = [o.strip() for o in options.split(",") if o.strip()]
        if len(choices) < 2:
            await ctx.send("Give me at least two options, separated by commas.")
            return
        await ctx.send(f"🎯 I choose: **{random.choice(choices)}**")


async def setup(bot: commands.Bot):
    await bot.add_cog(Fun(bot))
