import datetime
import discord
from discord.ext import commands, tasks
from discord import app_commands

from utils import storage
from utils.checks import is_staff

MONTH_NAMES = [
    "January", "February", "March", "April", "May", "June",
    "July", "August", "September", "October", "November", "December",
]
DAYS_IN_MONTH = [31, 29, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31]


class Birthdays(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.check_birthdays.start()

    def cog_unload(self):
        self.check_birthdays.cancel()

    @commands.hybrid_command(name="setbirthday", description="Set your birthday (month and day).")
    @app_commands.describe(month="Month (1-12)", day="Day of the month")
    async def setbirthday(self, ctx: commands.Context, month: int, day: int):
        if not (1 <= month <= 12):
            await ctx.send("Month must be between 1 and 12.")
            return
        if not (1 <= day <= DAYS_IN_MONTH[month - 1]):
            await ctx.send(f"Day must be between 1 and {DAYS_IN_MONTH[month - 1]} for that month.")
            return
        storage.set_birthday(ctx.author.id, month, day)
        await ctx.send(f"🎂 Birthday set to **{MONTH_NAMES[month - 1]} {day}**.")

    @commands.hybrid_command(name="birthday", description="Check a member's birthday.")
    @app_commands.describe(member="Whose birthday to check (defaults to you)")
    async def birthday(self, ctx: commands.Context, member: discord.Member = None):
        member = member or ctx.author
        bday = storage.get_birthday(member.id)
        if not bday:
            await ctx.send(f"{member.display_name} hasn't set a birthday yet.")
            return
        await ctx.send(f"🎂 **{member.display_name}**'s birthday is {MONTH_NAMES[bday['month'] - 1]} {bday['day']}.")

    @commands.hybrid_command(name="upcomingbirthdays", description="Show the next upcoming birthdays.")
    async def upcomingbirthdays(self, ctx: commands.Context):
        all_bdays = storage.get_all_birthdays()
        if not all_bdays:
            await ctx.send("No birthdays have been set yet.")
            return

        today = datetime.datetime.now(datetime.timezone.utc).date()
        entries = []
        for uid, b in all_bdays.items():
            try:
                next_date = datetime.date(today.year, b["month"], b["day"])
            except ValueError:
                continue  # e.g. Feb 29 in a non-leap year
            if next_date < today:
                try:
                    next_date = datetime.date(today.year + 1, b["month"], b["day"])
                except ValueError:
                    continue
            days_until = (next_date - today).days
            entries.append((days_until, int(uid), b))
        entries.sort()

        if not entries:
            await ctx.send("No upcoming birthdays found.")
            return

        lines = []
        for days_until, uid, b in entries[:10]:
            user = self.bot.get_user(uid)
            name = user.display_name if user else f"User {uid}"
            when = "🎉 Today!" if days_until == 0 else f"in {days_until} day(s)"
            lines.append(f"🎂 **{name}** — {MONTH_NAMES[b['month'] - 1]} {b['day']} ({when})")

        embed = discord.Embed(title="🎉 Upcoming Birthdays", description="\n".join(lines), color=discord.Color.pink())
        await ctx.send(embed=embed)

    @commands.hybrid_command(name="setbirthdaychannel", description="[Staff] Set the channel for birthday announcements.")
    @app_commands.describe(channel="Channel to post birthday announcements in (defaults to here)")
    @is_staff()
    async def setbirthdaychannel(self, ctx: commands.Context, channel: discord.TextChannel = None):
        channel = channel or ctx.channel
        storage.set_config("birthday_channel_id", channel.id)
        await ctx.send(f"🎂 Birthday announcements will now be posted in {channel.mention}.")

    @tasks.loop(time=datetime.time(hour=9, tzinfo=datetime.timezone.utc))
    async def check_birthdays(self):
        channel_id = storage.get_config("birthday_channel_id")
        if not channel_id:
            return
        channel = self.bot.get_channel(channel_id)
        if not channel:
            return

        today = datetime.datetime.now(datetime.timezone.utc)
        all_bdays = storage.get_all_birthdays()
        for uid, b in all_bdays.items():
            if b["month"] == today.month and b["day"] == today.day:
                user = self.bot.get_user(int(uid))
                mention = user.mention if user else f"<@{uid}>"
                await channel.send(f"🎉🎂 Happy Birthday {mention}!! Hope it's a great one! 🎂🎉")

    @check_birthdays.before_loop
    async def before_check_birthdays(self):
        await self.bot.wait_until_ready()


async def setup(bot: commands.Bot):
    await bot.add_cog(Birthdays(bot))
