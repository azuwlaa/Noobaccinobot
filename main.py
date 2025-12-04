import os
import sqlite3
import logging
from typing import Optional

try:
    from pyrotgfork import Client, filters
except:
    from pyrogram import Client, filters

from config import BOT_TOKEN, OWNER_ID, DB_PATH
from database import (
    init_db, get_db,
    add_sudo, rm_sudo, get_sudos,
    add_global_admin, rm_global_admin, get_global_admins,
    add_directory, rm_directory, get_directory,
    add_global_ban, rm_global_ban, get_global_bans
)

logging.basicConfig(level=logging.INFO)
log = logging.getLogger(__name__)


# Permission helpers
async def is_owner_or_sudo(app: Client, user_id: int) -> bool:
    if user_id == OWNER_ID:
        return True
    return user_id in get_sudos()


async def is_group_admin(app: Client, chat_id: int, user_id: int) -> bool:
    try:
        member = await app.get_chat_member(chat_id, user_id)
        return member.status in ("administrator", "creator")
    except:
        return False


# Initialize bot
app = Client("admin-bot", bot_token=BOT_TOKEN)

# Initialize database
init_db()


# Start command
@app.on_message(filters.command("start") & filters.private)
async def cmd_start(client, message):
    await message.reply_text("Bot is online and ready!")


# -----------------------------
# STAFF MANAGEMENT
# -----------------------------
@app.on_message(filters.command("addsudo"))
async def add_sudo_cmd(client, message):
    sender = message.from_user.id
    if not await is_owner_or_sudo(client, sender):
        return await message.reply_text("❌ Unauthorized")

    try:
        target = int(message.command[1])
    except:
        return await message.reply_text("Usage: /addsudo <user_id>")

    add_sudo(target)
    await message.reply_text(f"✅ Sudo added: `{target}`", parse_mode="md")


@app.on_message(filters.command("rmsudo"))
async def rm_sudo_cmd(client, message):
    sender = message.from_user.id
    if not await is_owner_or_sudo(client, sender):
        return await message.reply_text("❌ Unauthorized")

    try:
        target = int(message.command[1])
    except:
        return await message.reply_text("Usage: /rmsudo <user_id>")

    rm_sudo(target)
    await message.reply_text(f"✅ Sudo removed: `{target}`", parse_mode="md")


@app.on_message(filters.command("addadmin"))
async def add_admin_cmd(client, message):
    sender = message.from_user.id
    if not await is_owner_or_sudo(client, sender):
        return await message.reply_text("❌ Unauthorized")

    try:
        target = int(message.command[1])
    except:
        return await message.reply_text("Usage: /addadmin <user_id>")

    add_global_admin(target)
    await message.reply_text(f"✅ Global admin added: `{target}`", parse_mode="md")


@app.on_message(filters.command("rmadmin"))
async def rm_admin_cmd(client, message):
    sender = message.from_user.id
    if not await is_owner_or_sudo(client, sender):
        return await message.reply_text("❌ Unauthorized")

    try:
        target = int(message.command[1])
    except:
        return await message.reply_text("Usage: /rmadmin <user_id>")

    rm_global_admin(target)
    await message.reply_text(f"✅ Global admin removed: `{target}`", parse_mode="md")


@app.on_message(filters.command("allstaff"))
async def all_staff(client, message):
    if not await is_owner_or_sudo(client, message.from_user.id):
        return await message.reply_text("❌ Unauthorized")

    sudos = get_sudos()
    text = f"👑 **Owner:** [Owner](tg://user?id={OWNER_ID}) (`{OWNER_ID}`)\n\n"

    if sudos:
        text += "🔧 **Sudos:**\n"
        for uid in sudos:
            text += f"- [User](tg://user?id={uid}) (`{uid}`)\n"
    else:
        text += "No sudos added."

    await message.reply_text(text, parse_mode="md")


# -----------------------------
# DIRECTORY
# -----------------------------
@app.on_message(filters.command("directory"))
async def cmd_directory(client, message):
    user = message.from_user.id
    chat = message.chat

    allowed = False
    if await is_owner_or_sudo(client, user):
        allowed = True
    elif chat.type in ("group", "supergroup"):
        if await is_group_admin(client, chat.id, user):
            allowed = True

    if not allowed:
        return await message.reply_text("❌ No permission.")

    rows = get_directory()
    if not rows:
        return await message.reply_text("Directory empty.")

    text = ""
    for r in rows:
        text += f"- [{r['title']}]({r['link']}) — `{r['chat_id']}` ({r['chat_type']})\n"

    await message.reply_text(text, parse_mode="md")


