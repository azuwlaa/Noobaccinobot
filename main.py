"""
Telegram Admin Bot using pyrotgfork
Features:
- Owner + Sudo + Global Admin system
- Add/remove sudo/admin
- Directory system (groups & channels)
- Global ban/unban
- /allstaff with hyperlinks
- /directory allowed for Owner/Sudo & group admins
- /ginfo only Owner/Sudo
"""

import os
import logging
from typing import Optional

# Force pyrotgfork only (no pyrogram fallback)
from pyrotgfork import Client, filters

from config import BOT_TOKEN, OWNER_ID, DB_PATH
from database import (
    init_db, get_db,
    add_sudo, rm_sudo, get_sudos,
    add_global_admin, rm_global_admin, get_global_admins,
    add_directory, rm_directory, get_directory,
    add_global_ban, rm_global_ban, get_global_bans
)

# Logging
logging.basicConfig(level=logging.INFO)
log = logging.getLogger(__name__)

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# PERMISSION CHECK HELPERS
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
async def is_owner_or_sudo(app: Client, user_id: int) -> bool:
    """Owner or Sudo returns TRUE"""
    if user_id == OWNER_ID:
        return True
    return user_id in get_sudos()


async def is_group_admin(app: Client, chat_id: int, user_id: int) -> bool:
    """Check if user is admin in a group"""
    try:
        member = await app.get_chat_member(chat_id, user_id)
        return member.status in ("administrator", "creator")
    except:
        return False


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# BOT INIT
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
app = Client("admin-bot", bot_token=BOT_TOKEN)
init_db()


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# BASIC COMMANDS
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
@app.on_message(filters.command("start"))
async def start_cmd(client, message):
    await message.reply_text("✅ Bot is running (pyrotgfork).")


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# SUDO MANAGEMENT (Owner + Sudo)
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
@app.on_message(filters.command("addsudo"))
async def add_sudo_cmd(client, message):
    if not await is_owner_or_sudo(client, message.from_user.id):
        return await message.reply_text("❌ Unauthorized")

    if len(message.command) < 2:
        return await message.reply_text("Usage: /addsudo <user_id>")

    target = int(message.command[1])
    add_sudo(target)
    await message.reply_text(f"✅ Sudo added: `{target}`", parse_mode="md")


@app.on_message(filters.command("rmsudo"))
async def remove_sudo_cmd(client, message):
    if not await is_owner_or_sudo(client, message.from_user.id):
        return await message.reply_text("❌ Unauthorized")

    if len(message.command) < 2:
        return await message.reply_text("Usage: /rmsudo <user_id>")

    target = int(message.command[1])
    rm_sudo(target)
    await message.reply_text(f"🗑 Removed sudo `{target}`", parse_mode="md")


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# GLOBAL ADMINS (Owner + Sudo)
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
@app.on_message(filters.command("addadmin"))
async def add_admin_cmd(client, message):
    if not await is_owner_or_sudo(client, message.from_user.id):
        return await message.reply_text("❌ Unauthorized")

    if len(message.command) < 2:
        return await message.reply_text("Usage: /addadmin <user_id>")

    target = int(message.command[1])
    add_global_admin(target)
    await message.reply_text(f"✅ Global admin added `{target}`")


@app.on_message(filters.command("rmadmin"))
async def rm_admin_cmd(client, message):
    if not await is_owner_or_sudo(client, message.from_user.id):
        return await message.reply_text("❌ Unauthorized")

    if len(message.command) < 2:
        return await message.reply_text("Usage: /rmadmin <user_id>")

    target = int(message.command[1])
    rm_global_admin(target)
    await message.reply_text(f"🗑 Global admin removed `{target}`")


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# ALL STAFF
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
@app.on_message(filters.command("allstaff"))
async def allstaff_cmd(client, message):
    if not await is_owner_or_sudo(client, message.from_user.id):
        return await message.reply_text("❌ Unauthorized")

    sudos = get_sudos()
    text = f"👑 **Owner:** [Owner](tg://user?id={OWNER_ID}) (`{OWNER_ID}`)\n\n"

    text += "🔧 **Sudos:**\n" if sudos else "No sudos.\n"

    for s in sudos:
        text += f"- [User](tg://user?id={s}) (`{s}`)\n"

    await message.reply_text(text, parse_mode="md")


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# DIRECTORY SYSTEM
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
@app.on_message(filters.command("directory"))
async def directory_cmd(client, message):
    sender = message.from_user.id
    chat = message.chat

    # Allowed: owner + sudo + group admins
    allowed = (
        await is_owner_or_sudo(client, sender)
        or (chat.type in ("group", "supergroup") and await is_group_admin(client, chat.id, sender))
    )

    if not allowed:
        return await message.reply_text("❌ You cannot use this command.")

    items = get_directory()
    if not items:
        return await message.reply_text("📭 Directory is empty.")

    text = ""
    for row in items:
        text += f"- [{row['title']}]({row['link']}) — `{row['chat_id']}` ({row['chat_type']})\n"

    await message.reply_text(text, parse_mode="md")


