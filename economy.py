import discord
from discord.ext import commands
from discord import app_commands
from datetime import datetime, timezone, timedelta

from utils import storage
from utils.checks import is_staff

DAILY_AMOUNT = 300
DAILY_COOLDOWN_HOURS = 24


class Economy(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.hybrid_command(name="balance", description="Check your points balance.")
    @app_commands.describe(member="Whose balance to check (defaults to you)")
    async def balance(self, ctx: commands.Context, member: discord.Member = None):
        member = member or ctx.author
        bal = storage.get_balance(member.id)
        await ctx.send(f"💰 **{member.display_name}** has **{bal}** points.")

    @commands.hybrid_command(name="daily", description="Claim your daily points bonus.")
    async def daily(self, ctx: commands.Context):
        last = storage.get_last_daily(ctx.author.id)
        now = datetime.now(timezone.utc)
        if last:
            last_dt = datetime.fromisoformat(last)
            elapsed = now - last_dt
            if elapsed < timedelta(hours=DAILY_COOLDOWN_HOURS):
                remaining = timedelta(hours=DAILY_COOLDOWN_HOURS) - elapsed
                hours, rem = divmod(int(remaining.total_seconds()), 3600)
                minutes = rem // 60
                await ctx.send(f"You already claimed today. Try again in {hours}h {minutes}m.")
                return
        new_balance = storage.add_balance(ctx.author.id, DAILY_AMOUNT)
        storage.set_last_daily(ctx.author.id, now.isoformat())
        await ctx.send(f"🎁 You claimed your daily **{DAILY_AMOUNT}** points! Balance: **{new_balance}**.")

    @commands.hybrid_command(name="leaderboard", description="Show the top point holders.")
    async def leaderboard(self, ctx: commands.Context):
        top = storage.get_leaderboard(10)
        if not top:
            await ctx.send("No one has any points yet.")
            return
        lines = []
        for i, (user_id, bal) in enumerate(top, start=1):
            user = self.bot.get_user(user_id)
            name = user.display_name if user else f"User {user_id}"
            lines.append(f"**{i}.** {name} — {bal} points")
        embed = discord.Embed(title="🏆 Points Leaderboard", description="\n".join(lines), color=discord.Color.gold())
        await ctx.send(embed=embed)

    @commands.hybrid_command(name="pay", description="Send points to another user.")
    @app_commands.describe(member="Who to pay", amount="How many points to send")
    async def pay(self, ctx: commands.Context, member: discord.Member, amount: int):
        if amount <= 0:
            await ctx.send("Amount must be positive.")
            return
        if member.id == ctx.author.id:
            await ctx.send("You can't pay yourself.")
            return
        if member.bot:
            await ctx.send("You can't pay a bot.")
            return
        if storage.get_balance(ctx.author.id) < amount:
            await ctx.send("You don't have enough points.")
            return
        storage.add_balance(ctx.author.id, -amount)
        storage.add_balance(member.id, amount)
        await ctx.send(f"✅ {ctx.author.display_name} sent **{amount}** points to {member.display_name}.")

    @commands.hybrid_command(name="grant", description="[Admin] Give points to a user.")
    @app_commands.describe(member="Who to give points to", amount="How many points to grant")
    @is_staff()
    async def grant(self, ctx: commands.Context, member: discord.Member, amount: int):
        new_balance = storage.add_balance(member.id, amount)
        await ctx.send(f"✅ Granted **{amount}** points to {member.display_name}. New balance: **{new_balance}**.")


async def setup(bot: commands.Bot):
    await bot.add_cog(Economy(bot))
