from telegram import Update
from telegram.ext import ApplicationBuilder, MessageHandler, CommandHandler, filters, ContextTypes
import mysql.connector
import os

VALID_STATUS = ["applied", "in progress", "rejected", "selected"]

# -------- DB CONNECTION --------
def get_connection():
    return mysql.connector.connect(
        host=os.getenv("MYSQLHOST"),
        user=os.getenv("MYSQLUSER"),
        password=os.getenv("MYSQLPASSWORD"),
        database=os.getenv("MYSQLDATABASE"),
        port=os.getenv("MYSQLPORT")
    )

# -------- PARSE --------
def parse_message(text):
    data = {}
    for line in text.split("\n"):
        if "Source:" in line:
            data["source"] = line.split(":")[1].strip()
        elif "Company:" in line:
            data["company"] = line.split(":")[1].strip()
        elif "Role:" in line:
            data["role"] = line.split(":")[1].strip()
        elif "Date:" in line:
            data["applied_date"] = line.split(":")[1].strip()
        elif "Status:" in line:
            data["status"] = line.split(":")[1].strip().lower()
    return data

# -------- ADD --------
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.message.from_user.username or "unknown"
    data = parse_message(update.message.text)

    conn = get_connection()
    cursor = conn.cursor()

    query = """
    INSERT INTO jobs (user, source, company, role, applied_date, status)
    VALUES (%s, %s, %s, %s, %s, %s)
    """

    cursor.execute(query, (
        user,
        data.get("source"),
        data.get("company"),
        data.get("role"),
        data.get("applied_date"),
        data.get("status")
    ))

    conn.commit()
    cursor.close()
    conn.close()

    await update.message.reply_text("✅ Job saved")

# -------- VIEW --------
async def view_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM jobs")
    rows = cursor.fetchall()

    msg = "📋 JOB LIST\n\n"
    for r in rows:
        msg += f"{r[0]} | {r[3]} | {r[6]}\n"

    cursor.close()
    conn.close()

    await update.message.reply_text(msg)

# -------- UPDATE --------
async def update_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    job_id = int(context.args[0])
    status = " ".join(context.args[1:]).lower()

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("UPDATE jobs SET status=%s WHERE id=%s", (status, job_id))
    conn.commit()

    cursor.close()
    conn.close()

    await update.message.reply_text("🔄 Updated")

# -------- DELETE --------
async def delete_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    job_id = int(context.args[0])

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("DELETE FROM jobs WHERE id=%s", (job_id,))
    conn.commit()

    cursor.close()
    conn.close()

    await update.message.reply_text("🗑 Deleted")

# -------- SUMMARY --------
async def summary_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT COUNT(*) FROM jobs")
    total = cursor.fetchone()[0]

    msg = f"📊 JOB SUMMARY\n\nTotal Applied: {total}"

    cursor.close()
    conn.close()

    await update.message.reply_text(msg)

# -------- MAIN --------
app = ApplicationBuilder().token(os.getenv("BOT_TOKEN")).build()

app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
app.add_handler(CommandHandler("view", view_cmd))
app.add_handler(CommandHandler("update", update_cmd))
app.add_handler(CommandHandler("delete", delete_cmd))
app.add_handler(CommandHandler("summary", summary_cmd))

print("🚀 Bot running...")
app.run_polling()