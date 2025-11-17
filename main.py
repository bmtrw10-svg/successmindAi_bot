import os
import asyncio
from collections import defaultdict
from datetime import datetime, timedelta

from telegram import Update, BotCommand
from telegram.ext import Application, ContextTypes, MessageHandler, CommandHandler, filters
from telegram.constants import ParseMode
from openai import AsyncOpenAI
from dotenv import load_dotenv

load_dotenv()

# === CONFIG ===
BOT_TOKEN = os.getenv("BOT_TOKEN")
OPENAI_KEY = os.getenv("OPENAI_API_KEY")
WEBHOOK_URL = os.getenv("WEBHOOK_URL")
PORT = int(os.getenv("PORT", 10000))

client = AsyncOpenAI(api_key=OPENAI_KEY)

# === MEMORY & RATE LIMIT ===
memory = defaultdict(list)
rate = defaultdict(list)

async def ai_reply(update: Update, context: ContextTypes.DEFAULT_TYPE, text: str, chat_id: int):
    user_id = update.effective_user.id
    
    # Rate limit
    now = datetime.now()
    rate[user_id] = [t for t in rate[user_id] if now - t < timedelta(seconds=30)]
    if len(rate[user_id]) >= 3:
        await update.message.reply_text("3/30s")
        return
    rate[user_id].append(now)

    # Memory
    memory[chat_id].append({"role": "user", "content": text})
    if len(memory[chat_id]) > 10:
        memory[chat_id] = memory[chat_id][-10:]

    msg = await update.message.reply_text("Thinking...")

    try:
        # FORCE SHORT BUT COMPLETE ANSWER
        response = await asyncio.wait_for(
            client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": "Give a COMPLETE answer in 4–6 short bullet points. Never cut off."},
                    *memory[chat_id][-5:]
                ],
                temperature=0.7,
                max_tokens=500
            ),
            timeout=15
        )
        answer = response.choices[0].message.content.strip()

        # ONE clean message + tiny sleep so Render doesn't kill it
        await asyncio.sleep(0.5)
        await msg.edit_text(answer)
        memory[chat_id].append({"role": "assistant", "content": answer})

    except Exception as e:
        await msg.edit_text("AI busy, try again.")

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
