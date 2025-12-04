import logging
import asyncio
from telegram import Update, Chat, ChatMember
from telegram.constants import ParseMode
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    ContextTypes,
)

from config import BOT_TOKEN, OWNER_ID
import database as db

logging.basicConfig(level=logging.INFO)
log = logging.getLogger(__name__)

# Initialize DB
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
    await update.message.reply_text(f"Added sudo: `{target}`", parse_mode=ParseMode.MARKDOWN)

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
    await update.message.reply_text(f"Removed sudo: `{target}`", parse_mode=ParseMode.MARKDOWN)

# ---------------------------------------------------
# ADMIN ROLES
# ---------------------------------------------------
@groups_only
async def addadmin(update, context):
    uid = update.effective_user.id
    if not await is_owner_or_sudo(uid):
        return await update.message.reply_text("❌ Unauthorized.")
    if not context.args:
        return await update.message.reply_text("Usage: /addadmin <id>")

    target = int(context.args[0])
    db.add_global_admin(target)
    await update.message.reply_text(f"Added global admin `{target}`", parse_mode=ParseMode.MARKDOWN)

@groups_only
async def rmadmin(update, context):
    uid = update.effective_user.id
    if not await is_owner_or_sudo(uid):
        return await update.message.reply_text("❌ Unauthorized.")
    if not context.args:
        return await update.message.reply_text("Usage: /rmadmin <id>")

    target = int(context.args[0])
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
# DIRECTORY — HYPERLINKED GROUP/CHANNEL TITLES ONLY
# ---------------------------------------------------
@groups_only
async def directory(update, context):
    uid = update.effective_user.id
    chat = update.effective_chat

    if not (await is_owner_or_sudo(uid) or await is_group_admin(context.bot, chat.id, uid)):
        return await update.message.reply_text("❌ No permission.")

    rows = db.get_directory()
    if not rows:
        return await update.message.reply_text("📭 Directory empty.")

    lines = [f"• [{r['title']}]({r['link']})" for r in rows]

    await update.message.reply_text("\n".join(lines), parse_mode=ParseMode.MARKDOWN)

# ---------------------------------------------------
# ADD GROUP / CHANNEL
# ---------------------------------------------------
@groups_only
async def addgroup(update, context):
    uid = update.effective_user.id
    if not await is_owner_or_sudo(uid):
        return await update.message.reply_text("❌ Unauthorized.")
    if len(context.args) < 2:
        return await update.message.reply_text("Usage: /addgroup <group-id> <invite-link>")

    cid = int(context.args[0])
    link = context.args[1]

    try:
        bot_member = await context.bot.get_chat_member(cid, context.bot.id)
        if bot_member.status not in ("administrator", "creator"):
            return await update.message.reply_text("❌ Bot must be admin in that group.")
    except:
        return await update.message.reply_text("❌ Bot not in group.")

    chat = await context.bot.get_chat(cid)
    title = chat.title or "Unnamed Group"

    db.add_directory(cid, "group", link, title)
    await update.message.reply_text(f"Added **{title}** to directory.")

@groups_only
async def addchannel(update, context):
    uid = update.effective_user.id
    if not await is_owner_or_sudo(uid):
        return await update.message.reply_text("❌ Unauthorized.")
    if len(context.args) < 2:
        return await update.message.reply_text("Usage: /addchannel <channel-id> <invite-link>")

    cid = int(context.args[0])
    link = context.args[1]

    try:
        bot_member = await context.bot.get_chat_member(cid, context.bot.id)
        if bot_member.status not in ("administrator", "creator"):
            return await update.message.reply_text("❌ Bot must be admin in that channel.")
    except:
        return await update.message.reply_text("❌ Bot cannot access channel.")

    chat = await context.bot.get_chat(cid)
    title = chat.title or "Unnamed Channel"

    db.add_directory(cid, "channel", link, title)
    await update.message.reply_text(f"Added **{title}** to directory.")

# ---------------------------------------------------
# REMOVE DIRECTORY
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
# GLOBAL BAN / UNBAN
# ---------------------------------------------------
@groups_only
async def nban(update, context):
    uid = update.effective_user.id
    if not await is_owner_or_sudo(uid):
        return await update.message.reply_text("❌ Unauthorized.")

    target = int(context.args[0])
    rows = db.get_directory()
    db.add_global_ban(target)

    ok = fail = 0
    for r in rows:
        try:
            await context.bot.ban_chat_member(r['chat_id'], target)
            ok += 1
        except:
            fail += 1

    await update.message.reply_text(f"Global Ban → OK: {ok}, Failed: {fail}")

