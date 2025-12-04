# main.py

import logging
from telegram import Update, Chat, ChatMember
from telegram.constants import ParseMode
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    ContextTypes,
    filters,
)

from config import BOT_TOKEN, OWNER_ID
import database as db

logging.basicConfig(level=logging.INFO)
log = logging.getLogger(__name__)

db.init_db()

# ---------------------------------------------------
# PERMISSION HELPERS
# ---------------------------------------------------
async def is_owner_or_sudo(uid: int) -> bool:
    if uid == OWNER_ID:
        return True
    return uid in db.get_sudos()

async def is_group_admin(bot, chat_id: int, user_id: int) -> bool:
    try:
        m: ChatMember = await bot.get_chat_member(chat_id, user_id)
        return m.status in ("administrator", "creator")
    except:
        return False

def groups_only(func):
    async def wrapper(update: Update, context: ContextTypes.DEFAULT_TYPE):
        chat = update.effective_chat
        if chat is None or chat.type not in (Chat.GROUP, Chat.SUPERGROUP):
            return await update.message.reply_text("❌ Groups only.")
        return await func(update, context)
    return wrapper

# ---------------------------------------------------
# START
# ---------------------------------------------------
@groups_only
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Bot active in this group.")

# ---------------------------------------------------
# SUDO MANAGEMENT
# ---------------------------------------------------
@groups_only
async def addsudo(update, context):
    uid = update.effective_user.id
    if not await is_owner_or_sudo(uid):
        return await update.message.reply_text("❌ Unauthorized.")

    if not context.args:
        return await update.message.reply_text("Usage: /addsudo <id>")

    try:
        target = int(context.args[0])
    except:
        return await update.message.reply_text("Invalid ID.")

    db.add_sudo(target)
    await update.message.reply_text(f"Added sudo:\n`{target}`", parse_mode=ParseMode.MARKDOWN)

@groups_only
async def rmsudo(update, context):
    uid = update.effective_user.id
    if not await is_owner_or_sudo(uid):
        return await update.message.reply_text("❌ Unauthorized.")

    if not context.args:
        return await update.message.reply_text("Usage: /rmsudo <id>")

    try:
        target = int(context.args[0])
    except:
        return await update.message.reply_text("Invalid ID.")

    db.rm_sudo(target)
    await update.message.reply_text(f"Removed sudo:\n`{target}`", parse_mode=ParseMode.MARKDOWN)

# ---------------------------------------------------
# GLOBAL ADMINS
# ---------------------------------------------------
@groups_only
async def addadmin(update, context):
    uid = update.effective_user.id
    if not await is_owner_or_sudo(uid):
        return await update.message.reply_text("❌ Unauthorized.")

    if not context.args:
        return await update.message.reply_text("Usage: /addadmin <id>")

    try:
        target = int(context.args[0])
    except:
        return await update.message.reply_text("Invalid ID.")

    db.add_global_admin(target)
    await update.message.reply_text(f"Added global admin `{target}`", parse_mode=ParseMode.MARKDOWN)

@groups_only
async def rmadmin(update, context):
    uid = update.effective_user.id
    if not await is_owner_or_sudo(uid):
        return await update.message.reply_text("❌ Unauthorized.")

    if not context.args:
        return await update.message.reply_text("Usage: /rmadmin <id>")

    try:
        target = int(context.args[0])
    except:
        return await update.message.reply_text("Invalid ID.")

    db.rm_global_admin(target)
    await update.message.reply_text(f"Removed admin `{target}`", parse_mode=ParseMode.MARKDOWN)

