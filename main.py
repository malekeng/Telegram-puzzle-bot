import os
import sqlite3
from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, ContextTypes, filters

# قاعدة البيانات
conn = sqlite3.connect("bot_users.db", check_same_thread=False)
cur = conn.cursor()
cur.execute("CREATE TABLE IF NOT EXISTS users (user_id INTEGER PRIMARY KEY, points INTEGER)")
conn.commit()

# فزورة اليوم
puzzle = "شيء ماشي طول الوقت وما إله رجلين، شو هو؟"
answer = "الساعة"

# start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    cur.execute("INSERT OR IGNORE INTO users (user_id, points) VALUES (?, ?)", (user_id, 0))
    conn.commit()
    
    buttons = [["فزورة اليوم"], ["رصيدي"]]
    await update.message.reply_text(
        "أهلا فيك ببوت 'عصف ذهني'! اختر من القائمة:",
        reply_markup=ReplyKeyboardMarkup(buttons, resize_keyboard=True)
    )

# إرسال فزورة
async def puzzle_today(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(f"فزورة اليوم:\n{puzzle}\nاكتب إجابتك:")

# استقبال إجابات
async def handle_answer(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_answer = update.message.text.strip()
    user_id = update.effective_user.id
    
    if user_answer == answer:
        cur.execute("UPDATE users SET points = points + 10 WHERE user_id = ?", (user_id,))
        conn.commit()
        await update.message.reply_text("صح عليك! دماغك شغّال\n+10 نقاط")
    elif user_answer == "فزورة اليوم":
        await puzzle_today(update, context)
    elif user_answer == "رصيدي":
        cur.execute("SELECT points FROM users WHERE user_id = ?", (user_id,))
        points = cur.fetchone()[0]
        await update.message.reply_text(f"رصيدك الحالي: {points} نقطة")
    else:
        await update.message.reply_text("لسه بدها شوية تفكير… جرب كمان!")

# إعداد التطبيق
app = ApplicationBuilder().token(os.getenv("TELEGRAM_BOT_TOKEN")).build()
app.add_handler(CommandHandler("start", start))
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_answer))

# تشغيل البوت
app.run_polling()
