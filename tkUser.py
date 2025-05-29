# NOTE: This script is designed to Test the API for uploading images from an Alternative Client.


"""
PIP installs:
pip install requests python-dotenv
"""

import os
import uuid
from datetime import datetime
import requests
import tkinter as tk
from tkinter import filedialog
from dotenv import load_dotenv

load_dotenv()

API_BASE = os.getenv('API_URL', 'http://127.0.0.1:8000')
SOURCE = 'TKINTER'

# Identifier for this source (e.g., your configured TKINTER_ID in .env)
IDENTIFIER = os.getenv('TKINTER_ID')
if not IDENTIFIER:
    IDENTIFIER = input("Enter your identifier (e.g. 'jcp-tech'): ").strip()

def ensure_registration():
    """Check or register this identifier with the API, returning primary_id."""
    # Try to get existing primary
    resp = requests.get(f"{API_BASE}/get_primary", params={
        'source': SOURCE,
        'identifier': IDENTIFIER
    })
    if resp.status_code == 200:
        return resp.json().get('primary_id')

    print("You are not registered for TKINTER uploads.")
    if input("Register now? (yes/no): ").lower().startswith('y'):
        # Ask for desired primary ID
        primary = input(f"Enter desired primary ID (default '{IDENTIFIER}'): ").strip() or IDENTIFIER
        r2 = requests.post(f"{API_BASE}/register", json={
            'source': SOURCE,
            'identifier': IDENTIFIER,
            'primary_id': primary
        })
        if r2.ok:
            print(f"Registered under primary ID: {primary}")
            return primary
        else:
            print("Registration failed:", r2.text)
    return None

def select_and_send():
    primary = ensure_registration()
    if not primary:
        print("Cannot proceed without registration.")
        return

    # Hide root UI
    root = tk.Tk()
    root.withdraw()

    file_path = filedialog.askopenfilename(
        title="Select Image File",
        filetypes=[("Image Files", "*.png *.jpg *.jpeg *.bmp *.gif")]
    )
    if not file_path:
        print("No file selected.")
        return

    session_id = str(uuid.uuid4())
    timestamp = datetime.utcnow().isoformat()
    file_name = os.path.basename(file_path)
    ext = file_name.split('.')[-1].lower()
    mime_type = f"image/{{ext if ext != 'jpg' else 'jpeg'}}"

    with open(file_path, 'rb') as f:
        files = {'file': (file_name, f, mime_type)}
        data = {
            'session_id': session_id,
            'identifier': IDENTIFIER,
            'source': SOURCE,
            'timestamp': timestamp
        }
        print(f"Uploading session {session_id}...")
        r = requests.post(f"{API_BASE}/upload", files=files, data=data)
        if r.ok:
            print("✅ Processing started:", r.json())
        else:
            print("❌ Upload failed:", r.status_code, r.text)

if __name__ == '__main__':
    select_and_send()
