from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes
import mysql.connector
import os

# ---------------- VALID STATUS ----------------
VALID_STATUS = ["applied", "in progress", "rejected", "selected"]

# ---------------- DB CONNECTION ----------------
def get_connection():
    return mysql.connector.connect(
        host=os.getenv("MYSQLHOST"),
        user=os.getenv("MYSQLUSER"),
        password=os.getenv("MYSQLPASSWORD"),
        database=os.getenv("MYSQLDATABASE"),
        port=int(os.getenv("MYSQLPORT"))
    )

# ---------------- CREATE TABLE ----------------
def create_table():
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS jobs (
        id INT AUTO_INCREMENT PRIMARY KEY,
        user VARCHAR(50),
        source VARCHAR(50),
        company VARCHAR(100),
        role VARCHAR(100),
        applied_date VARCHAR(20),
        status VARCHAR(50)
    )
    """)

    conn.commit()
    conn.close()

# ---------------- START ----------------
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Bot is running...")

# ---------------- PARSE MESSAGE ----------------
def parse_message(text):
    data = {}
    for line in text.split("\n"):
        if ":" in line:
            key, value = line.split(":", 1)
            data[key.strip().lower()] = value.strip()
    return data

# ---------------- ADD JOB ----------------
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    user = update.message.from_user.username

    data = parse_message(text)

    try:
        source = data["source"]
        company = data["company"]
        role = data["role"]
        date = data["date"]
        status = data["status"].lower()

        if status not in VALID_STATUS:
            await update.message.reply_text("Invalid status!")
            return

        conn = get_connection()
        cursor = conn.cursor()

        cursor.execute("""
        INSERT INTO jobs (user, source, company, role, applied_date, status)
        VALUES (%s, %s, %s, %s, %s, %s)
        """, (user, source, company, role, date, status))

        conn.commit()

        job_id = cursor.lastrowid

        conn.close()

        await update.message.reply_text(f"Job saved (ID: {job_id})")

    except Exception as e:
        await update.message.reply_text("Invalid format!")

# ---------------- VIEW ----------------
async def view(update: Update, context: ContextTypes.DEFAULT_TYPE):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT id, company, status FROM jobs")
    rows = cursor.fetchall()

    conn.close()

    if not rows:
        await update.message.reply_text("No data found")
        return

    msg = "JOB LIST\n\n"

    for r in rows:
        msg += f"{r[0]} | {r[1]} | {r[2]}\n"

    await update.message.reply_text(msg)

# ---------------- SUMMARY ----------------
async def summary(update: Update, context: ContextTypes.DEFAULT_TYPE):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT source, status FROM jobs")
    rows = cursor.fetchall()

    conn.close()

    total = len(rows)
    sla = sum(1 for r in rows if r[0].lower() == "sla")
    off = sum(1 for r in rows if r[0].lower() == "off-campus")

    selected = sum(1 for r in rows if r[1].lower() == "selected")
    inprogress = sum(1 for r in rows if r[1].lower() == "in progress")
    rejected = sum(1 for r in rows if r[1].lower() == "rejected")

    msg = f"""
JOB SUMMARY

Total Applied: {total}

SLA Applied: {sla}
Off-Campus Applied: {off}

Selected: {selected}
In Progress: {inprogress}
Rejected: {rejected}
"""

    await update.message.reply_text(msg)

# ---------------- MAIN ----------------
if __name__ == "__main__":
    create_table()

    app = ApplicationBuilder().token(os.getenv("BOT_TOKEN")).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("view", view))
    app.add_handler(CommandHandler("summary", summary))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    print("Bot started...")

    app.run_polling(close_loop=False)

