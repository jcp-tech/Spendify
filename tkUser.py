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

API_URL = os.getenv('API_URL', 'http://127.0.0.1:8000/upload')
USER_NAME = 'jcp-tech'

def select_and_send():
    # Hide the root window
    root = tk.Tk()
    root.withdraw()

    # Let user pick an image file
    file_path = filedialog.askopenfilename(
        title="Select Image File",
        filetypes=[("Image Files", "*.png *.jpg *.jpeg *.bmp *.gif")])
    if not file_path:
        print("No file selected.")
        return

    # Prepare metadata
    session_id = str(uuid.uuid4())
    timestamp = datetime.utcnow().isoformat()
    file_name = os.path.basename(file_path)
    ext = file_name.split('.')[-1].lower()
    mime_type = f"image/{ext if ext != 'jpg' else 'jpeg'}"

    # Upload to API
    with open(file_path, 'rb') as f:
        files = {'file': (file_name, f, mime_type)}
        data = {
            'session_id': session_id,
            'user_name': USER_NAME,
            'timestamp': timestamp
        }
        try:
            response = requests.post(API_URL, files=files, data=data)
            response.raise_for_status()
            print("✅ Response from server:", response.json())
        except Exception as e:
            print("❌ Failed to send:", e)

if __name__ == '__main__':
    select_and_send()
