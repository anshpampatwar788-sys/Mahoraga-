import os
import discord
from discord.ext import commands

STAFF_ROLE_NAME = os.getenv("STAFF_ROLE_NAME", "Staff")


def is_staff():
    """Allows the command only for members with the Administrator or
    Moderate Members (Discord's built-in 'moderator' permission) permission,
    or the configured staff role (STAFF_ROLE_NAME in .env, default 'Staff')."""

    async def predicate(ctx: commands.Context) -> bool:
        if ctx.guild is None:
            raise commands.CheckFailure("This command can only be used in a server.")
        perms = ctx.author.guild_permissions
        if perms.administrator or perms.moderate_members:
            return True
        role_names = {role.name.lower() for role in ctx.author.roles}
        if STAFF_ROLE_NAME.lower() in role_names:
            return True
        raise commands.CheckFailure(
            f"You need Moderator or Administrator permissions (or the **{STAFF_ROLE_NAME}** role) "
            "to use this command."
        )

    return commands.check(predicate)


def check_hierarchy(moderator: discord.Member, target: discord.Member):
    """Returns an error string if `moderator` should NOT be allowed to act on
    `target` (kick/ban/timeout/warn), or None if the action is allowed."""
    guild = moderator.guild

    if target.id == moderator.id:
        return "You can't do that to yourself."
    if target.id == guild.me.id:
        return "You can't do that to me."
    if target.id == guild.owner_id:
        return "You can't take action against the server owner."
    if moderator.id != guild.owner_id and target.top_role >= moderator.top_role:
        return "You can't take action against someone with an equal or higher role than you."
    if target.top_role >= guild.me.top_role:
        return "That member's role is higher than or equal to mine — ask an admin to move my role up."
    return None
