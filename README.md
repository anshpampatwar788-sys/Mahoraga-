# Mahoraga

A Discord bot with fun commands, moderation tools, a points economy, gambling and PvP games, polls, a web-search command, a birthday tracker, a suggestion box, and a claim-based drop system.

## Commands

**Fun:** `ping`, `8ball`, `coinflip`, `roll`, `joke`, `avatar`

**Economy:** `balance`, `daily` (300 points/day), `leaderboard`, `pay`, `grant` *(Mod/Admin)*

**Gambling & Games:** `mines`, `slots`, `rps` (rock-paper-scissors vs the bot, optional bet), `duel` (challenge another member, winner takes the pot), `trivia` (answer for bonus points)

**Birthdays:** `setbirthday`, `birthday`, `upcomingbirthdays`, `setbirthdaychannel` *(Mod/Admin)* — the bot checks daily at 9:00 UTC and announces birthdays in the configured channel

**Suggestions:** `suggest` — posts to a suggestions channel with 👍/👎 reactions for voting; `setsuggestionchannel` *(Mod/Admin)* sets where they go

**Polls:** `poll` — up to 5 options, live vote-count bars, auto-closes after a set time

**Search:** `question` — ask anything, Mahoraga searches the web and returns top results

**Drops:** `drop` *(Mod/Admin)* — posts an embed with a Claim button; first click gets the info you typed, sent privately. Optionally restrict to a role.

**Moderation** *(Mod/Admin only)*: `kick`, `ban`, `timeout`, `untimeout`, `clear`, `slowmode`, `warn`

All commands work as both `!prefix` commands and `/slash` commands. Run `/help` any time for the full list in Discord.

## Setup

1. **Create the application**
   - Go to https://discord.com/developers/applications → New Application → name it `Mahoraga`.
   - Go to the **Bot** tab → click **Reset Token** → copy the token (you'll only see it once).
   - Under **Privileged Gateway Intents**, enable **Server Members Intent** and **Message Content Intent**.

2. **Invite it to your server**
   - Go to **OAuth2 → URL Generator**.
   - Scopes: `bot` and `applications.commands`.
   - Bot permissions: Administrator (simplest), or pick individually: Kick Members, Ban Members, Moderate Members, Manage Messages, Manage Channels, Send Messages, Embed Links, Add Reactions, Read Message History.
   - Open the generated URL and add the bot to your server.
   - **Important:** in Server Settings → Roles, drag the bot's own role **above** any role you want it to be able to moderate. Discord won't let it act on equal-or-higher roles no matter what the code says.

3. **Install and run**
   ```bash
   pip install -r requirements.txt
   cp .env.example .env
   # paste your token into .env
   python main.py
   ```

   On first run it syncs slash commands — they may take a minute to show up in Discord.

4. **One-time channel setup** (in your server, as a mod/admin):
   - `/setbirthdaychannel #channel` — where birthday shoutouts get posted
   - `/setsuggestionchannel #channel` — where suggestions get posted

## Moderation permissions & safety guards

- **Who can use mod commands:** anyone with the **Moderate Members** or **Administrator** Discord permission, or a role named **Staff** (configurable via `STAFF_ROLE_NAME` in `.env`).
- **Role-hierarchy guard:** moderators can't kick, ban, timeout, or warn anyone whose top role is equal to or higher than their own, and no one but the server owner can act on the owner.
- **Input guards:** timeouts capped at 28 days, slowmode at 6 hours, `clear` at 100 messages, bets/payments/duels must be positive numbers the user can actually afford.

## Notes

- Points, birthdays, and channel settings are stored in plain JSON files under `data/`. Fine for one server; swap `utils/storage.py` for a real database (SQLite/Postgres) if you scale up.
- The birthday check runs once a day at 9:00 UTC — adjust the `time=` value in `cogs/birthdays.py` if your community is mostly in a different timezone.
- `/question` uses the `duckduckgo-search` package, which scrapes public search results — no API key needed, but it can occasionally break if DuckDuckGo changes their page layout.
- `drop` is generic by design — type whatever prize text you want claimed (a code, a link, instructions). It doesn't manage external accounts or services; you control what gets sent.
- Restart the bot any time you edit a cog, or use a hot-reload extension if you want live editing.
