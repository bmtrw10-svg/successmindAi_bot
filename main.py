import os
import asyncio
from collections import defaultdict
from datetime import datetime, timedelta

from telegram import Update
from telegram.ext import Application, ContextTypes, CommandHandler, MessageHandler, filters
from openai import AsyncOpenAI

# === CONFIG ===
BOT_TOKEN = os.environ.get("BOT_TOKEN")
OPENAI_KEY = os.environ.get("OPENAI_API_KEY")
WEBHOOK_URL = os.environ.get("WEBHOOK_URL")
PORT = int(os.environ.get("PORT", 10000))

client = AsyncOpenAI(api_key=OPENAI_KEY)

# === MEMORY & RATE LIMIT ===
memory = defaultdict(list)
rate = defaultdict(list)

async def ai_reply(update: Update, context: ContextTypes.DEFAULT_TYPE, text: str, chat_id: int):
    user_id = update.effective_user.id

    # Rate limit: 3 messages per 30 seconds
    now = datetime.now()
    rate[user_id] = [t for t in rate[user_id] if now - t < timedelta(seconds=30)]
    if len(rate[user_id]) >= 3:
        await update.message.reply_text("3/30s")
        return
    rate[user_id].append(now)

    # Save user message (keep last 10 total)
    memory[chat_id].append({"role": "user", "content": text})
    if len(memory[chat_id]) > 10:
        memory[chat_id] = memory[chat_id][-10:]

    msg = await update.message.reply_text("Thinking...")

    try:
        # ONE CALL – NO STREAMING – NO CUTOFF
        response = await asyncio.wait_for(
            client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": "Answer fully in 4-7 short bullet points. Never cut off."}
                ] + memory[chat_id][-5:],
                temperature=0.7,
                max_tokens=600
            ),
            timeout=16
        )
        answer = response.choices[0].message.content.strip()

        await asyncio.sleep(0.5)  # tiny delay so Render doesn't kill
        await msg.edit_text(answer or "No reply.")
        memory[chat_id].append({"role": "assistant", "content": answer})

    except Exception:
        await msg.edit_text("AI busy, try again.")

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "*SuccessMind AI*\n\n"
        "• DM: full chat\n"
        "• Group: @me or /ask\n"
        "• Made in Ethiopia",
        parse_mode="Markdown"
    )

async def ask(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if context.args:
        await ai_reply(update, context, " ".join(context.args), update.effective_chat.id)

async def handle(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text or ""
    chat = update.effective_chat

    # DM: any text
    if chat.type == "private" and text.strip():
        await ai_reply(update, context, text, chat.id)
        return

    # Group: only when mentioned
    me = await context.bot.get_me()
    if f"@{me.username}" in text.lower():
        clean = text.replace(f"@{me.username}", "", 1).strip()
        if clean:
            await ai_reply(update, context, clean, chat.id)

# === APP ===
app = Application.builder().token(BOT_TOKEN).build()

app.add_handler(CommandHandler("start", start))
app.add_handler(CommandHandler("ask", ask))
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle))

if __name__ == "__main__":
    app.run_webhook(
        listen="0.0.0.0",
        port=PORT,
        url_path="/webhook",
        webhook_url=WEBHOOK_URL
    )
