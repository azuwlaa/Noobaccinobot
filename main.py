# main.py
import logging
from typing import Optional

from telegram import Update, Chat, ChatMember, constants
from telegram.ext import (
    ApplicationBuilder,
    ContextTypes,
    CommandHandler,
    filters,
)

from config import BOT_TOKEN, OWNER_ID
import database as db

logging.basicConfig(level=logging.INFO)
log = logging.getLogger(__name__)

# initialize DB
db.init_db()

# ---------- Permission helpers ----------
async def is_owner_or_sudo(user_id: int) -> bool:
    if user_id == OWNER_ID:
        return True
    sudos = db.get_sudos()
    return user_id in sudos

async def is_group_admin(context: ContextTypes.DEFAULT_TYPE, chat_id: int, user_id: int) -> bool:
    try:
        member: ChatMember = await context.bot.get_chat_member(chat_id, user_id)
        return member.status in ("administrator", "creator")
    except Exception:
        return False

# ---------- Decorator-like guard for groups only ----------
def groups_only(func):
    async def wrapper(update: Update, context: ContextTypes.DEFAULT_TYPE):
        if update.effective_chat is None or update.effective_chat.type not in (Chat.GROUP, Chat.SUPERGROUP):
            await update.message.reply_text("This command can only be used in groups/supergroups.")
            return
        return await func(update, context)
    return wrapper

# ---------- Start ----------
@groups_only
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Bot is active in this group.")

# ---------- Sudo management (Owner + Sudo) ----------
@groups_only
async def addsudo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    sender = update.effective_user.id
    if not await is_owner_or_sudo(sender):
        await update.message.reply_text("❌ Unauthorized")
        return
    if not context.args:
        await update.message.reply_text("Usage: /addsudo <user_id>")
        return
    try:
        target = int(context.args[0])
    except ValueError:
        await update.message.reply_text("Invalid user id.")
        return
    db.add_sudo(target)
    await update.message.reply_text(f"✅ Added sudo: `{target}`", parse_mode=constants.ParseMode.MARKDOWN)

@groups_only
async def rmsudo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    sender = update.effective_user.id
    if not await is_owner_or_sudo(sender):
        await update.message.reply_text("❌ Unauthorized")
        return
    if not context.args:
        await update.message.reply_text("Usage: /rmsudo <user_id>")
        return
    try:
        target = int(context.args[0])
    except ValueError:
        await update.message.reply_text("Invalid user id.")
        return
    db.rm_sudo(target)
    await update.message.reply_text(f"✅ Removed sudo: `{target}`", parse_mode=constants.ParseMode.MARKDOWN)

# ---------- Global admin management (Owner + Sudo) ----------
@groups_only
async def addadmin(update: Update, context: ContextTypes.DEFAULT_TYPE):
    sender = update.effective_user.id
    if not await is_owner_or_sudo(sender):
        await update.message.reply_text("❌ Unauthorized")
        return
    if not context.args:
        await update.message.reply_text("Usage: /addadmin <user_id>")
        return
    try:
        target = int(context.args[0])
    except ValueError:
        await update.message.reply_text("Invalid user id.")
        return
    db.add_global_admin(target)
    await update.message.reply_text(f"✅ Added global admin: `{target}`", parse_mode=constants.ParseMode.MARKDOWN)

@groups_only
async def rmadmin(update: Update, context: ContextTypes.DEFAULT_TYPE):
    sender = update.effective_user.id
    if not await is_owner_or_sudo(sender):
        await update.message.reply_text("❌ Unauthorized")
        return
    if not context.args:
        await update.message.reply_text("Usage: /rmadmin <user_id>")
        return
    try:
        target = int(context.args[0])
    except ValueError:
        await update.message.reply_text("Invalid user id.")
        return
    db.rm_global_admin(target)
    await update.message.reply_text(f"✅ Removed global admin: `{target}`", parse_mode=constants.ParseMode.MARKDOWN)

