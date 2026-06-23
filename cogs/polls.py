import discord
from discord.ext import commands
from discord import app_commands


class PollView(discord.ui.View):
    def __init__(self, options: list, duration_minutes: int):
        timeout = duration_minutes * 60 if duration_minutes > 0 else None
        super().__init__(timeout=timeout)
        self.options = options
        self.votes = {i: set() for i in range(len(options))}
        self.message: discord.Message = None

        for i, opt in enumerate(options):
            btn = discord.ui.Button(label=opt[:80], style=discord.ButtonStyle.primary, row=i // 5)
            btn.callback = self._make_callback(i)
            self.add_item(btn)

    def _make_callback(self, index: int):
        async def callback(interaction: discord.Interaction):
            for voters in self.votes.values():
                voters.discard(interaction.user.id)
            self.votes[index].add(interaction.user.id)
            await interaction.response.edit_message(embed=self._build_embed(), view=self)
        return callback

    def _build_embed(self, closed: bool = False) -> discord.Embed:
        total = sum(len(v) for v in self.votes.values()) or 1
        embed = discord.Embed(
            title="📊 Poll (Closed)" if closed else "📊 Poll",
            color=discord.Color.dark_grey() if closed else discord.Color.blue(),
        )
        for i, opt in enumerate(self.options):
            count = len(self.votes[i])
            pct = round(count / total * 100)
            filled = pct // 10
            bar = "█" * filled + "░" * (10 - filled)
            embed.add_field(name=opt, value=f"{bar} {count} vote(s) ({pct}%)", inline=False)
        return embed

    async def on_timeout(self):
        for child in self.children:
            child.disabled = True
        if self.message:
            try:
                await self.message.edit(embed=self._build_embed(closed=True), view=self)
            except discord.HTTPException:
                pass


class Polls(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.hybrid_command(name="poll", description="Host a poll with up to 5 options.")
    @app_commands.describe(
        question="The poll question",
        option1="First option",
        option2="Second option",
        option3="Optional third option",
        option4="Optional fourth option",
        option5="Optional fifth option",
        duration_minutes="How long the poll stays open, in minutes (default 60, 0 = never auto-closes)",
    )
    async def poll(
        self,
        ctx: commands.Context,
        question: str,
        option1: str,
        option2: str,
        option3: str = None,
        option4: str = None,
        option5: str = None,
        duration_minutes: int = 60,
    ):
        options = [o for o in [option1, option2, option3, option4, option5] if o]
        if len(options) < 2:
            await ctx.send("A poll needs at least two options.")
            return
        if duration_minutes < 0:
            await ctx.send("Duration can't be negative.")
            return

        view = PollView(options, duration_minutes)
        embed = view._build_embed()
        embed.title = f"📊 {question}"
        embed.set_footer(text=f"Poll by {ctx.author.display_name}")
        msg = await ctx.send(embed=embed, view=view)
        view.message = msg


async def setup(bot: commands.Bot):
    await bot.add_cog(Polls(bot))
