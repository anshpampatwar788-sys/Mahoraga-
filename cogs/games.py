import random
import discord
from discord.ext import commands
from discord import app_commands

from utils import storage

RPS_CHOICES = ["🪨 Rock", "📄 Paper", "✂️ Scissors"]
RPS_BEATS = {0: 2, 1: 0, 2: 1}  # key beats value: rock>scissors, paper>rock, scissors>paper

TRIVIA_QUESTIONS = [
    {"q": "What is the capital of Japan?", "options": ["Seoul", "Tokyo", "Beijing", "Bangkok"], "answer": 1},
    {"q": "How many continents are there on Earth?", "options": ["5", "6", "7", "8"], "answer": 2},
    {"q": "What is the largest planet in our solar system?", "options": ["Earth", "Saturn", "Jupiter", "Neptune"], "answer": 2},
    {"q": "Which language is Discord's bot library 'discord.py' written in?", "options": ["Java", "Python", "C++", "Rust"], "answer": 1},
    {"q": "What is the chemical symbol for gold?", "options": ["Go", "Gd", "Au", "Ag"], "answer": 2},
    {"q": "How many sides does a hexagon have?", "options": ["5", "6", "7", "8"], "answer": 1},
    {"q": "What is the smallest prime number?", "options": ["0", "1", "2", "3"], "answer": 2},
    {"q": "Which ocean is the largest?", "options": ["Atlantic", "Indian", "Arctic", "Pacific"], "answer": 3},
    {"q": "What does CPU stand for?", "options": [
        "Central Process Unit", "Central Processing Unit", "Computer Personal Unit", "Core Processing Unit"
    ], "answer": 1},
    {"q": "How many minutes are in a full day?", "options": ["1200", "1440", "1320", "1500"], "answer": 1},
    {"q": "What is the freezing point of water in Celsius?", "options": ["0°C", "32°C", "100°C", "-10°C"], "answer": 0},
    {"q": "Which planet is known as the Red Planet?", "options": ["Venus", "Mars", "Jupiter", "Mercury"], "answer": 1},
]

TRIVIA_REWARD = 50


class RPSView(discord.ui.View):
    def __init__(self, player: discord.Member, bet: int):
        super().__init__(timeout=30)
        self.player = player
        self.bet = bet
        self.answered = False
        for i, label in enumerate(RPS_CHOICES):
            btn = discord.ui.Button(label=label, style=discord.ButtonStyle.secondary)
            btn.callback = self._make_callback(i)
            self.add_item(btn)

    def _make_callback(self, choice: int):
        async def callback(interaction: discord.Interaction):
            if interaction.user.id != self.player.id:
                await interaction.response.send_message("This isn't your game.", ephemeral=True)
                return
            if self.answered:
                return
            self.answered = True
            bot_choice = random.randint(0, 2)
            for child in self.children:
                child.disabled = True

            if choice == bot_choice:
                outcome = "🤝 It's a tie! Your bet is unchanged."
            elif RPS_BEATS[choice] == bot_choice:
                if self.bet:
                    storage.add_balance(self.player.id, self.bet)
                outcome = f"🎉 You win! +{self.bet} points." if self.bet else "🎉 You win!"
            else:
                if self.bet:
                    storage.add_balance(self.player.id, -self.bet)
                outcome = f"💀 You lose! -{self.bet} points." if self.bet else "💀 You lose!"

            await interaction.response.edit_message(
                content=f"You chose {RPS_CHOICES[choice]}, I chose {RPS_CHOICES[bot_choice]}.\n{outcome}",
                view=self,
            )
        return callback

    async def on_timeout(self):
        for child in self.children:
            child.disabled = True


