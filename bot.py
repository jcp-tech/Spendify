"""
PIP installs:
pip install -U discord.py python-dotenv requests
"""

import os, uuid
import requests
from dotenv import load_dotenv
import discord
from discord.ext import commands
from datetime import datetime

load_dotenv()

DISCORD_TOKEN = os.getenv('DISCORD_TOKEN')
API_URL = os.getenv('API_URL', 'http://127.0.0.1:8000/upload')

intents = discord.Intents.default()
intents.message_content = True
intents.messages = True
intents.guilds = True
intents.members = True

bot = commands.Bot(command_prefix='!', intents=intents)

@bot.event
async def on_ready():
    print(f'✅ Logged in as {bot.user} (ID: {bot.user.id})')

@bot.event
async def on_message(message):
    if message.author == bot.user:
        return

    if message.attachments:
        # Ensure img_content folder exists
        img_dir = os.path.join(os.getcwd(), 'img_content')
        os.makedirs(img_dir, exist_ok=True)

        for attachment in message.attachments:
            if attachment.content_type and attachment.content_type.startswith('image/'):
                session_id = str(uuid.uuid4())
                timestamp = message.created_at.isoformat()
                user_name = message.author.name
                file_extension = attachment.filename.split('.')[-1]
                file_name = f'{session_id}.{file_extension}'
                file_path = os.path.join(img_dir, file_name)
                await attachment.save(file_path)
                print(f'[📸] Saved image: {file_path}')

                # Send to API
                with open(file_path, 'rb') as f:
                    files = {'file': (file_name, f, attachment.content_type)}
                    data = {
                        'session_id': session_id,
                        'user_name': user_name,
                        'timestamp': timestamp
                    }
                    try:
                        response = requests.post(API_URL, files=files, data=data)
                        response.raise_for_status()
                        print(f'[✅] Successfully sent to API: {response.json()}')
                    except Exception as e:
                        print(f'[❌] Failed to send to API: {e}')

    await bot.process_commands(message)

if __name__ == '__main__':
    bot.run(DISCORD_TOKEN)
