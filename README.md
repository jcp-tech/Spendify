# Capstone Project: AI-Based Receipt Processing System - SPENDIFY

SPENDIFY is an AI-powered system designed to process receipts. It allows users to upload receipt images, extracts relevant information using AI, classifies items, and stores the data for potential future analysis or expense tracking. The system comprises a backend API, a Discord bot for user interaction, and integrations with Google Cloud Document AI and Firebase.

## Table of Contents

1. [Project Overview](#1-project-overview)
2. [File Structure and Descriptions](#2-file-structure-and-descriptions)
3. [Setup and Installation](#3-setup-and-installation)
    * [Prerequisites](#prerequisites)
    * [Environment Variables (.env)](#environment-variables-env)
    * [Credentials Files](#credentials-files)
    * [Python Dependencies](#python-dependencies)
4. [How to Launch](#4-how-to-launch)
    * [Backend API](#backend-api)
    * [Discord Bot](#discord-bot)
5. [Key Components and Flow](#5-key-components-and-flow)
6. [Directory Structure](#6-directory-structure)

## 1. Project Overview

The core functionality of SPENDIFY revolves around:

*   **User Interaction**: Primarily through a Discord bot, allowing users to register and submit receipts.
*   **Receipt Processing**: Utilizes Google Cloud Document AI for OCR and initial data extraction from receipt images.
*   **Data Classification & Summarization**: Employs language models (via Langchain with Ollama) to categorize items and summarize receipt details.
*   **Data Storage**: Uses Firebase Firestore to store user information and processed receipt data.

## 2. File Structure and Descriptions

Here's a breakdown of the main Python files in the project:

*   **`main_api.py`**:
    *   **Purpose**: The central backend API built with Flask. It exposes endpoints for user registration, receipt uploads, and data retrieval.
    *   **Connections**:
        *   Receives HTTP requests from `bot.py` (e.g., for `/register`, `/get_primary`, `/upload`).
        *   Calls `gcp_docai.extract_receipt_data()` to process receipt images.
        *   Uses functions from `firebase_store.py` (e.g., `create_user`, `get_primary_id`, `save_session_meta`, `save_raw_data`, `save_receipt_data`, `save_summarised_data`) for database interactions.
        *   Integrates with `receipt_classifier.py` (functions `init_classifier` and `run`) to classify items and summarize receipt content.
    *   **Launch**: `python main_api.py`

*   **`bot.py`**:
    *   **Purpose**: A Discord bot (`discord.py`) that serves as the primary user interface. Users can register, upload receipts (as image attachments), and interact with the system via Discord commands.
    *   **Connections**:
        *   Makes HTTP requests (using the `requests` library) to the endpoints exposed by `main_api.py`.
    *   **Launch**: `python bot.py` (requires `DISCORD_TOKEN` in `.env`).

*   **`gcp_docai.py`**:
    *   **Purpose**: Contains functions to interact with Google Cloud Document AI. Its main role is to send receipt images to the Document AI service and retrieve the extracted text and entities.
    *   **Connections**:
        *   The `extract_receipt_data()` function is called by `main_api.py` when a new receipt image is uploaded.
    *   **Launch**: This is a library module, not launched directly.

*   **`firebase_store.py`**:
    *   **Purpose**: Manages all communication with the Firebase Firestore database. It includes functions for creating and retrieving user profiles, and for saving various stages of receipt data (raw, processed, summarized).
    *   **Connections**:
        *   Its functions are extensively used by `main_api.py` for all database operations.
    *   **Launch**: This is a library module, not launched directly.

*   **`receipt_classifier.py`**:
    *   **Purpose**: Implements the logic for classifying items found on receipts into predefined categories (e.g., "Groceries", "Fast Food"). It uses language models (Langchain with Ollama) and prompt templating for this task. It may also be responsible for generating summaries.
    *   **Connections**:
        *   The `run()` function (and `init_classifier()`) is used by `main_api.py` after data has been extracted by `gcp_docai.py`.
    *   **Launch**: This is a library module, not launched directly.

*   **`requirements.txt`**:
    *   **Purpose**: Lists all necessary Python packages for the project.
    *   **Usage**: Install with `pip install -r requirements.txt`.

## 3. Setup and Installation

### Prerequisites

*   Python 3.x
*   Access to Google Cloud Platform (with Document AI API enabled)
*   A Firebase project
*   A Discord Bot application

### Environment Variables (`.env`)

Create a `.env` file in the root directory of the project. This file should store sensitive keys and configuration details.

```env
# API Configuration
API_PORT=8000 # Port for the Flask API

# Language Model Configuration
MAIN_MODEL="llama3"       # Primary LLM for classification/tasks
FALLBACK_MODEL="mistral"  # Fallback LLM
VISION_MODEL="llava"      # Vision-capable LLM for image-related tasks (if used directly by classifier)

# Discord Bot Configuration
DISCORD_TOKEN="YOUR_DISCORD_BOT_TOKEN"
API_URL="http://127.0.0.1:8000" # URL of your running main_api.py
OPTIMISE="True" # Optimization flag for the bot

# Google Cloud Configuration
GOOGLE_APPLICATION_PATH="C:/path/to/your/gcp_service_account.json" # Absolute path
DOCUMENT_AI_PROCESSOR_URL="projects/YOUR_PROJECT_ID/locations/YOUR_LOCATION/processors/YOUR_PROCESSOR_ID"

# Firebase Configuration
FIREBASE_CREDENTIALS="C:/path/to/your/firebase_credentials.json" # Absolute path
```

**Note**: Replace placeholder values (like `YOUR_DISCORD_BOT_TOKEN`, paths, and GCP/Firebase project details) with your actual credentials and configuration.

### Credentials Files

*   **`gcp_service_account.json`**:
    *   **Purpose**: Service account key for authenticating with Google Cloud Platform services, including Document AI.
    *   **Setup**:
        1.  Go to the IAM & Admin section of your Google Cloud Console.
        2.  Navigate to "Service Accounts".
        3.  Create a new service account or use an existing one.
        4.  Ensure it has the necessary roles (e.g., "Document AI User" or "Editor" for the project).
        5.  Create a key (JSON format) for this service account and download it.
        6.  Rename the downloaded file to `gcp_service_account.json` and place it in a secure location. Update the `GOOGLE_APPLICATION_PATH` in your `.env` file to its absolute path.

*   **`firebase_credentials.json`**:
    *   **Purpose**: Service account key for authenticating the Firebase Admin SDK.
    *   **Setup**:
        1.  Go to your Firebase project settings in the Firebase Console.
        2.  Navigate to the "Service accounts" tab.
        3.  Click on "Generate new private key" and confirm.
        4.  A JSON file will be downloaded.
        5.  Rename this file to `firebase_credentials.json` and place it in a secure location. Update the `FIREBASE_CREDENTIALS` in your `.env` file to its absolute path.

### Python Dependencies

Install all required Python libraries using the `requirements.txt` file:

```bash
pip install -r requirements.txt
```

## 4. How to Launch

### Backend API

To start the Flask backend server:

```bash
python main_api.py
```

By default, it will run on `http://127.0.0.1:8000` (or the port specified in `API_PORT`).

### Discord Bot

To start the Discord bot:

```bash
python bot.py
```

Ensure the `DISCORD_TOKEN` and `API_URL` are correctly set in your `.env` file. The bot will connect to Discord and listen for commands and messages with attachments.

## 5. Key Components and Flow

1.  **User Registration (via Discord Bot)**:
    *   User sends a command (e.g., `!register` or attempts an action requiring registration).
    *   `bot.py` calls the `/get_primary` endpoint of `main_api.py` to check if the user (by Discord username) is known.
    *   If not registered, `bot.py` interactively prompts the user for registration details.
    *   `bot.py` calls the `/register` endpoint of `main_api.py` with the user's Discord name and chosen primary ID.
    *   `main_api.py` uses `firebase_store.create_user()` to save/update the user in Firebase.

2.  **Receipt Upload and Processing (via Discord Bot)**:
    *   User sends a message with an image attachment (the receipt) in a monitored channel.
    *   `bot.py` detects the attachment.
    *   It ensures the user is registered (using the flow above if necessary).
    *   `bot.py` uploads the image file and associated metadata (session ID, user identifier, source, timestamp) to the `/upload` endpoint of `main_api.py`.
    *   **In `main_api.py` (`/upload` endpoint)**:
        *   The primary user ID is looked up using `firebase_store.get_primary_id()`.
        *   Session metadata is saved using `firebase_store.save_session_meta()`.
        *   The uploaded image is passed to `gcp_docai.extract_receipt_data()`.
            *   `gcp_docai.py` sends the image to Google Document AI.
            *   The raw structured data from Document AI is returned.
        *   This raw data is saved using `firebase_store.save_raw_data()`.
        *   The extracted data is then passed to `receipt_classifier.run()`.
            *   `receipt_classifier.py` uses LLMs (Langchain, Ollama) to classify items and determine totals.
        *   The classified/structured receipt data is saved using `firebase_store.save_receipt_data()`.
        *   A summarized version of the data might be generated and saved using `firebase_store.save_summarised_data()`.
    *   `bot.py` (potentially, if implemented) informs the user about the processing status or results.

## 6. Directory Structure (Simplified)

```text
Spendify/
│
├── .env                    # Environment variables (create this manually)
├── main_api.py             # Flask backend API
├── bot.py                  # Discord bot
├── gcp_docai.py            # Google Cloud Document AI interaction
├── firebase_store.py       # Firebase Firestore interaction
├── receipt_classifier.py   # Receipt item classification logic
├── requirements.txt        # Python dependencies
├── README.md               # This file
│
├── gcp_service_account.json # GCP credentials (place here or secure path)
├── firebase_credentials.json# Firebase credentials (place here or secure path)
│
├── uploads/                # Likely for temporary storage of uploaded receipts
├── img_content/            # Sample images or content
└── __pycache__/            # Python bytecode cache (auto-generated)
```

This README provides a comprehensive guide to understanding, setting up, and running the SPENDIFY project.
