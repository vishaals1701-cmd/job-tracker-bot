from telegram import Update
from telegram.ext import (
    ApplicationBuilder,
    MessageHandler,
    CommandHandler,
    filters,
    ContextTypes
)
import mysql.connector
import os

# ================= DB CONNECTION =================
def get_connection():
    return mysql.connector.connect(
        host=os.getenv("MYSQLHOST"),
        user=os.getenv("MYSQLUSER"),
        password=os.getenv("MYSQLPASSWORD"),
        database=os.getenv("MYSQLDATABASE"),
        port=int(os.getenv("MYSQLPORT"))
    )

# ================= PARSE MESSAGE =================
def parse_message(text):
    data = {}
    for line in text.split("\n"):
        if ":" in line:
            key, value = line.split(":", 1)
            data[key.strip().lower()] = value.strip()
    return data

# ================= SAVE DATA =================
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        text = update.message.text
        user = update.message.from_user.username or "unknown"

        data = parse_message(text)

        source = data.get("source")
        company = data.get("company")
        role = data.get("role")
        date = data.get("date")
        status = data.get("status")

        # Validation
        if not all([source, company, role, date, status]):
            await update.message.reply_text(
                "❌ Invalid format\n\nUse:\nSource:\nCompany:\nRole:\nDate:\nStatus:"
            )
            return

        conn = get_connection()
        cursor = conn.cursor()

        query = """
        INSERT INTO jobs (user, source, company, role, applied_date, status)
        VALUES (%s, %s, %s, %s, %s, %s)
        """

        cursor.execute(query, (user, source, company, role, date, status))
        conn.commit()

        cursor.close()
        conn.close()

        await update.message.reply_text("✅ Data saved successfully!")

    except Exception as e:
        print("ERROR:", e)
        await update.message.reply_text("❌ Error occurred")

# ================= VIEW COMMAND =================
async def view_jobs(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        conn = get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT source, company, role, applied_date, status 
            FROM jobs 
            ORDER BY id DESC 
            LIMIT 5
        """)

        rows = cursor.fetchall()

        if not rows:
            await update.message.reply_text("📭 No data found")
            return

        msg = "📌 Last 5 Applications:\n"
        for row in rows:
            msg += f"\n{row[0]} | {row[1]} | {row[2]} | {row[3]} | {row[4]}"

        await update.message.reply_text(msg)

        cursor.close()
        conn.close()

    except Exception as e:
        print("VIEW ERROR:", e)
        await update.message.reply_text("❌ Error fetching data")

# ================= SUMMARY COMMAND =================
async def summary(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        conn = get_connection()
        cursor = conn.cursor()

        cursor.execute("SELECT status, COUNT(*) FROM jobs GROUP BY status")
        rows = cursor.fetchall()

        if not rows:
            await update.message.reply_text("📭 No data available")
            return

        msg = "📊 Application Summary:\n"
        for row in rows:
            msg += f"{row[0]}: {row[1]}\n"

        await update.message.reply_text(msg)

        cursor.close()
        conn.close()

    except Exception as e:
        print("SUMMARY ERROR:", e)
        await update.message.reply_text("❌ Error fetching summary")

# ================= START BOT =================
def main():
    app = ApplicationBuilder().token(os.getenv("BOT_TOKEN")).build()

    # Handlers
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    app.add_handler(CommandHandler("view", view_jobs))
    app.add_handler(CommandHandler("summary", summary))

    print("🚀 Bot started...")
    app.run_polling()

# ================= RUN =================
if __name__ == "__main__":
    main()