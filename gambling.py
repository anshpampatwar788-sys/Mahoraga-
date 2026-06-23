import random
import discord
from discord.ext import commands
from discord import app_commands

from utils import storage

GRID_COLUMNS = 5
GRID_ROWS = 4
TOTAL_TILES = GRID_COLUMNS * GRID_ROWS
HOUSE_EDGE = 0.97


class MinesView(discord.ui.View):
    def __init__(self, player: discord.Member, bet: int, bombs: int):
        super().__init__(timeout=120)
        self.player = player
        self.bet = bet
        self.bombs = bombs
        self.revealed = 0
        self.multiplier = 1.0
        self.bomb_positions = set(random.sample(range(TOTAL_TILES), bombs))
        self.game_over = False

        for i in range(TOTAL_TILES):
            row = i // GRID_COLUMNS
            btn = discord.ui.Button(label="?", style=discord.ButtonStyle.secondary, row=row)
            btn.callback = self._make_tile_callback(i, btn)
            self.add_item(btn)

        cashout_btn = discord.ui.Button(label="Cash Out", style=discord.ButtonStyle.success, row=GRID_ROWS)
        cashout_btn.callback = self._cashout_callback
        self.add_item(cashout_btn)

    def _make_tile_callback(self, index: int, button: discord.ui.Button):
        async def callback(interaction: discord.Interaction):
            if interaction.user.id != self.player.id:
                await interaction.response.send_message("This isn't your game.", ephemeral=True)
                return
            if self.game_over:
                return
            if index in self.bomb_positions:
                self.game_over = True
                button.label = "💣"
                button.style = discord.ButtonStyle.danger
                self._reveal_all_bombs()
                self._disable_all()
                await interaction.response.edit_message(
                    content=f"💥 Boom! You hit a mine and lost **{self.bet}** points.",
                    view=self,
                )
            else:
                self.revealed += 1
                safe_remaining_before = (TOTAL_TILES - self.bombs) - (self.revealed - 1)
                total_remaining_before = TOTAL_TILES - (self.revealed - 1)
                self.multiplier *= (total_remaining_before / safe_remaining_before) * HOUSE_EDGE
                button.label = "💎"
                button.style = discord.ButtonStyle.success
                button.disabled = True
                payout = int(self.bet * self.multiplier)
                if self.revealed >= (TOTAL_TILES - self.bombs):
                    self.game_over = True
                    self._disable_all()
                    storage.add_balance(self.player.id, payout)
                    await interaction.response.edit_message(
                        content=f"🎉 All gems found! You cashed out **{payout}** points (x{self.multiplier:.2f}).",
                        view=self,
                    )
                else:
                    await interaction.response.edit_message(
                        content=f"💎 Safe! Multiplier: x{self.multiplier:.2f} — potential payout: **{payout}** points.",
                        view=self,
                    )
        return callback

    async def _cashout_callback(self, interaction: discord.Interaction):
        if interaction.user.id != self.player.id:
            await interaction.response.send_message("This isn't your game.", ephemeral=True)
            return
        if self.game_over:
            return
        if self.revealed == 0:
            await interaction.response.send_message("Reveal at least one tile before cashing out.", ephemeral=True)
            return
        self.game_over = True
        payout = int(self.bet * self.multiplier)
        storage.add_balance(self.player.id, payout)
        self._disable_all()
        await interaction.response.edit_message(
            content=f"💰 Cashed out **{payout}** points (x{self.multiplier:.2f}).",
            view=self,
        )

    def _reveal_all_bombs(self):
        for i, item in enumerate(self.children[:TOTAL_TILES]):
            if i in self.bomb_positions:
                item.label = "💣"
                item.style = discord.ButtonStyle.danger

    def _disable_all(self):
        for item in self.children:
            item.disabled = True

    async def on_timeout(self):
        self.game_over = True
        self._disable_all()


class Gambling(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.hybrid_command(name="mines", description="Play Mines! Bet points and avoid the bombs.")
    @app_commands.describe(bet="How many points to bet", bombs="Number of bombs (1-15, default 3)")
    async def mines(self, ctx: commands.Context, bet: int, bombs: int = 3):
        if bet <= 0:
            await ctx.send("Bet must be a positive number.")
            return
        if storage.get_balance(ctx.author.id) < bet:
            await ctx.send("You don't have enough points for that bet.")
            return
        if not (1 <= bombs <= TOTAL_TILES - 1):
            await ctx.send(f"Bombs must be between 1 and {TOTAL_TILES - 1}.")
            return
        storage.add_balance(ctx.author.id, -bet)
        view = MinesView(ctx.author, bet, bombs)
        await ctx.send(
            f"💣 **Mines** — {ctx.author.display_name} bet **{bet}** points with **{bombs}** bombs. Pick a tile!",
            view=view,
        )

    @commands.hybrid_command(name="slots", description="Spin the slots and try your luck.")
    @app_commands.describe(bet="How many points to bet")
    async def slots(self, ctx: commands.Context, bet: int):
        if bet <= 0:
            await ctx.send("Bet must be a positive number.")
            return
        if storage.get_balance(ctx.author.id) < bet:
            await ctx.send("You don't have enough points for that bet.")
            return
        symbols = ["🍒", "🍋", "🍇", "⭐", "💎", "7️⃣"]
        reels = [random.choice(symbols) for _ in range(3)]
        storage.add_balance(ctx.author.id, -bet)

        if reels[0] == reels[1] == reels[2]:
            multiplier = 10 if reels[0] == "7️⃣" else 5
            winnings = bet * multiplier
            storage.add_balance(ctx.author.id, winnings)
            result = f"🎉 JACKPOT! You won **{winnings}** points (x{multiplier})!"
        elif reels[0] == reels[1] or reels[1] == reels[2] or reels[0] == reels[2]:
            winnings = int(bet * 1.5)
            storage.add_balance(ctx.author.id, winnings)
            result = f"You matched two! Won **{winnings}** points."
        else:
            result = f"No match. You lost **{bet}** points."

        await ctx.send(f"🎰 [ {' | '.join(reels)} ]\n{result}")


async def setup(bot: commands.Bot):
    await bot.add_cog(Gambling(bot))
