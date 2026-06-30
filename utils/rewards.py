import discord
from discord.ext import commands
from discord import app_commands

from utils import storage
from utils.checks import is_staff

CLAIM_CHANNEL_NAME = "#claim-tickets"


class RewardShop(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self._seed_default_rewards()

    def _seed_default_rewards(self):
        """Populate the shop with placeholder rewards on first run only —
        never overwrites if items already exist (e.g. after an admin edits the catalog)."""
        if storage.get_all_reward_items():
            return
        placeholders = [
            ("🥈 Silver Reward", "A silver-tier placeholder reward.", 7500, None, "Placeholder"),
            ("🥉 Bronze Reward", "A bronze-tier placeholder reward.", 10000, None, "Placeholder"),
            ("🥇 Gold Reward", "A gold-tier placeholder reward.", 10000, None, "Placeholder"),
            ("💎 Diamond Reward", "A diamond-tier placeholder reward.", 10000, None, "Placeholder"),
            ("🌟 Community Reward", "A community-tier placeholder reward.", 10000, None, "Placeholder"),
            ("🎉 Event Reward", "An event placeholder reward.", 10000, None, "Placeholder"),
            ("🏆 Champion Reward", "The top-tier placeholder reward.", 15000, None, "Placeholder"),
        ]
        for name, desc, cost, stock, category in placeholders:
            storage.add_reward_item(name, desc, cost, stock, category)

    reward = app_commands.Group(name="reward", description="Reward Points shop and redemption commands.")

    # ---------- USER COMMANDS ----------

    @reward.command(name="shop", description="Browse the Reward Points shop.")
    async def shop(self, interaction: discord.Interaction):
        items = storage.get_all_reward_items(enabled_only=True)
        if not items:
            await interaction.response.send_message("The reward shop is empty right now.", ephemeral=True)
            return

        embed = discord.Embed(
            title="🛍️ Reward Shop",
            description="Redeem with `/reward redeem <id>`. Use `/reward history` to track your redemptions.",
            color=discord.Color.gold(),
        )
        current_category = None
        for item in items:
            stock_text = "Unlimited" if item["stock"] is None else f"{item['stock']} left"
            field_value = f"{item['description']}\n**Cost:** {item['cost']} RP · **Stock:** {stock_text} · **ID:** `{item['id']}`"
            embed.add_field(name=item["name"], value=field_value, inline=False)
        await interaction.response.send_message(embed=embed)

    @reward.command(name="redeem", description="Redeem a reward using your Reward Points.")
    @app_commands.describe(reward_id="The ID of the reward (shown in /reward shop)")
    async def redeem(self, interaction: discord.Interaction, reward_id: int):
        item = storage.get_reward_item(reward_id)
        if not item:
            await interaction.response.send_message("That reward doesn't exist.", ephemeral=True)
            return
        if not item.get("enabled", True):
            await interaction.response.send_message("That reward isn't currently available.", ephemeral=True)
            return
        if item["stock"] is not None and item["stock"] <= 0:
            await interaction.response.send_message("That reward is out of stock.", ephemeral=True)
            return

        balance = storage.get_balance(interaction.user.id)
        if balance < item["cost"]:
            await interaction.response.send_message(
                f"You need **{item['cost']}** RP for this, but you only have **{balance}**.", ephemeral=True
            )
            return

        if not storage.decrement_reward_stock(reward_id):
            await interaction.response.send_message("That reward just sold out — sorry!", ephemeral=True)
            return

        storage.add_balance(interaction.user.id, -item["cost"])
        record = storage.create_redemption(interaction.user.id, item)

        await interaction.response.send_message(
            f"🎉 **Reward redeemed successfully!**\n\n"
            f"🆔 **Redemption ID:** `{record['redemption_id']}`\n\n"
            f"Please claim your reward by creating a ticket in {CLAIM_CHANNEL_NAME} and include your "
            f"Redemption ID so the staff team can verify your claim.",
            ephemeral=True,
        )

        log_channel_id = storage.get_config("reward_log_channel_id")
        if log_channel_id:
            channel = self.bot.get_channel(log_channel_id)
            if channel:
                embed = discord.Embed(title="🛍️ New Redemption", color=discord.Color.purple())
                embed.add_field(name="User", value=f"{interaction.user.mention} ({interaction.user.id})", inline=False)
                embed.add_field(name="Reward", value=item["name"], inline=True)
                embed.add_field(name="Cost", value=f"{item['cost']} RP", inline=True)
                embed.add_field(name="Redemption ID", value=record["redemption_id"], inline=True)
                try:
                    await channel.send(embed=embed)
                except discord.Forbidden:
                    pass

    @reward.command(name="history", description="View your reward redemption history.")
    async def history(self, interaction: discord.Interaction):
        records = storage.get_user_redemptions(interaction.user.id)
        if not records:
            await interaction.response.send_message("You haven't redeemed anything yet.", ephemeral=True)
            return

        embed = discord.Embed(title="📜 Your Redemption History", color=discord.Color.blue())
        for r in sorted(records, key=lambda x: x["timestamp"], reverse=True)[:15]:
            status = "✅ Claimed" if r["claimed"] else "⏳ Not Claimed"
            date = r["timestamp"][:10]
            embed.add_field(
                name=f"{r['redemption_id']} — {r['item_name']}",
                value=f"{date} · {status}",
                inline=False,
            )
        await interaction.response.send_message(embed=embed, ephemeral=True)

    # ---------- ADMIN COMMANDS ----------

    @reward.command(name="additem", description="[Staff] Add a new reward to the shop.")
    @app_commands.describe(
        name="Reward name", description="Reward description", cost="Cost in Reward Points",
        category="Category name", stock="Limited stock amount (leave blank for unlimited)",
    )
    @is_staff()
    async def additem(
        self, interaction: discord.Interaction, name: str, description: str, cost: int,
        category: str = "General", stock: int = None,
    ):
        if cost <= 0:
            await interaction.response.send_message("Cost must be positive.", ephemeral=True)
            return
        item = storage.add_reward_item(name, description, cost, stock, category)
        await interaction.response.send_message(f"✅ Added **{item['name']}** (ID `{item['id']}`) to the shop.", ephemeral=True)

    @reward.command(name="edititem", description="[Staff] Edit an existing reward.")
    @app_commands.describe(
        reward_id="The reward's ID", name="New name", description="New description",
        cost="New cost in Reward Points", category="New category",
    )
    @is_staff()
    async def edititem(
        self, interaction: discord.Interaction, reward_id: int, name: str = None,
        description: str = None, cost: int = None, category: str = None,
    ):
        item = storage.edit_reward_item(reward_id, name=name, description=description, cost=cost, category=category)
        if not item:
            await interaction.response.send_message("No reward found with that ID.", ephemeral=True)
            return
        await interaction.response.send_message(f"✅ Updated **{item['name']}** (ID `{item['id']}`).", ephemeral=True)

    @reward.command(name="removeitem", description="[Staff] Remove a reward from the shop.")
    @app_commands.describe(reward_id="The reward's ID")
    @is_staff()
    async def removeitem(self, interaction: discord.Interaction, reward_id: int):
        if storage.remove_reward_item(reward_id):
            await interaction.response.send_message(f"🗑️ Removed reward ID `{reward_id}`.", ephemeral=True)
        else:
            await interaction.response.send_message("No reward found with that ID.", ephemeral=True)

    @reward.command(name="stock", description="[Staff] Update a reward's stock.")
    @app_commands.describe(reward_id="The reward's ID", amount="New stock amount (leave blank for unlimited)")
    @is_staff()
    async def stock(self, interaction: discord.Interaction, reward_id: int, amount: int = None):
        item = storage.set_reward_stock(reward_id, amount)
        if not item:
            await interaction.response.send_message("No reward found with that ID.", ephemeral=True)
            return
        stock_text = "unlimited" if amount is None else str(amount)
        await interaction.response.send_message(f"✅ **{item['name']}** stock set to **{stock_text}**.", ephemeral=True)

    @reward.command(name="toggle", description="[Staff] Enable or disable a reward.")
    @app_commands.describe(reward_id="The reward's ID")
    @is_staff()
    async def toggle(self, interaction: discord.Interaction, reward_id: int):
        item = storage.toggle_reward_item(reward_id)
        if not item:
            await interaction.response.send_message("No reward found with that ID.", ephemeral=True)
            return
        state = "enabled ✅" if item["enabled"] else "disabled 🚫"
        await interaction.response.send_message(f"**{item['name']}** is now {state}.", ephemeral=True)

    @reward.command(name="claimed", description="[Staff] Mark a redemption as claimed after delivering it.")
    @app_commands.describe(member="The member who redeemed it", redemption_id="The redemption ID, e.g. RW-0001")
    @is_staff()
    async def claimed(self, interaction: discord.Interaction, member: discord.Member, redemption_id: str):
        if storage.mark_redemption_claimed(member.id, redemption_id):
            await interaction.response.send_message(f"✅ Marked `{redemption_id}` as claimed for {member.display_name}.", ephemeral=True)
        else:
            await interaction.response.send_message("Couldn't find that redemption ID for that member.", ephemeral=True)

    @reward.command(name="setlogchannel", description="[Staff] Set the channel where new redemptions are logged.")
    @app_commands.describe(channel="Channel for redemption logs (defaults to here)")
    @is_staff()
    async def setlogchannel(self, interaction: discord.Interaction, channel: discord.TextChannel = None):
        channel = channel or interaction.channel
        storage.set_config("reward_log_channel_id", channel.id)
        await interaction.response.send_message(f"📋 Redemption logs will now post in {channel.mention}.", ephemeral=True)


async def setup(bot: commands.Bot):
    await bot.add_cog(RewardShop(bot))
