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
import asyncio
from functools import partial

load_dotenv()

DISCORD_TOKEN = os.getenv('DISCORD_TOKEN')
API_BASE = os.getenv('API_URL', 'http://127.0.0.1:8000')

intents = discord.Intents.default()
intents.message_content = True
intents.messages = True
intents.guilds = True
intents.members = True

bot = commands.Bot(command_prefix='!', intents=intents)

async def ensure_registered(ctx):
    """
    Check with API if user is registered.
    If not, interactively register them.
    Return primary_id or None.
    """
    identifier = ctx.author.name
    # Quick check
    try:
        r = requests.get(f"{API_BASE}/get_primary", params={
            'source': 'DISCORD',
            'identifier': identifier
        })
        if r.status_code == 200:
            return r.json().get('primary_id')
    except:
        await ctx.channel.send("❗ Registration check failed. Try again later.")
        return None

    # Not registered: prompt user
    await ctx.channel.send("You are not registered. Would you like to register now? (yes/no)")
    def check(m):
        return m.author == ctx.author and m.channel == ctx.channel

    try:
        msg = await bot.wait_for('message', check=check, timeout=60)
    except asyncio.TimeoutError:
        await ctx.channel.send("⏰ Registration timed out.")
        return None

    if not msg.content.lower().startswith('y'):
        await ctx.channel.send("Cannot process without registration. Please register later.")
        return None

    # Ask for primary ID
    await ctx.channel.send("Use your Discord username as primary ID? (yes/no)")
    try:
        opt = await bot.wait_for('message', check=check, timeout=60)
    except asyncio.TimeoutError:
        await ctx.channel.send("⏰ Registration timed out.")
        return None

    if opt.content.lower().startswith('y'):
        primary = identifier
    else:
        await ctx.channel.send("Please enter your desired primary ID:")
        try:
            custom = await bot.wait_for('message', check=check, timeout=60)
            primary = custom.content.strip()
        except asyncio.TimeoutError:
            await ctx.channel.send("⏰ Registration timed out.")
            return None

    # Call API to register
    try:
        resp = requests.post(f"{API_BASE}/register", json={
            'source': 'DISCORD',
            'identifier': identifier,
            'primary_id': primary
        })
        resp.raise_for_status()
        await ctx.channel.send(f"✅ Registered under ID: `{primary}`")
        return primary
    except Exception as e:
        await ctx.channel.send(f"❌ Registration failed: {e}")
        return None

async def process_upload(session_id, file_path, identifier, primary, source, timestamp):
    """
    Background upload to API.
    """
    try:
        with open(file_path, 'rb') as f:
            files = {'file': (os.path.basename(file_path), f, f"image/{{file_path.split('.')[-1]}}")}
            data = {
                'session_id': session_id,
                'identifier': identifier,
                'source': source,
                'timestamp': timestamp
            }
            requests.post(f"{API_BASE}/upload", files=files, data=data, timeout=30)
    except Exception as e:
        print(f"[❌] Background upload failed for session {session_id}: {e}")

@bot.event
async def on_message(message):
    if message.author == bot.user:
        return

    # Process commands (like !register)
    await bot.process_commands(message)

    if message.attachments:
        # Ensure registration
        primary = await ensure_registered(message)
        if not primary:
            return

        # Ensure img_content folder exists
        img_dir = os.path.join(os.getcwd(), 'img_content')
        os.makedirs(img_dir, exist_ok=True)

        identifier = message.author.name
        source = 'DISCORD'

        for attachment in message.attachments:
            if attachment.content_type and attachment.content_type.startswith('image/'):
                session_id = str(uuid.uuid4())
                timestamp = message.created_at.isoformat()
                file_extension = attachment.filename.split('.')[-1]
                file_name = f'{session_id}.{file_extension}'
                file_path = os.path.join(img_dir, file_name)
                await attachment.save(file_path)
                await message.channel.send(f"📸 Image saved, session `{session_id}`. Uploading for processing...")

                # Schedule background upload
                asyncio.create_task(process_upload(
                    session_id, file_path, identifier, primary, source, timestamp
                ))

if __name__ == '__main__':
    bot.run(DISCORD_TOKEN)
