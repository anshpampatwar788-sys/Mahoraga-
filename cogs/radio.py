import asyncio
import discord
from discord.ext import commands
from discord import app_commands
from collections import deque

try:
    import yt_dlp
except ImportError:
    yt_dlp = None

YDL_OPTS = {
    "format": "bestaudio/best",
    "noplaylist": True,
    "quiet": True,
    "default_search": "ytsearch",
    "source_address": "0.0.0.0",
}

FFMPEG_OPTS = {
    "before_options": "-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5",
    "options": "-vn",
}

AUTO_LEAVE_SECONDS = 30


class Track:
    def __init__(self, title, stream_url, requester, webpage_url=None):
        self.title = title
        self.stream_url = stream_url
        self.requester = requester
        self.webpage_url = webpage_url


class GuildMusicState:
    def __init__(self):
        self.queue = deque()
        self.voice_client = None
        self.current = None
        self.volume = 0.5


class Radio(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.states = {}

    def get_state(self, guild_id: int) -> GuildMusicState:
        if guild_id not in self.states:
            self.states[guild_id] = GuildMusicState()
        return self.states[guild_id]

    async def _extract(self, query: str):
        def _run():
            with yt_dlp.YoutubeDL(YDL_OPTS) as ydl:
                info = ydl.extract_info(query, download=False)
                if "entries" in info:
                    info = info["entries"][0]
                return info
        return await self.bot.loop.run_in_executor(None, _run)

    async def _play_next(self, guild: discord.Guild):
        state = self.get_state(guild.id)
        if not state.queue:
            state.current = None
            return
        track = state.queue.popleft()
        state.current = track
        source = discord.FFmpegPCMAudio(track.stream_url, **FFMPEG_OPTS)
        source = discord.PCMVolumeTransformer(source, volume=state.volume)

        def after_play(error):
            if error:
                print(f"[radio] playback error: {error}")
            asyncio.run_coroutine_threadsafe(self._play_next(guild), self.bot.loop)

        if state.voice_client and state.voice_client.is_connected():
            state.voice_client.play(source, after=after_play)

    @commands.hybrid_command(name="play", description="Play a song in your voice channel.")
    @app_commands.describe(query="Song name, or a YouTube/SoundCloud link")
    @commands.bot_has_permissions(connect=True, speak=True)
    async def play(self, ctx: commands.Context, *, query: str):
        if yt_dlp is None:
            await ctx.send("Music isn't set up yet — `yt-dlp` and `PyNaCl` need to be installed on the host.")
            return
        if not ctx.author.voice or not ctx.author.voice.channel:
            await ctx.send("Join a voice channel first!")
            return

        if ctx.interaction:
            await ctx.defer()

        state = self.get_state(ctx.guild.id)
        voice_channel = ctx.author.voice.channel

        if state.voice_client is None or not state.voice_client.is_connected():
            try:
                state.voice_client = await voice_channel.connect()
            except discord.ClientException:
                await ctx.send("Couldn't connect to your voice channel.")
                return

        try:
            info = await self._extract(query)
        except Exception as e:
            print(f"[radio] extract failed: {e}")
            await ctx.send("Couldn't find or load that track. Try a different search term or link.")
            return

        track = Track(
            title=info.get("title", "Unknown title"),
            stream_url=info.get("url"),
            requester=ctx.author,
            webpage_url=info.get("webpage_url"),
        )
        state.queue.append(track)
        await ctx.send(f"➕ Queued **{track.title}**")

        if not state.voice_client.is_playing() and not state.voice_client.is_paused():
            await self._play_next(ctx.guild)

    @commands.hybrid_command(name="skip", description="Skip the current song.")
    async def skip(self, ctx: commands.Context):
        state = self.get_state(ctx.guild.id)
        if state.voice_client and (state.voice_client.is_playing() or state.voice_client.is_paused()):
            state.voice_client.stop()
            await ctx.send("⏭️ Skipped.")
        else:
            await ctx.send("Nothing is playing.")

    @commands.hybrid_command(name="pause", description="Pause playback.")
    async def pause(self, ctx: commands.Context):
        state = self.get_state(ctx.guild.id)
        if state.voice_client and state.voice_client.is_playing():
            state.voice_client.pause()
            await ctx.send("⏸️ Paused.")
        else:
            await ctx.send("Nothing is playing.")

    @commands.hybrid_command(name="resume", description="Resume playback.")
    async def resume(self, ctx: commands.Context):
        state = self.get_state(ctx.guild.id)
        if state.voice_client and state.voice_client.is_paused():
            state.voice_client.resume()
            await ctx.send("▶️ Resumed.")
        else:
            await ctx.send("Nothing is paused.")

    @commands.hybrid_command(name="stop", description="Stop playback, clear the queue, and leave the voice channel.")
    async def stop(self, ctx: commands.Context):
        state = self.get_state(ctx.guild.id)
        state.queue.clear()
        state.current = None
        if state.voice_client:
            await state.voice_client.disconnect()
            state.voice_client = None
        await ctx.send("⏹️ Stopped and left the voice channel.")

    @commands.hybrid_command(name="leave", description="Disconnect from the voice channel.")
    async def leave(self, ctx: commands.Context):
        await self.stop(ctx)

    @commands.hybrid_command(name="queue", description="Show the upcoming song queue.")
    async def queue_cmd(self, ctx: commands.Context):
        state = self.get_state(ctx.guild.id)
        if not state.current and not state.queue:
            await ctx.send("The queue is empty.")
            return
        lines = []
        if state.current:
            lines.append(f"▶️ **Now playing:** {state.current.title}")
        for i, t in enumerate(state.queue, start=1):
            lines.append(f"{i}. {t.title} (requested by {t.requester.display_name})")
        embed = discord.Embed(title="🎶 Queue", description="\n".join(lines), color=discord.Color.blurple())
        await ctx.send(embed=embed)

    @commands.hybrid_command(name="nowplaying", description="Show the currently playing track.")
    async def nowplaying(self, ctx: commands.Context):
        state = self.get_state(ctx.guild.id)
        if not state.current:
            await ctx.send("Nothing is playing right now.")
            return
        t = state.current
        embed = discord.Embed(
            title="▶️ Now Playing",
            description=f"[{t.title}]({t.webpage_url})" if t.webpage_url else t.title,
            color=discord.Color.blurple(),
        )
        embed.set_footer(text=f"Requested by {t.requester.display_name}")
        await ctx.send(embed=embed)

    @commands.hybrid_command(name="volume", description="Set the playback volume (0-150).")
    @app_commands.describe(level="Volume percentage, 0-150")
    async def volume(self, ctx: commands.Context, level: int):
        if not (0 <= level <= 150):
            await ctx.send("Volume must be between 0 and 150.")
            return
        state = self.get_state(ctx.guild.id)
        state.volume = level / 100
        if state.voice_client and state.voice_client.source:
            state.voice_client.source.volume = state.volume
        await ctx.send(f"🔊 Volume set to {level}%.")

    @commands.Cog.listener()
    async def on_voice_state_update(self, member: discord.Member, before, after):
        if member.bot:
            return
        state = self.states.get(member.guild.id)
        if not state or not state.voice_client:
            return
        channel = state.voice_client.channel
        if channel and all(m.bot for m in channel.members):
            asyncio.create_task(self._auto_leave_if_still_empty(member.guild.id, channel))

    async def _auto_leave_if_still_empty(self, guild_id: int, channel: discord.VoiceChannel):
        await asyncio.sleep(AUTO_LEAVE_SECONDS)
        state = self.states.get(guild_id)
        if state and state.voice_client and state.voice_client.channel == channel:
            if all(m.bot for m in channel.members):
                state.queue.clear()
                state.current = None
                await state.voice_client.disconnect()
                state.voice_client = None


async def setup(bot: commands.Bot):
    await bot.add_cog(Radio(bot))
