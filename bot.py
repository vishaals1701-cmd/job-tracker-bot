from telegram import Update
from telegram.ext import ApplicationBuilder, MessageHandler, filters, ContextTypes
import mysql.connector
import os

# DB CONNECTION
def get_connection():
    return mysql.connector.connect(
        host=os.getenv("MYSQLHOST"),
        user=os.getenv("MYSQLUSER"),
        password=os.getenv("MYSQLPASSWORD"),
        database=os.getenv("MYSQLDATABASE"),
        port=int(os.getenv("MYSQLPORT"))
    )

# PARSE MESSAGE
def parse_message(text):
    data = {}
    for line in text.split("\n"):
        if ":" in line:
            key, value = line.split(":", 1)
            data[key.strip().lower()] = value.strip()
    return data

# MAIN HANDLER
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

        if not all([source, company, role, date, status]):
            await update.message.reply_text("❌ Invalid format. Please follow correct format.")
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

# START BOT
def main():
    app = ApplicationBuilder().token(os.getenv("BOT_TOKEN")).build()

    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    print("Bot started...")
    app.run_polling()

if __name__ == "__main__":
    main()