# ---------- Allstaff ----------
@groups_only
async def allstaff(update: Update, context: ContextTypes.DEFAULT_TYPE):
    sender = update.effective_user.id
    if not await is_owner_or_sudo(sender):
        await update.message.reply_text("❌ Unauthorized")
        return

    sudos = db.get_sudos()
    text_lines = [f"👑 Owner: [Owner](tg://user?id={OWNER_ID}) (`{OWNER_ID}`)\n"]
    if sudos:
        text_lines.append("🔧 Sudos:")
        for s in sudos:
            text_lines.append(f"- [User](tg://user?id={s}) (`{s}`)")
    else:
        text_lines.append("No sudos set.")
    await update.message.reply_text("\n".join(text_lines), parse_mode=constants.ParseMode.MARKDOWN)

# ---------- Directory (/directory available to Owner/Sudo and group admins) ----------
@groups_only
async def directory(update: Update, context: ContextTypes.DEFAULT_TYPE):
    sender = update.effective_user.id
    chat = update.effective_chat

    allowed = False
    if await is_owner_or_sudo(sender):
        allowed = True
    else:
        # group admins allowed (group context guaranteed by decorator)
        if await is_group_admin(context, chat.id, sender):
            allowed = True

    if not allowed:
        await update.message.reply_text("❌ You don't have permission to view the directory.")
        return

    rows = db.get_directory()
    if not rows:
        await update.message.reply_text("Directory is empty.")
        return

    lines = []
    for r in rows:
        title = r["title"] or str(r["chat_id"])
        link = r["link"]
        cid = r["chat_id"]
        ctype = r["chat_type"]
        lines.append(f"- [{title}]({link}) — `{cid}` ({ctype})")

    await update.message.reply_text("\n".join(lines), parse_mode=constants.ParseMode.MARKDOWN)

@groups_only
async def addgroup(update: Update, context: ContextTypes.DEFAULT_TYPE):
    sender = update.effective_user.id
    if not await is_owner_or_sudo(sender):
        await update.message.reply_text("❌ Unauthorized")
        return
    if len(context.args) < 2:
        await update.message.reply_text("Usage: /addgroup <group-id> <group-link>")
        return
    try:
        cid = int(context.args[0])
    except ValueError:
        await update.message.reply_text("Invalid chat id.")
        return
    link = context.args[1]
    # try to fetch title if bot is in that chat
    title = ""
    try:
        chat = await context.bot.get_chat(cid)
        title = getattr(chat, "title", "")
    except Exception:
        title = ""
    db.add_directory(cid, "group", link, title)
    await update.message.reply_text(f"✅ Added group `{cid}` to directory.")

@groups_only
async def rmgroup(update: Update, context: ContextTypes.DEFAULT_TYPE):
    sender = update.effective_user.id
    if not await is_owner_or_sudo(sender):
        await update.message.reply_text("❌ Unauthorized")
        return
    if not context.args:
        await update.message.reply_text("Usage: /rmgroup <group-id>")
        return
    try:
        cid = int(context.args[0])
    except ValueError:
        await update.message.reply_text("Invalid chat id.")
        return
    db.rm_directory(cid)
    await update.message.reply_text(f"🗑 Removed `{cid}` from directory.")

@groups_only
async def addchannel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    sender = update.effective_user.id
    if not await is_owner_or_sudo(sender):
        await update.message.reply_text("❌ Unauthorized")
        return
    if len(context.args) < 2:
        await update.message.reply_text("Usage: /addchannel <channel-id> <channel-link>")
        return
    try:
        cid = int(context.args[0])
    except ValueError:
        await update.message.reply_text("Invalid chat id.")
        return
    link = context.args[1]
    title = ""
    try:
        chat = await context.bot.get_chat(cid)
        title = getattr(chat, "title", "")
    except Exception:
        title = ""
    db.add_directory(cid, "channel", link, title)
    await update.message.reply_text(f"✅ Added channel `{cid}` to directory.")

@groups_only
async def rmchannel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    sender = update.effective_user.id
    if not await is_owner_or_sudo(sender):
        await update.message.reply_text("❌ Unauthorized")
        return
    if not context.args:
        await update.message.reply_text("Usage: /rmchannel <channel-id>")
        return
    try:
        cid = int(context.args[0])
    except ValueError:
        await update.message.reply_text("Invalid chat id.")
        return
    db.rm_directory(cid)
    await update.message.reply_text(f"🗑 Removed channel `{cid}` from directory.")

