# successmindai-bot

Minimal Telegram AI bot (webhook) using python-telegram-bot v20 and OpenAI.

## Files
- `main.py` — webhook bot code
- `requirements.txt` — dependencies
- `.env.example` — example env vars

## Quick deploy to Render

1. Create a new GitHub repo (e.g., `successmindai-bot-v1`) and add the files above.
2. In Render: New → Web Service → connect the repo.
   - **Service name**: `successmindai-bot-v1` (or choose your own)
   - **Build command**: `pip install -r requirements.txt`
   - **Start command**: `python main.py`
3. Add environment variables in Render (do not commit them):
   - `BOT_TOKEN` = your Telegram bot token
   - `OPENAI_API_KEY` = your OpenAI API key
   - `WEBHOOK_URL` = `https://successmindai-bot-v1.onrender.com/webhook` (replace if you chose a different service name)
   - `PORT` = `10000`
4. Deploy. On first deploy choose "Clear cache and deploy" if available.
5. Test:
   - DM the bot: send `/start`
   - In a group: mention `@YourBotUsername` or use `/ask your question`

## Security notes
- **Do not** paste tokens or keys into code or commit them.
- If a token was ever posted publicly, **regenerate** it in BotFather and update Render env var.
- Keep `requirements.txt` clean — do not include a package named `telegram`. Use `python-telegram-bot[webhooks]==20.8`.

## Troubleshooting
- If you see errors referencing `Updater` or a `telegram` package, ensure:
  - `requirements.txt` contains only the pinned packages above.
  - No `telegram/` folder exists in the repo.
  - You cleared Render build cache and redeployed.
