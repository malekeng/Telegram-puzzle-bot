import os
import json
import random
import sqlite3
from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, ContextTypes, filters

# توكن البوت
TOKEN = "7753856798:AAGefhZp4P8NK8FftW5fXsCR2mlYGKM48mg"

# قاعدة البيانات
conn = sqlite3.connect("players.db", check_same_thread=False)
cur = conn.cursor()
cur.execute('''
CREATE TABLE IF NOT EXISTS players (
    user_id INTEGER PRIMARY KEY,
    username TEXT,
    score INTEGER
)
''')
conn.commit()

# تحميل الفوازير
with open("questions.json", "r", encoding="utf-8") as f:
    puzzles = json.load(f)

# /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    cur.execute("INSERT OR IGNORE INTO players (user_id, username, score) VALUES (?, ?, ?)",
                (user.id, user.username, 0))
    conn.commit()

    buttons = [["فزورة عشوائية"], ["رصيدي"], ["/تصنيف"], ["/مساعدة"]]
    await update.message.reply_text(
        "أهلا فيك ببوت 'عصف ذهني'! اختر من القائمة:",
        reply_markup=ReplyKeyboardMarkup(buttons, resize_keyboard=True)
    )

# فزورة عشوائية
async def random_puzzle(update: Update, context: ContextTypes.DEFAULT_TYPE):
    puzzle = random.choice(puzzles)
    context.user_data["current_puzzle"] = puzzle
    await update.message.reply_text(f"فزورتك:\n{puzzle['question']}\nاكتب إجابتك:")

# استقبال الإجابة
async def handle_answer(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip()
    user = update.effective_user

    if "current_puzzle" in context.user_data:
        correct_answer = context.user_data["current_puzzle"]["answer"]
        if text == correct_answer:
            cur.execute("UPDATE players SET score = score + 10 WHERE user_id = ?", (user.id,))
            conn.commit()
            await update.message.reply_text("صح عليك! +10 نقاط")
            del context.user_data["current_puzzle"]
        else:
            await update.message.reply_text("لسه بدها تفكير… جرب كمان!")
    elif text == "فزورة عشوائية":
        await random_puzzle(update, context)
    elif text == "رصيدي":
        cur.execute("SELECT score FROM players WHERE user_id = ?", (user.id,))
        points = cur.fetchone()
        score = points[0] if points else 0
        await update.message.reply_text(f"رصيدك: {score} نقطة")
    else:
        await update.message.reply_text("اكتب إجابتك أو اختر من الأزرار.")

# /تصنيف
async def leaderboard(update: Update, context: ContextTypes.DEFAULT_TYPE):
    cur.execute("SELECT username, score FROM players ORDER BY score DESC LIMIT 5")
    top_players = cur.fetchall()

    if top_players:
        message = "أفضل اللاعبين:\n\n"
        for i, player in enumerate(top_players, start=1):
            message += f"{i}. @{player[0] or 'بدون اسم'} — {player[1]} نقطة\n"
    else:
        message = "لسه ما في لاعبين."

    await update.message.reply_text(message)

# /مساعدة
async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "أوامر البوت:\n"
        "/start — ابدأ اللعب\n"
        "/تصنيف — أفضل اللاعبين\n"
        "/مساعدة — المساعدة\n"
        "واستخدم الأزرار عشان تطلب فزورة أو تشوف رصيدك"
    )

# إعداد التطبيق
app = ApplicationBuilder().token(TOKEN).build()
app.add_handler(CommandHandler("start", start))
app.add_handler(CommandHandler("تصنيف", leaderboard))
app.add_handler(CommandHandler("مساعدة", help_command))
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_answer))

# تشغيل البوت
app.run_polling()
