import json
import os
import threading
from flask import Flask
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    CallbackQueryHandler,
    ContextTypes
)

# ========= SOZLAMALAR =========
TOKEN = os.environ.get("BOT_TOKEN")  # Render Environment'dan olinadi

CHANNELS = ["@Din_koreakosmetika", "@D_lingu"]
PRIVATE_CHANNEL_ID = -1003512316765   # yopiq kanal ID
ADMINS = [123456789]                 # o'zingizning telegram ID
REQUIRED = 8

DATA_FILE = "data.json"

# ========= DATA =========
def load():
    try:
        with open(DATA_FILE, "r") as f:
            return json.load(f)
    except:
        return {"users": {}, "used": []}

def save(d):
    with open(DATA_FILE, "w") as f:
        json.dump(d, f)

data = load()

TEXT = (
    "Online til markazimizga xush kelibsiz 😍\n\n"
    "Men sizga:\n"
    "🇬🇧 Ingliz tili\n"
    "🇰🇷 Koreys tili\n"
    "🇸🇦 Arab tilini\n"
    "oddiy va tushunarli usulda o‘rgataman.\n\n"
    "👇 Arab tilidan TEKIN kurs\n"
    "🎯 8 ta odam olib keling va sovg‘ani oling!\n\n"
)

# ========= KANAL TEKSHIRISH =========
async def is_subscribed(bot, uid):
    for ch in CHANNELS:
        m = await bot.get_chat_member(ch, uid)
        if m.status in ["left", "kicked"]:
            return False
    return True

# ========= /start =========
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = str(update.effective_user.id)

    if uid not in data["users"]:
        data["users"][uid] = {"count": 0, "reward": False}

        if context.args:
            ref = context.args[0]
            key = f"{ref}>{uid}"
            if ref != uid and ref in data["users"] and key not in data["used"]:
                data["users"][ref]["count"] += 1
                data["used"].append(key)

        save(data)

    keyboard = [
        [InlineKeyboardButton("📢 1-kanal", url="https://t.me/Din_koreakosmetika")],
        [InlineKeyboardButton("📢 2-kanal", url="https://t.me/D_lingu")],
        [InlineKeyboardButton("✅ Tekshirish", callback_data="check")]
    ]

    await update.message.reply_text(
        "👋 Avval barcha kanallarga obuna bo‘ling 👇",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

# ========= TEKSHIRISH =========
async def check(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    uid = str(q.from_user.id)
    bot = context.bot

    if not await is_subscribed(bot, int(uid)):
        await q.message.reply_text("❌ Avval barcha kanallarga obuna bo‘ling.")
        return

    link = f"https://t.me/{bot.username}?start={uid}"
    count = data["users"][uid]["count"]

    await q.message.reply_photo(
        photo=open("promo.jpg", "rb"),
        caption=(
            TEXT +
            f"🔗 Sizning referal linkingiz:\n{link}\n\n"
            f"📊 Natija: {count}/{REQUIRED}"
        )
    )

    if count >= REQUIRED and not data["users"][uid]["reward"]:
        invite = await bot.create_chat_invite_link(
            chat_id=PRIVATE_CHANNEL_ID,
            member_limit=1
        )
        data["users"][uid]["reward"] = True
        save(data)

        await bot.send_message(
            int(uid),
            f"🎉 TABRIKLAYMIZ!\n\n"
            f"🎁 Yopiq kanal (1 martalik link):\n{invite.invite_link}"
        )

# ========= ADMIN =========
async def stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id not in ADMINS:
        return

    txt = "📊 STATISTIKA\n\n"
    for u, d in data["users"].items():
        txt += f"{u} → {d['count']}\n"

    await update.message.reply_text(txt or "Bo‘sh")

async def reset(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id not in ADMINS:
        return

    data["users"] = {}
    data["used"] = []
    save(data)
    await update.message.reply_text("♻️ Hammasi tozalandi")# ========= TELEGRAM APP =========
tg_app = ApplicationBuilder().token(TOKEN).build()
tg_app.add_handler(CommandHandler("start", start))
tg_app.add_handler(CommandHandler("stats", stats))
tg_app.add_handler(CommandHandler("reset", reset))
tg_app.add_handler(CallbackQueryHandler(check))

# ========= FLASK (Render uchun) =========
web = Flask(__name__)
PORT = int(os.environ.get("PORT", 10000))

@web.route("/")
def home():
    return "OK"

def run_bot():
    tg_app.run_polling()

if __name__== "__main__":
    threading.Thread(target=run_bot).start()
    web.run(host="0.0.0.0", port=PORT)
