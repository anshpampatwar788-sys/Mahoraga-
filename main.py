import os
import sys
import asyncio
import importlib.util
import subprocess
import discord
from discord.ext import commands
from dotenv import load_dotenv

load_dotenv()
TOKEN = os.getenv("DISCORD_TOKEN")

intents = discord.Intents.default()
intents.message_content = True
intents.members = True

bot = commands.Bot(command_prefix="!", intents=intents, help_command=None)


def print_startup_diagnostics():
    print("===== STARTUP DIAGNOSTICS =====")
    print(f"[diag] Python: {sys.version}")
    print(f"[diag] discord.__version__ = {discord.__version__}")

    spec = importlib.util.find_spec("davey")
    print(f"[diag] importlib.util.find_spec('davey') = {spec}")

    try:
        result = subprocess.run(
            [sys.executable, "-m", "pip", "show", "davey"],
            capture_output=True, text=True, timeout=10,
        )
        if result.returncode == 0:
            print(f"[diag] pip show davey:\n{result.stdout}")
        else:
            print(f"[diag] pip show davey FAILED (not installed?): {result.stderr.strip()}")
    except Exception as e:
        print(f"[diag] pip show davey raised an exception: {e}")

    try:
        result = subprocess.run(
            [sys.executable, "-m", "pip", "list"],
            capture_output=True, text=True, timeout=10,
        )
        relevant = [l for l in result.stdout.splitlines() if any(
            k in l.lower() for k in ["discord", "davey", "nacl", "opus", "yt-dlp"]
        )]
        print("[diag] relevant installed packages:\n" + "\n".join(relevant))
    except Exception as e:
        print(f"[diag] pip list raised an exception: {e}")

    print(f"[diag] discord.opus.is_loaded() = {discord.opus.is_loaded()}")
    print("===== END DIAGNOSTICS =====")


@bot.event
async def on_ready():
    print(f"{bot.user} (Mahoraga) is online and adapting.")
    try:
        synced = await bot.tree.sync()
        print(f"Synced {len(synced)} slash command(s).")
    except Exception as e:
        print(f"Slash command sync failed: {e}")


@bot.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.MissingPermissions):
        await ctx.send("You don't have permission to use that command.")
    elif isinstance(error, commands.BotMissingPermissions):
        await ctx.send("I don't have the permissions needed to do that.")
    elif isinstance(error, commands.CommandOnCooldown):
        minutes, seconds = divmod(int(error.retry_after), 60)
        hours, minutes = divmod(minutes, 60)
        parts = []
        if hours:
            parts.append(f"{hours}h")
        if minutes:
            parts.append(f"{minutes}m")
        if seconds or not parts:
            parts.append(f"{seconds}s")
        await ctx.send(f"⏳ That's on cooldown — try again in {' '.join(parts)}.")
    elif isinstance(error, commands.CheckFailure):
        await ctx.send(str(error) or "You can't use that command.")
    elif isinstance(error, commands.CommandNotFound):
        return
    elif isinstance(error, commands.MissingRequiredArgument):
        await ctx.send(f"Missing argument: `{error.param.name}`")
    else:
        await ctx.send("Something went wrong running that command.")
        raise error


async def load_cogs():
    for filename in os.listdir("./cogs"):
        if filename.endswith(".py") and not filename.startswith("__"):
            await bot.load_extension(f"cogs.{filename[:-3]}")


async def main():
    print_startup_diagnostics()
    if not TOKEN:
        raise RuntimeError("DISCORD_TOKEN not found. Copy .env.example to .env and add your bot token.")
    async with bot:
        await load_cogs()
        await bot.start(TOKEN)


if __name__ == "__main__":
    asyncio.run(main())