# ---------------------------------------------------
# ALL STAFF
# ---------------------------------------------------
@groups_only
async def allstaff(update, context):
    uid = update.effective_user.id
    if not await is_owner_or_sudo(uid):
        return await update.message.reply_text("❌ Unauthorized.")

    sudos = db.get_sudos()
    text = f"👑 Owner: [Owner](tg://user?id={OWNER_ID}) (`{OWNER_ID}`)\n\n"

    if sudos:
        text += "🔧 Sudos:\n"
        for s in sudos:
            text += f"- [User](tg://user?id={s}) (`{s}`)\n"
    else:
        text += "No sudos configured."

    await update.message.reply_text(text, parse_mode=ParseMode.MARKDOWN)

# ---------------------------------------------------
# DIRECTORY — CLEAN OUTPUT
# ---------------------------------------------------
@groups_only
async def directory(update, context):
    uid = update.effective_user.id
    chat = update.effective_chat

    # Permission: owner/sudo OR group admin
    if not (await is_owner_or_sudo(uid) or await is_group_admin(context.bot, chat.id, uid)):
        return await update.message.reply_text("❌ No permission to view directory.")

    rows = db.get_directory()
    if not rows:
        return await update.message.reply_text("📭 Directory empty.")

    # Clean bullet list
    lines = []
    for r in rows:
        name = r["title"] or "Unnamed"
        link = r["link"]
        lines.append(f"• [{name}]({link})")

    await update.message.reply_text("\n".join(lines), parse_mode=ParseMode.MARKDOWN)

# ---------------------------------------------------
# ADD GROUP — BOT MUST BE ADMIN
# ---------------------------------------------------
@groups_only
async def addgroup(update, context):
    uid = update.effective_user.id
    if not await is_owner_or_sudo(uid):
        return await update.message.reply_text("❌ Unauthorized.")

    if len(context.args) < 2:
        return await update.message.reply_text("Usage: /addgroup <group-id> <invite-link>")

    try:
        cid = int(context.args[0])
    except:
        return await update.message.reply_text("Invalid chat ID.")

    link = context.args[1]

    # Check bot is admin
    try:
        bot_member = await context.bot.get_chat_member(cid, context.bot.id)
        if bot_member.status not in ("administrator", "creator"):
            return await update.message.reply_text("❌ Bot must be admin in that group.")
    except:
        return await update.message.reply_text("❌ Bot is not in that group.")

    # Fetch chat title
    try:
        chat = await context.bot.get_chat(cid)
        title = chat.title or "Unnamed Group"
    except:
        title = "Unnamed Group"

    db.add_directory(cid, "group", link, title)
    await update.message.reply_text(f"✅ Added **{title}** to directory.")

# ---------------------------------------------------
# ADD CHANNEL — BOT MUST BE ADMIN
# ---------------------------------------------------
@groups_only
async def addchannel(update, context):
    uid = update.effective_user.id
    if not await is_owner_or_sudo(uid):
        return await update.message.reply_text("❌ Unauthorized.")

    if len(context.args) < 2:
        return await update.message.reply_text("Usage: /addchannel <channel-id> <invite-link>")

    try:
        cid = int(context.args[0])
    except:
        return await update.message.reply_text("Invalid ID.")

    link = context.args[1]

    # Check bot admin
    try:
        bot_member = await context.bot.get_chat_member(cid, context.bot.id)
        if bot_member.status not in ("administrator", "creator"):
            return await update.message.reply_text("❌ Bot must be admin in that channel.")
    except:
        return await update.message.reply_text("❌ Bot cannot access that channel.")

    # Fetch title
    try:
        chat = await context.bot.get_chat(cid)
        title = chat.title or "Unnamed Channel"
    except:
        title = "Unnamed Channel"

    db.add_directory(cid, "channel", link, title)
    await update.message.reply_text(f"📡 Added **{title}** to directory.")

# ---------------------------------------------------
# REMOVE FROM DIRECTORY
# ---------------------------------------------------
@groups_only
async def rmgroup(update, context):
    uid = update.effective_user.id
    if not await is_owner_or_sudo(uid):
        return await update.message.reply_text("❌ Unauthorized.")

    if not context.args:
        return await update.message.reply_text("Usage: /rmgroup <id>")

    db.rm_directory(int(context.args[0]))
    await update.message.reply_text("🗑 Group removed.")