# ---------- nban / unban (Owner + Sudo) ----------
@groups_only
async def nban(update: Update, context: ContextTypes.DEFAULT_TYPE):
    sender = update.effective_user.id
    if not await is_owner_or_sudo(sender):
        await update.message.reply_text("❌ Unauthorized")
        return
    if not context.args:
        await update.message.reply_text("Usage: /nban <user_id>")
        return
    try:
        target = int(context.args[0])
    except ValueError:
        await update.message.reply_text("Invalid user id.")
        return

    rows = db.get_directory()
    if not rows:
        await update.message.reply_text("Directory empty. Nothing to ban from.")
        return

    db.add_global_ban(target, reason="nban")
    success = fail = 0
    for r in rows:
        try:
            await context.bot.ban_chat_member(r["chat_id"], target)
            success += 1
        except Exception as e:
            log.warning("Failed to ban %s in %s: %s", target, r["chat_id"], e)
            fail += 1

    await update.message.reply_text(f"✅ Global ban attempted. Success: {success}, Failed: {fail}")

@groups_only
async def unban(update: Update, context: ContextTypes.DEFAULT_TYPE):
    sender = update.effective_user.id
    if not await is_owner_or_sudo(sender):
        await update.message.reply_text("❌ Unauthorized")
        return
    if not context.args:
        await update.message.reply_text("Usage: /unban <user_id>")
        return
    try:
        target = int(context.args[0])
    except ValueError:
        await update.message.reply_text("Invalid user id.")
        return

    rows = db.get_directory()
    if not rows:
        await update.message.reply_text("Directory empty. Nothing to unban in.")
        return

    db.rm_global_ban(target)
    success = fail = 0
    for r in rows:
        try:
            await context.bot.unban_chat_member(r["chat_id"], target)
            success += 1
        except Exception as e:
            log.warning("Failed to unban %s in %s: %s", target, r["chat_id"], e)
            fail += 1

    await update.message.reply_text(f"✅ Global unban attempted. Success: {success}, Failed: {fail}")

# ---------- ginfo (Owner + Sudo only) ----------
@groups_only
async def ginfo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    sender = update.effective_user.id
    if not await is_owner_or_sudo(sender):
        await update.message.reply_text("❌ Unauthorized")
        return

    # accept chat_id argument or run inside the target group
    if context.args:
        try:
            target_chat = int(context.args[0])
        except ValueError:
            await update.message.reply_text("Usage: /ginfo <chat_id>")
            return
    else:
        # in group: use current chat
        target_chat = update.effective_chat.id

    try:
        chat = await context.bot.get_chat(target_chat)
        try:
            members = await context.bot.get_chat_members_count(target_chat)
        except Exception:
            members = "unknown"

        title = getattr(chat, "title", getattr(chat, "first_name", "N/A"))
        text = (
            f"**Group Info**\n\n"
            f"Title: `{title}`\n"
            f"Chat ID: `{target_chat}`\n"
            f"Type: `{chat.type}`\n"
            f"Members: `{members}`\n"
        )
        if getattr(chat, "username", None):
            text += f"Username: @{chat.username}\n"

        await update.message.reply_text(text, parse_mode=constants.ParseMode.MARKDOWN)
    except Exception as e:
        log.exception(e)
        await update.message.reply_text("Failed to fetch chat info. Ensure bot is in that chat or ID is valid.")

# ---------- Setup & run ----------
def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    # basic
    app.add_handler(CommandHandler("start", start))

    # staff
    app.add_handler(CommandHandler("addsudo", addsudo))
    app.add_handler(CommandHandler("rmsudo", rmsudo))
    app.add_handler(CommandHandler("addadmin", addadmin))
    app.add_handler(CommandHandler("rmadmin", rmadmin))
    app.add_handler(CommandHandler("allstaff", allstaff))

    # directory
    app.add_handler(CommandHandler("directory", directory))
    app.add_handler(CommandHandler("addgroup", addgroup))
    app.add_handler(CommandHandler("rmgroup", rmgroup))
    app.add_handler(CommandHandler("addchannel", addchannel))
    app.add_handler(CommandHandler("rmchannel", rmchannel))

    # bans
    app.add_handler(CommandHandler("nban", nban))
    app.add_handler(CommandHandler("unban", unban))

    # ginfo
    app.add_handler(CommandHandler("ginfo", ginfo))

    print("Starting bot (groups-only mode)...")
    app.run_polling()

if __name__ == "__main__":
    main()
