import os
import random
import json
import sqlite3
from datetime import datetime
from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, ContextTypes, filters

# قاعدة البيانات
conn = sqlite3.connect("bot_users.db", check_same_thread=False)
cur = conn.cursor()

# جداول
cur.execute("CREATE TABLE IF NOT EXISTS users (user_id INTEGER PRIMARY KEY, points INTEGER)")
cur.execute("CREATE TABLE IF NOT EXISTS attempts (id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER, puzzle TEXT, answer TEXT, timestamp TEXT)")
conn.commit()

# تحميل الفوازير من ملف JSON
with open("puzzles.json", "r", encoding="utf-8") as f:
    puzzles = json.load(f)

# فزورة اليوم
today_puzzle = random.choice(puzzles)
today_answer = today_puzzle['answer']

# أوامر البداية
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    cur.execute("INSERT OR IGNORE INTO users (user_id, points) VALUES (?, ?)", (user_id, 0))
    conn.commit()

    buttons = [["فزورة اليوم"], ["رصيدي"], ["لوحة الشرف"], ["استبدل نقاطي"]]
    await update.message.reply_text(
        "أهلا فيك ببوت 'عصف ذهني'! اختر من القائمة:",
        reply_markup=ReplyKeyboardMarkup(buttons, resize_keyboard=True)
    )

# إرسال فزورة اليوم
async def puzzle_today(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(f"فزورة اليوم:\n{today_puzzle['question']}\nاكتب إجابتك:")

# التعامل مع الإجابات
async def handle_answer(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_answer = update.message.text.strip()
    user_id = update.effective_user.id
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    if user_answer == today_answer:
        points = random.choice([5, 10, 15])
        cur.execute("UPDATE users SET points = points + ? WHERE user_id = ?", (points, user_id))
        conn.commit()
        await update.message.reply_text(f"صح عليك! +{points} نقطة")
    elif user_answer == "فزورة اليوم":
        await puzzle_today(update, context)
        return
    elif user_answer == "رصيدي":
        cur.execute("SELECT points FROM users WHERE user_id = ?", (user_id,))
        points = cur.fetchone()[0]
        await update.message.reply_text(f"رصيدك الحالي: {points} نقطة")
        return
    elif user_answer == "لوحة الشرف":
        await leaderboard(update)
        return
    elif user_answer == "استبدل نقاطي":
        await redeem_points(update)
        return
    else:
        await update.message.reply_text("غلط… جرب كمان!")

    # حفظ المحاولة
    cur.execute("INSERT INTO attempts (user_id, puzzle, answer, timestamp) VALUES (?, ?, ?, ?)", (user_id, today_puzzle['question'], user_answer, timestamp))
    conn.commit()

# لوحة الشرف
async def leaderboard(update: Update):
    cur.execute("SELECT user_id, points FROM users ORDER BY points DESC LIMIT 5")
    top_users = cur.fetchall()

    msg = "لوحة الشرف:\n"
    for rank, (user_id, points) in enumerate(top_users, start=1):
        msg += f"{rank}. {user_id}: {points} نقطة\n"
    await update.message.reply_text(msg)

# استبدال النقاط
async def redeem_points(update: Update):
    user_id = update.effective_user.id
    cur.execute("SELECT points FROM users WHERE user_id = ?", (user_id,))
    points = cur.fetchone()[0]

    if points >= 30:
        cur.execute("UPDATE users SET points = points - 30 WHERE user_id = ?", (user_id,))
        conn.commit()
        await update.message.reply_text("تم خصم 30 نقطة… وهديتك: فزورة صعبة جدا! (قريبًا)")
    else:
        await update.message.reply_text("رصيدك مش كافي… بدك تجمع أكتر!")

# إعداد التطبيق
app = ApplicationBuilder().token(os.getenv("TELEGRAM_BOT_TOKEN")).build()
app.add_handler(CommandHandler("start", start))
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_answer))
app.add_handler(CommandHandler("تصنيف", leaderboard))

# تشغيل البوت
app.run_polling()