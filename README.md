# Capstone Project: AI-Based Receipt Processing System

## 📚 Overview
This repository implements the Milestone 1 deliverable of a capstone project: an end-to-end pipeline that
1. Receives receipt images via Discord bot
2. Forwards them to a backend API for processing
3. Extracts structured data using Google Cloud Vertex Document AI
4. Stores the raw and user metadata in Firebase Firestore

Each component is modularized into separate Python scripts to simplify testing, maintenance, and future extensions.

---

## 🗂 Repository Structure

```text
├── bot.py               # Discord bot: captures images, metadata, and POSTs to API1
├── api1.py              # Flask API: endpoint to accept uploads, orchestrate GCP and Firebase calls
├── gcp_docai.py         # Wrapper for Vertex Document AI: sends images and returns parsed JSON
├── firebase_store.py    # Firestore helper: writes USERDATA, RAW_DATA, SUMMARISED_DATA
├── requirements.txt     # All Python dependencies
└── README.md            # This documentation
```

---

## ⚙️ Prerequisites

- **Python 3.8+** installed
- **Google Cloud Service Account JSON** with Document AI permissions
- **Firebase Service Account JSON** with Firestore permissions
- Discord bot token and a Discord server where the bot is invited

---

## 🔐 Environment Variables
Create a `.env` file in the root directory with the following:

```ini
# Discord Bot
DISCORD_TOKEN=your_discord_bot_token
API1_URL=http://<API_HOST>:<API_PORT>/upload

# GCP Document AI
GOOGLE_APPLICATION_PATH=/path/to/gcp_service_account.json
DOCUMENT_AI_PROCESSOR_URL=https://us-documentai.googleapis.com/v1/projects/PROJECT_ID/locations/LOCATION/processors/PROCESSOR_ID:process

# Firebase
FIREBASE_CREDENTIALS=/path/to/firebase_service_account.json

# API1 Settings (optional)
API_PORT=8000
```

---

## 📦 Installation

1. Clone the repo:
   ```bash
   git clone https://github.com/your-org/receipt-ai-capstone.git
   cd receipt-ai-capstone
   ```
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. Create and populate `.env` as described above.

---

## 🚀 Usage

### 1. Start the Flask API (`api1.py`)
```bash
python api1.py
```
By default, it listens on `0.0.0.0:${API_PORT}` and exposes:
- **POST /upload** — Accepts form-data: `file`, `session_id`, `user_name`, `timestamp`.

### 2. Run the Discord Bot (`bot.py`)
```bash
python bot.py
```
- On image attachments, the bot:
  - Saves the file locally
  - Generates a UUID session ID
  - Sends the file and metadata to `/upload`

### 3. Processing Flow
1. **Discord Bot** receives image → POSTs to **API1**
2. **API1** saves image, calls `extract_receipt_data` from **gcp_docai.py**
3. **gcp_docai.py** returns parsed JSON via Vertex AI
4. **API1** calls Firestore helpers in **firebase_store.py**:
   - `save_user_source(...)` → stores mapping of user ID to source
   - `save_raw_data(...)` → stores raw GCP output under `RAW_DATA/{user}/{date}/{session}`
5. (Future) **SUMMARISED_DATA** can be filled via `save_summarised_data(...)`

---

## 🛠️ Customization & Extension
- **Add other bots**: Simply replicate `bot.py` logic for WhatsApp or Slack SDKs.
- **Summarization**: Implement an ML or LLM-based summarizer and call `save_summarised_data`.
- **Dashboard**: Build a web UI that reads Firestore collections.

---

## 📄 License
This project is released