@groups_only
async def unban(update, context):
    uid = update.effective_user.id
    if not await is_owner_or_sudo(uid):
        return await update.message.reply_text("❌ Unauthorized.")

    target = int(context.args[0])
    rows = db.get_directory()
    db.rm_global_ban(target)

    ok = fail = 0
    for r in rows:
        try:
            await context.bot.unban_chat_member(r['chat_id'], target)
            ok += 1
        except:
            fail += 1

    await update.message.reply_text(f"Global Unban → OK: {ok}, Failed: {fail}")

# ---------------------------------------------------
# PROMOTE ADMINS WITH TITLES
# ---------------------------------------------------
@groups_only
async def promote(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    chat = update.effective_chat

    if not (await is_owner_or_sudo(uid) or await is_group_admin(context.bot, chat.id, uid)):
        return await update.message.reply_text("❌ No permission.")

    if not context.args:
        return await update.message.reply_text("Usage: /promote <title> (reply/user(s))")

    title = context.args[0]
    targets = []

    # Reply
    if update.message.reply_to_message:
        targets.append(update.message.reply_to_message.from_user.id)

    # Direct
    for arg in context.args[1:]:
        try:
            if arg.startswith("@"):
                data = await context.bot.get_chat_member(chat.id, arg)
                targets.append(data.user.id)
            else:
                targets.append(int(arg))
        except:
            pass

    if not targets:
        return await update.message.reply_text("❌ No valid users found.")

    promoted = 0
    failed = 0

    for uid in targets:
        try:
            await context.bot.promote_chat_member(
                chat.id,
                uid,
                can_change_info=True,
                can_delete_messages=True,
                can_invite_users=True,
                can_manage_chat=True,
                can_manage_topics=True,
                can_manage_video_chats=True
            )
            db.save_admin_title(chat.id, uid, title)
            promoted += 1
        except:
            failed += 1

    await update.message.reply_text(
        f"👑 Promotion Results:\nPromoted: `{promoted}`\nFailed: `{failed}`",
        parse_mode=ParseMode.MARKDOWN
    )

# ---------------------------------------------------
# AUTO CACHE ADMINS (via JobQueue)
# ---------------------------------------------------
async def auto_cache(context: ContextTypes.DEFAULT_TYPE):
    rows = db.get_directory()
    for r in rows:
        try:
            admins = await context.bot.get_chat_administrators(r['chat_id'])
            admin_ids = [a.user.id for a in admins]
            db.cache_admins(r['chat_id'], admin_ids)
        except:
            pass

@groups_only
async def cache(update, context):
    uid = update.effective_user.id
    if not await is_owner_or_sudo(uid):
        return await update.message.reply_text("❌ Unauthorized.")

    rows = db.get_directory()
    done = 0

    for r in rows:
        try:
            admins = await context.bot.get_chat_administrators(r['chat_id'])
            admin_ids = [a.user.id for a in admins]
            db.cache_admins(r['chat_id'], admin_ids)
            done += 1
        except:
            pass

    await update.message.reply_text(f"🔄 Cached `{done}` groups.")

# ---------------------------------------------------
# GROUP INFO
# ---------------------------------------------------
@groups_only
async def ginfo(update, context):
    uid = update.effective_user.id
    if not await is_owner_or_sudo(uid):
        return await update.message.reply_text("❌ Owner/Sudo only.")

    chat_id = int(context.args[0]) if context.args else update.effective_chat.id

    try:
        chat = await context.bot.get_chat(chat_id)
        members = await context.bot.get_chat_member_count(chat_id)

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

    # Commands
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
    app.add_handler(CommandHandler("promote", promote))
    app.add_handler(CommandHandler("cache", cache))
    app.add_handler(CommandHandler("ginfo", ginfo))

    # Auto-cache every 30 sec
    app.job_queue.run_repeating(auto_cache, interval=30, first=5)

    print("Bot running...")
    app.run_polling()

if __name__ == "__main__":
    main()
