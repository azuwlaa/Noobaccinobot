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
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")

# Admin IDs
ADMINS = {624102836, 8394010826, 548916625}

DB_FILE = "data/users.json"


# ------------------ Database Helpers ------------------

def load_db():
    if not os.path.exists(DB_FILE):
        return {}
    with open(DB_FILE, "r") as f:
        return json.load(f)


def save_db(db):
    with open(DB_FILE, "w") as f:
        json.dump(db, f, indent=4)


def ensure_user_exists(user_id):
    db = load_db()
    uid = str(user_id)

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

            # Admin-only fields
            "join_date": None,
            "left_date": None,
            "invited_by": None,
            "inactive_reason": None,
            "banned_reason": None,

            # User permissions
            "can_edit_self": True,
        }
        save_db(db)


# ------------------ Permissions ------------------

def is_admin(user_id):
    return user_id in ADMINS


# ------------------ Bot Commands ------------------

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    ensure_user_exists(user.id)
    await update.message.reply_text("Welcome! Use /myinfo to view your info.")


async def myinfo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    ensure_user_exists(user.id)
    db = load_db()
    info = db[str(user.id)]

    msg = "👤 *Your Information:*\n"
    for key, value in info.items():
        if key in ["join_date", "left_date", "invited_by", "inactive_reason", "banned_reason"]:
            continue
        msg += f"- *{key.replace('_', ' ').title()}*: {value}\n"

    await update.message.reply_markdown(msg)


async def thisuser(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user

    if not is_admin(user.id):
        return await update.message.reply_text("❌ You are not an admin.")

    if len(context.args) == 0:
        return await update.message.reply_text("Usage: /thisuser <telegram_id>")

    target_id = context.args[0]

    db = load_db()
    if target_id not in db:
        return await update.message.reply_text("❌ User not found.")

    info = db[target_id]

    msg = "📝 *Full User Info (Admin Only)*\n"
    for key, value in info.items():
        msg += f"- *{key.replace('_',' ').title()}*: {value}\n"

    await update.message.reply_markdown(msg)


# ------------ Update Info Conversation ------------

UPDATE_FIELD, UPDATE_VALUE = range(2)


async def updateinfo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    ensure_user_exists(user.id)

    db = load_db()

    if not db[str(user.id)].get("can_edit_self", True):
        return await update.message.reply_text("❌ You cannot edit your profile.")

    await update.message.reply_text(
        "Which field do you want to update?\n"
        "Options: name, nationality, personal_channel, birthday, "
        "zodiac, chinese_zodiac, mbti, height"
    )
    return UPDATE_FIELD


async def update_field(update: Update, context: ContextTypes.DEFAULT_TYPE):
    field = update.message.text.lower()
    allowed = [
        "name",
        "nationality",
        "personal_channel",
        "birthday",
        "zodiac",
        "chinese_zodiac",
        "mbti",
        "height",
    ]

    if field not in allowed:
        return await update.message.reply_text("❌ Invalid field. Try again.")

    context.user_data["field"] = field
    await update.message.reply_text(f"Send the new value for *{field}*:")
    return UPDATE_VALUE


async def update_value(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    new_value = update.message.text
    field = context.user_data["field"]

    db = load_db()
    db[str(user.id)][field] = new_value
    save_db(db)

    await update.message.reply_text("✔ Updated successfully!")
    return ConversationHandler.END


async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("❌ Update cancelled.")
    return ConversationHandler.END


# ------------------ Application (PTB 21+) ------------------

async def main():
    app = Application.builder().token(BOT_TOKEN).build()

    update_conv = ConversationHandler(
        entry_points=[CommandHandler("updateinfo", updateinfo)],
        states={
            UPDATE_FIELD: [MessageHandler(filters.TEXT, update_field)],
            UPDATE_VALUE: [MessageHandler(filters.TEXT, update_value)],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
    )

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("myinfo", myinfo))
    app.add_handler(CommandHandler("thisuser", thisuser))
    app.add_handler(update_conv)

    print("Bot running on PTB 21+ …")
    await app.run_polling()


if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
