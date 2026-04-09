import os
import mysql.connector
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes

# DB CONNECTION
def get_db():
    return mysql.connector.connect(
        host=os.getenv("MYSQLHOST"),
        user=os.getenv("MYSQLUSER"),
        password=os.getenv("MYSQLPASSWORD"),
        database=os.getenv("MYSQL_DATABASE"),
        port=int(os.getenv("MYSQLPORT"))
    )

# START COMMAND
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("✅ Send job details:\n\nSource: SLA\nCompany: TCS\nRole: Data Analyst\nDate: 2026-04-10\nStatus: applied")

# SAVE DATA
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        text = update.message.text
        user = update.message.from_user.username or "unknown"

        lines = text.split("\n")
        data = {}

        for line in lines:
            key, value = line.split(":", 1)
            data[key.strip().lower()] = value.strip()

        source = data.get("source")
        company = data.get("company")
        role = data.get("role")
        date = data.get("date")
        status = data.get("status")

        conn = get_db()
        cursor = conn.cursor()

        cursor.execute("""
        INSERT INTO jobs (user, source, company, role, applied_date, status)
        VALUES (%s, %s, %s, %s, %s, %s)
        """, (user, source, company, role, date, status))

        conn.commit()
        conn.close()

        await update.message.reply_text("✅ Data saved successfully!")

    except Exception as e:
        await update.message.reply_text(f"❌ Error: {str(e)}")

# VIEW LAST 5
async def view(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        conn = get_db()
        cursor = conn.cursor()

        cursor.execute("SELECT * FROM jobs ORDER BY id DESC LIMIT 5")
        rows = cursor.fetchall()

        msg = "📌 Last Applications:\n\n"

        for row in rows:
            msg += f"{row[2]} | {row[3]} | {row[4]} | {row[5]} | {row[6]}\n"

        conn.close()

        await update.message.reply_text(msg)

    except Exception as e:
        await update.message.reply_text(f"❌ Error: {str(e)}")

# SUMMARY
async def summary(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        conn = get_db()
        cursor = conn.cursor()

        cursor.execute("SELECT COUNT(*) FROM jobs")
        total = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(*) FROM jobs WHERE source='SLA'")
        sla = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(*) FROM jobs WHERE source='Off-Campus'")
        off = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(*) FROM jobs WHERE source='SLA' AND status='in process'")
        sla_in = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(*) FROM jobs WHERE source='Off-Campus' AND status='in process'")
        off_in = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(*) FROM jobs WHERE source='SLA' AND status='rejected'")
        sla_rej = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(*) FROM jobs WHERE source='Off-Campus' AND status='rejected'")
        off_rej = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(*) FROM jobs WHERE status='selected'")
        selected = cursor.fetchone()[0]

        conn.close()

        msg = f"""
📊 Summary Report

📌 Total Applied: {total}

📂 Source:
• SLA: {sla}
• Off-Campus: {off}

⏳ In Process:
• SLA: {sla_in}
• Off-Campus: {off_in}

❌ Rejected:
• SLA: {sla_rej}
• Off-Campus: {off_rej}

✅ Selected: {selected}
"""

        await update.message.reply_text(msg)

    except Exception as e:
        await update.message.reply_text(f"❌ Error: {str(e)}")

# MAIN
if __name__ == "__main__":
    app = ApplicationBuilder().token(os.getenv("BOT_TOKEN")).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("view", view))
    app.add_handler(CommandHandler("summary", summary))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    print("Bot running...")
    app.run_polling()