@app.on_message(filters.command("addgroup"))
async def add_group_cmd(client, message):
    if not await is_owner_or_sudo(client, message.from_user.id):
        return await message.reply_text("❌ Unauthorized")

    try:
        cid = int(message.command[1])
        link = message.command[2]
    except:
        return await message.reply_text("Usage: /addgroup <id> <link>")

    title = None
    try:
        chat = await client.get_chat(cid)
        title = chat.title
    except:
        title = "Unknown"

    add_directory(cid, "group", link, title)
    await message.reply_text("✅ Group added to directory.")


@app.on_message(filters.command("rmgroup"))
async def rm_group_cmd(client, message):
    if not await is_owner_or_sudo(client, message.from_user.id):
        return await message.reply_text("❌ Unauthorized")

    try:
        cid = int(message.command[1])
    except:
        return await message.reply_text("Usage: /rmgroup <id>")

    rm_directory(cid)
    await message.reply_text("✅ Group removed.")


# CHANNEL MANAGEMENT
@app.on_message(filters.command("addchannel"))
async def add_channel_cmd(client, message):
    if not await is_owner_or_sudo(client, message.from_user.id):
        return await message.reply_text("❌ Unauthorized")

    try:
        cid = int(message.command[1])
        link = message.command[2]
    except:
        return await message.reply_text("Usage: /addchannel <id> <link>")

    title = None
    try:
        chat = await client.get_chat(cid)
        title = chat.title
    except:
        title = "Unknown"

    add_directory(cid, "channel", link, title)
    await message.reply_text("✅ Channel added.")


@app.on_message(filters.command("rmchannel"))
async def rm_channel_cmd(client, message):
    if not await is_owner_or_sudo(client, message.from_user.id):
        return await message.reply_text("❌ Unauthorized")

    try:
        cid = int(message.command[1])
    except:
        return await message.reply_text("Usage: /rmchannel <id>")

    rm_directory(cid)
    await message.reply_text("✅ Channel removed.")


# -----------------------------
# GLOBAL BAN SYSTEM
# -----------------------------
@app.on_message(filters.command("nban"))
async def global_ban(client, message):
    if not await is_owner_or_sudo(client, message.from_user.id):
        return await message.reply_text("❌ Unauthorized")

    try:
        target = int(message.command[1])
    except:
        return await message.reply_text("Usage: /nban <id>")

    rows = get_directory()

    add_global_ban(target)
    ok = no = 0

    for r in rows:
        try:
            await client.ban_chat_member(r["chat_id"], target)
            ok += 1
        except:
            no += 1

    await message.reply_text(f"Global ban complete. Success: {ok}, Failed: {no}")


@app.on_message(filters.command("unban"))
async def global_unban(client, message):
    if not await is_owner_or_sudo(client, message.from_user.id):
        return await message.reply_text("❌ Unauthorized")

    try:
        target = int(message.command[1])
    except:
        return await message.reply_text("Usage: /unban <id>")

    rm_global_ban(target)
    ok = no = 0

    for r in get_directory():
        try:
            await client.unban_chat_member(r["chat_id"], target)
            ok += 1
        except:
            no += 1

    await message.reply_text(f"Global unban complete. Success: {ok}, Failed: {no}")


# -----------------------------
# GINFO (Owner/Sudo only)
# -----------------------------
@app.on_message(filters.command("ginfo"))
async def ginfo_cmd(client, message):
    if not await is_owner_or_sudo(client, message.from_user.id):
        return await message.reply_text("❌ Unauthorized")

    target = None

    if len(message.command) > 1:
        try:
            target = int(message.command[1])
        except:
            return await message.reply_text("Usage: /ginfo <chat_id>")
    else:
        if message.chat.type in ("group", "supergroup"):
            target = message.chat.id
        else:
            return await message.reply_text("Use /ginfo <chat_id>.")

    try:
        chat = await client.get_chat(target)
        members = await client.get_chat_members_count(target)

        text = (
            f"📌 **Group Info**\n\n"
            f"Title: `{chat.title}`\n"
            f"ID: `{chat.id}`\n"
            f"Type: `{chat.type}`\n"
            f"Members: `{members}`\n"
        )

        await message.reply_text(text, parse_mode="md")

    except:
        await message.reply_text("Failed to fetch group info.")


# -----------------------------
# BOT RUN
# -----------------------------
if __name__ == "__main__":
    print("Bot starting...")
    app.run()
