# Discord Bot

An interactive bot for uploading receipt images directly from Discord to the Spendify processing pipeline.

---

## 🤖 Bot Overview

This bot listens for image attachments in any channel it has access to. When a user sends a receipt image, the bot:

1. Ensures the user is registered via the API.
2. Saves the image locally with a session ID.
3. Uploads the image to the Flask API for processing.
4. Provides status feedback in Discord.

---

## 💡 Key Features

* **Interactive registration** – the bot guides new users through creating a primary ID.
* **Asynchronous uploads** – images are uploaded in the background while the user continues chatting.
* **Session tracking** – each upload is associated with a unique session ID for later reference.

---

## 🚀 Getting Started

1. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
2. Copy `.env.template` to `.env` and fill in:
   - `DISCORD_TOKEN` – your Discord bot token.
   - `API_URL` – base URL of the Flask API.
3. Run the bot:
   ```bash
   python bot.py
   ```

---

## 📝 Commands

The bot does not use complex commands. Simply upload an image in a channel where the bot is present. If the user is unregistered, the bot will prompt for registration through chat messages.

---

## 🛠️ Extending the Bot

* **Additional platforms** – adapt `process_upload` to send images to other APIs.
* **Custom prefixes or commands** – modify the `commands.Bot` initialization in `bot.py`.
* **Persistent storage** – change where images are temporarily saved before upload.

