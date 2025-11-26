import logging
import os
import json
from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    ConversationHandler,
    filters
)

# ------------------ CONFIG ------------------
BOT_TOKEN = "5217317508:AAEBtf71up5-fssiHWOwamZakB7_OveI3Os"
ADMINS = {624102836, 8394010826, 548916625}
DB_FILE = "data/users.json"

# ------------------ LOGGING ------------------
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)

# ------------------ DATABASE ------------------
def load_db():
    if not os.path.exists(DB_FILE):
        return {}
    with open(DB_FILE, "r") as f:
        return json.load(f)

def save_db(db):
    with open(DB_FILE, "w") as f:
        json.dump(db, f, indent=4)

def ensure_user_exists(uid):
    db = load_db()
    uid = str(uid)
    if uid not in db:
        db[uid] = {
            "name": None,
            "nationality": None,
            "personal_channel": None,
            "birthday": None,
            "zodiac": None,
            "chinese_zodiac": None,
            "mbti": None,
            "height": None,

            # Admin-only
            "join_date": None,
            "left_date": None,
            "invited_by": None,
            "inactive_reason": None,
            "banned_reason": None,

            "can_edit_self": True
        }
        save_db(db)

def is_admin(uid):
    return uid in ADMINS

# ------------------ COMMANDS ------------------
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    ensure_user_exists(uid)
    await update.message.reply_text("Welcome! Use /myinfo to view your profile.")

async def myinfo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    ensure_user_exists(uid)
    db = load_db()
    info = db[str(uid)]
    msg = "👤 *Your Profile:*\n"
    for k, v in info.items():
        if k in ["join_date", "left_date", "invited_by", "inactive_reason", "banned_reason"]:
            continue
        msg += f"- *{k.replace('_',' ').title()}*: {v}\n"
    await update.message.reply_markdown(msg)

async def thisuser(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    if not is_admin(uid):
        return await update.message.reply_text("❌ You are not an admin.")
    if not context.args:
        return await update.message.reply_text("Usage: /thisuser <telegram_id>")
    target = context.args[0]
    db = load_db()
    if target not in db:
        return await update.message.reply_text("❌ User not found.")
    info = db[target]
    msg = "📝 *Full User Info:*\n"
    for k, v in info.items():
        msg += f"- *{k.replace('_',' ').title()}*: {v}\n"
    await update.message.reply_markdown(msg)

# ------------------ TEST COMMAND ------------------
async def ping(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Pong!")

# ------------------ UPDATE INFO ------------------
UPDATE_FIELD, UPDATE_VALUE = range(2)

async def updateinfo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    ensure_user_exists(uid)
    db = load_db()
    if not db[str(uid)]["can_edit_self"]:
        return await update.message.reply_text("❌ You cannot edit your own info.")
    await update.message.reply_text(
        "Which field do you want to update?\n"
        "name, nationality, personal_channel, birthday, zodiac, chinese_zodiac, mbti, height"
    )
    return UPDATE_FIELD

async def update_field(update: Update, context: ContextTypes.DEFAULT_TYPE):
    field = update.message.text.lower()
    allowed = [
        "name", "nationality", "personal_channel",
        "birthday", "zodiac", "chinese_zodiac",
        "mbti", "height"
    ]
    if field not in allowed:
        return await update.message.reply_text("❌ Invalid field. Try again.")
    context.user_data["field"] = field
    await update.message.reply_text("Send the new value:")
    return UPDATE_VALUE

async def update_value(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    field = context.user_data["field"]
    new_value = update.message.text
    db = load_db()
    db[str(uid)][field] = new_value
    save_db(db)
    await update.message.reply_text("✔ Updated successfully!")
    return ConversationHandler.END

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("❌ Cancelled.")
    return ConversationHandler.END

# ------------------ MAIN ------------------
def main():
    if not os.path.exists("data"):
        os.mkdir("data")

    app = Application.builder().token(BOT_TOKEN).build()

    update_conv = ConversationHandler(
        entry_points=[CommandHandler("updateinfo", updateinfo)],
        states={
            UPDATE_FIELD: [MessageHandler(filters.TEXT & ~filters.COMMAND, update_field)],
            UPDATE_VALUE: [MessageHandler(filters.TEXT & ~filters.COMMAND, update_value)],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
    )

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("myinfo", myinfo))
    app.add_handler(CommandHandler("thisuser", thisuser))
    app.add_handler(CommandHandler("ping", ping))
    app.add_handler(update_conv)

    print("Bot running…")
    app.run_polling()

if __name__ == "__main__":
    main()
