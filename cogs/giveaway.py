import discord
from discord.ext import commands
from discord import app_commands

from utils.checks import is_staff


class ClaimView(discord.ui.View):
    def __init__(self, prize_info: str, claimer_role: discord.Role = None):
        super().__init__(timeout=None)
        self.prize_info = prize_info
        self.claimer_role = claimer_role
        self.claimed = False
        self.winner: discord.Member = None

    @discord.ui.button(label="🎁 Claim", style=discord.ButtonStyle.success)
    async def claim(self, interaction: discord.Interaction, button: discord.ui.Button):
        if self.claimed:
            await interaction.response.send_message("Too slow — this drop has already been claimed.", ephemeral=True)
            return
        if self.claimer_role and self.claimer_role not in interaction.user.roles:
            await interaction.response.send_message(
                f"You need the {self.claimer_role.mention} role to claim this.", ephemeral=True
            )
            return

        self.claimed = True
        self.winner = interaction.user
        button.disabled = True
        button.label = f"Claimed by {interaction.user.display_name}"

        await interaction.response.edit_message(view=self)
        await interaction.followup.send(f"🎉 Here's your prize:\n{self.prize_info}", ephemeral=True)


class Giveaway(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.hybrid_command(name="drop", description="[Admin] Post a claimable drop. First click wins.")
    @app_commands.describe(
        title="Title shown on the drop announcement",
        prize_info="The info sent privately to whoever claims it",
        description="Optional extra text shown publicly on the drop",
        required_role="Optional role required to be eligible to claim",
    )
    @is_staff()
    async def drop(
        self,
        ctx: commands.Context,
        title: str,
        prize_info: str,
        description: str = None,
        required_role: discord.Role = None,
    ):
        embed = discord.Embed(
            title=f"🎁 {title}",
            description=description or "First to click **Claim** gets it!",
            color=discord.Color.purple(),
        )
        if required_role:
            embed.set_footer(text=f"Requires the {required_role.name} role")

        view = ClaimView(prize_info, claimer_role=required_role)
        await ctx.send(embed=embed, view=view)


async def setup(bot: commands.Bot):
    await bot.add_cog(Giveaway(bot))