@groups_only
async def rmchannel(update, context):
    uid = update.effective_user.id
    if not await is_owner_or_sudo(uid):
        return await update.message.reply_text("❌ Unauthorized.")

    if not context.args:
        return await update.message.reply_text("Usage: /rmchannel <id>")

    db.rm_directory(int(context.args[0]))
    await update.message.reply_text("🗑 Channel removed.")

# ---------------------------------------------------
# NBAN / UNBAN — GLOBAL
# ---------------------------------------------------
@groups_only
async def nban(update, context):
    uid = update.effective_user.id
    if not await is_owner_or_sudo(uid):
        return await update.message.reply_text("❌ Unauthorized.")

    if not context.args:
        return await update.message.reply_text("Usage: /nban <user_id>")

    target = int(context.args[0])
    rows = db.get_directory()
    if not rows:
        return await update.message.reply_text("Directory empty.")

    db.add_global_ban(target)
    ok = fail = 0

    for r in rows:
        try:
            await context.bot.ban_chat_member(r["chat_id"], target)
            ok += 1
        except:
            fail += 1

    await update.message.reply_text(f"Global ban → OK: {ok}, Failed: {fail}")

@groups_only
async def unban(update, context):
    uid = update.effective_user.id
    if not await is_owner_or_sudo(uid):
        return await update.message.reply_text("❌ Unauthorized.")

    if not context.args:
        return await update.message.reply_text("Usage: /unban <user_id>")

    target = int(context.args[0])
    rows = db.get_directory()
    if not rows:
        return await update.message.reply_text("Directory empty.")

    db.rm_global_ban(target)
    ok = fail = 0

    for r in rows:
        try:
            await context.bot.unban_chat_member(r["chat_id"], target)
            ok += 1
        except:
            fail += 1

    await update.message.reply_text(f"Global unban → OK: {ok}, Failed: {fail}")

# ---------------------------------------------------
# GINFO — OWNER/SUDO ONLY
# ---------------------------------------------------
@groups_only
async def ginfo(update, context):
    uid = update.effective_user.id
    if not await is_owner_or_sudo(uid):
        return await update.message.reply_text("❌ Owner/Sudo only.")

    if context.args:
        chat_id = int(context.args[0])
    else:
        chat_id = update.effective_chat.id

    try:
        chat = await context.bot.get_chat(chat_id)
        members = await context.bot.get_chat_members_count(chat_id)
        await update.message.reply_text(
            f"**Group Info**\n"
            f"Title: `{chat.title}`\n"
            f"ID: `{chat_id}`\n"
            f"Type: `{chat.type}`\n"
            f"Members: `{members}`",
            parse_mode=ParseMode.MARKDOWN
        )
    except:
        await update.message.reply_text("❌ Cannot fetch info.")

# ---------------------------------------------------
# MAIN APP
# ---------------------------------------------------
def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("addsudo", addsudo))
    app.add_handler(CommandHandler("rmsudo", rmsudo))
    app.add_handler(CommandHandler("addadmin", addadmin))
    app.add_handler(CommandHandler("rmadmin", rmadmin))
    app.add_handler(CommandHandler("allstaff", allstaff))
    app.add_handler(CommandHandler("directory", directory))
    app.add_handler(CommandHandler("addgroup", addgroup))
    app.add_handler(CommandHandler("addchannel", addchannel))
    app.add_handler(CommandHandler("rmgroup", rmgroup))
    app.add_handler(CommandHandler("rmchannel", rmchannel))
    app.add_handler(CommandHandler("nban", nban))
    app.add_handler(CommandHandler("unban", unban))
    app.add_handler(CommandHandler("ginfo", ginfo))

    print("Bot running... (PTB v21, Groups Only)")
    app.run_polling()

if __name__ == "__main__":
    main()