@app.on_message(filters.command("addgroup"))
async def add_group_cmd(client, message):
    if not await is_owner_or_sudo(client, message.from_user.id):
        return await message.reply_text("❌ Unauthorized")

    if len(message.command) < 3:
        return await message.reply_text("Usage: /addgroup <chat_id> <group_link>")

    cid = int(message.command[1])
    link = message.command[2]

    try:
        chat = await client.get_chat(cid)
        title = chat.title or "Unknown Group"
    except:
        title = "Unknown Group"

    add_directory(cid, "group", link, title)
    await message.reply_text("✅ Group added.")


@app.on_message(filters.command("rmgroup"))
async def rm_group_cmd(client, message):
    if not await is_owner_or_sudo(client, message.from_user.id):
        return await message.reply_text("❌ Unauthorized")

    if len(message.command) < 2:
        return await message.reply_text("Usage: /rmgroup <chat_id>")

    cid = int(message.command[1])
    rm_directory(cid)
    await message.reply_text("🗑 Group removed.")


@app.on_message(filters.command("addchannel"))
async def add_channel_cmd(client, message):
    if not await is_owner_or_sudo(client, message.from_user.id):
        return await message.reply_text("❌ Unauthorized")

    if len(message.command) < 3:
        return await message.reply_text("Usage: /addchannel <chat_id> <link>")

    cid = int(message.command[1])
    link = message.command[2]

    try:
        chat = await client.get_chat(cid)
        title = chat.title or "Unknown Channel"
    except:
        title = "Unknown Channel"

    add_directory(cid, "channel", link, title)
    await message.reply_text("📡 Channel added.")


@app.on_message(filters.command("rmchannel"))
async def rm_channel_cmd(client, message):
    if not await is_owner_or_sudo(client, message.from_user.id):
        return await message.reply_text("❌ Unauthorized")

    if len(message.command) < 2:
        return await message.reply_text("Usage: /rmchannel <chat_id>")

    cid = int(message.command[1])
    rm_directory(cid)
    await message.reply_text("🗑 Channel removed.")


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# GLOBAL BAN SYSTEM
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
@app.on_message(filters.command("nban"))
async def nban_cmd(client, message):
    if not await is_owner_or_sudo(client, message.from_user.id):
        return await message.reply_text("❌ Unauthorized")

    if len(message.command) < 2:
        return await message.reply_text("Usage: /nban <user_id>")

    target = int(message.command[1])
    add_global_ban(target)

    ok = fail = 0
    for d in get_directory():
        try:
            await client.ban_chat_member(d["chat_id"], target)
            ok += 1
        except:
            fail += 1

    await message.reply_text(f"🚫 Global Ban → Success: {ok}, Failed: {fail}")


@app.on_message(filters.command("unban"))
async def unban_cmd(client, message):
    if not await is_owner_or_sudo(client, message.from_user.id):
        return await message.reply_text("❌ Unauthorized")

    if len(message.command) < 2:
        return await message.reply_text("Usage: /unban <user_id>")

    target = int(message.command[1])
    rm_global_ban(target)

    ok = fail = 0
    for d in get_directory():
        try:
            await client.unban_chat_member(d["chat_id"], target)
            ok += 1
        except:
            fail += 1

    await message.reply_text(f"♻ Global Unban → Success: {ok}, Failed: {fail}")


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# GROUP INFO (Owner + Sudo ONLY)
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
@app.on_message(filters.command("ginfo"))
async def ginfo_cmd(client, message):
    if not await is_owner_or_sudo(client, message.from_user.id):
        return await message.reply_text("❌ Owner/Sudo only.")

    if len(message.command) >= 2:
        chat_id = int(message.command[1])
    else:
        if message.chat.type in ("group", "supergroup"):
            chat_id = message.chat.id
        else:
            return await message.reply_text("Usage: /ginfo <chat_id>")

    try:
        chat = await client.get_chat(chat_id)
        members = await client.get_chat_members_count(chat_id)

        text = (
            f"📊 **Group Info**:\n\n"
            f"Title: `{chat.title}`\n"
            f"ID: `{chat.id}`\n"
            f"Type: `{chat.type}`\n"
            f"Members: `{members}`\n"
        )

        await message.reply_text(text, parse_mode="md")
    except:
        await message.reply_text("❌ Could not fetch group info.")


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# RUN BOT
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
if __name__ == "__main__":
    print("Bot is running with pyrotgfork...")
    app.run()