class DuelView(discord.ui.View):
    def __init__(self, challenger: discord.Member, opponent: discord.Member, bet: int):
        super().__init__(timeout=60)
        self.challenger = challenger
        self.opponent = opponent
        self.bet = bet
        self.resolved = False

    @discord.ui.button(label="Accept", style=discord.ButtonStyle.success)
    async def accept(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.opponent.id:
            await interaction.response.send_message("This duel isn't addressed to you.", ephemeral=True)
            return
        if self.resolved:
            return
        if storage.get_balance(self.challenger.id) < self.bet or storage.get_balance(self.opponent.id) < self.bet:
            self.resolved = True
            for child in self.children:
                child.disabled = True
            await interaction.response.edit_message(
                content="One of you no longer has enough points. Duel cancelled.", view=self
            )
            return

        self.resolved = True
        winner = random.choice([self.challenger, self.opponent])
        loser = self.opponent if winner.id == self.challenger.id else self.challenger
        storage.add_balance(winner.id, self.bet)
        storage.add_balance(loser.id, -self.bet)
        for child in self.children:
            child.disabled = True
        await interaction.response.edit_message(
            content=f"⚔️ **{winner.display_name}** wins the duel and takes **{self.bet}** points from {loser.display_name}!",
            view=self,
        )

    @discord.ui.button(label="Decline", style=discord.ButtonStyle.danger)
    async def decline(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.opponent.id:
            await interaction.response.send_message("This duel isn't addressed to you.", ephemeral=True)
            return
        if self.resolved:
            return
        self.resolved = True
        for child in self.children:
            child.disabled = True
        await interaction.response.edit_message(content=f"{self.opponent.display_name} declined the duel.", view=self)

    async def on_timeout(self):
        if not self.resolved:
            for child in self.children:
                child.disabled = True


class TriviaView(discord.ui.View):
    def __init__(self, player: discord.Member, question: dict, reward: int):
        super().__init__(timeout=20)
        self.player = player
        self.correct_index = question["answer"]
        self.reward = reward
        self.answered = False
        for i, opt in enumerate(question["options"]):
            btn = discord.ui.Button(label=opt, style=discord.ButtonStyle.primary)
            btn.callback = self._make_callback(i)
            self.add_item(btn)

    def _make_callback(self, index: int):
        async def callback(interaction: discord.Interaction):
            if interaction.user.id != self.player.id:
                await interaction.response.send_message("This isn't your question.", ephemeral=True)
                return
            if self.answered:
                return
            self.answered = True
            for child in self.children:
                child.disabled = True
            if index == self.correct_index:
                new_balance = storage.add_balance(self.player.id, self.reward)
                msg = f"✅ Correct! +{self.reward} points (balance: {new_balance})."
            else:
                correct_label = self.children[self.correct_index].label
                msg = f"❌ Wrong! The correct answer was **{correct_label}**."
            await interaction.response.edit_message(content=msg, view=self)
        return callback

    async def on_timeout(self):
        for child in self.children:
            child.disabled = True


class Games(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.hybrid_command(name="rps", description="Play rock-paper-scissors against Mahoraga.")
    @app_commands.describe(bet="Points to bet, optional (default 0)")
    @commands.cooldown(1, 3600, commands.BucketType.user)
    async def rps(self, ctx: commands.Context, bet: int = 0):
        if bet < 0:
            ctx.command.reset_cooldown(ctx)
            await ctx.send("Bet can't be negative.")
            return
        if bet > 0 and storage.get_balance(ctx.author.id) < bet:
            ctx.command.reset_cooldown(ctx)
            await ctx.send("You don't have enough points for that bet.")
            return
        view = RPSView(ctx.author, bet)
        await ctx.send(f"🪨📄✂️ {ctx.author.display_name}, pick one!", view=view)

    @commands.hybrid_command(name="duel", description="Challenge another member to a points duel.")
    @app_commands.describe(opponent="Who to challenge", bet="Points on the line")
    @commands.cooldown(1, 3600, commands.BucketType.user)
    async def duel(self, ctx: commands.Context, opponent: discord.Member, bet: int):
        if bet <= 0:
            ctx.command.reset_cooldown(ctx)
            await ctx.send("Bet must be a positive number.")
            return
        if opponent.id == ctx.author.id:
            ctx.command.reset_cooldown(ctx)
            await ctx.send("You can't duel yourself.")
            return
        if opponent.bot:
            ctx.command.reset_cooldown(ctx)
            await ctx.send("You can't duel a bot.")
            return
        if storage.get_balance(ctx.author.id) < bet:
            ctx.command.reset_cooldown(ctx)
            await ctx.send("You don't have enough points for that bet.")
            return
        if storage.get_balance(opponent.id) < bet:
            ctx.command.reset_cooldown(ctx)
            await ctx.send(f"{opponent.display_name} doesn't have enough points to accept that bet.")
            return
        view = DuelView(ctx.author, opponent, bet)
        await ctx.send(
            f"⚔️ {opponent.mention}, **{ctx.author.display_name}** challenges you to a duel for **{bet}** points! Accept?",
            view=view,
        )

    @commands.hybrid_command(name="trivia", description="Answer a trivia question for bonus points.")
    @commands.cooldown(1, 5400, commands.BucketType.user)
    async def trivia(self, ctx: commands.Context):
        question = random.choice(TRIVIA_QUESTIONS)
        view = TriviaView(ctx.author, question, TRIVIA_REWARD)
        await ctx.send(f"🧠 **{question['q']}**", view=view)


async def setup(bot: commands.Bot):
    await bot.add_cog(Games(bot))
