# Flask API

Central service that receives uploaded receipts, extracts data with Google Document AI, classifies items via the ADK pipeline and stores results in Firebase.

---

## 🌐 API Overview

The API exposes endpoints for user registration, file uploads and data retrieval. On upload it performs:

1. OCR extraction using Document AI.
2. Grouping of recognised entities.
3. Optional classification via the ADK pipeline.
4. Persistence of raw and summarised data in Firebase.

---

## 💡 Key Features

* **Document AI integration** for robust OCR across many receipt formats.
* **Firebase storage** of sessions, raw OCR data and classification results.
* **Dashboard endpoint** (`/`) serving a simple spending summary UI.

---

## 🚀 Getting Started

1. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
2. Copy `.env.template` to `.env` and configure:
   - `API_PORT` – port to run the Flask server.
   - `CLASSIFICATION_URL` – URL of the ADK classification service.
   - `FIREBASE_CREDENTIALS` – path to your Firebase service account JSON.
   - `GOOGLE_APPLICATION_PATH` and `DOCUMENT_AI_PROCESSOR_URL` for Document AI.
3. Run the API locally:
   ```bash
   python main_api.py
   ```
   The dashboard will be available at `http://localhost:<API_PORT>/`.
5. Refer to
   - /docs on the web.
   <!-- - or /... -->

---

## 📝 Endpoints

| Method | Path          | Description                       |
| ------ | ------------- | --------------------------------- |
| `POST` | `/register`   | Register a new user source.       |
| `GET`  | `/get_primary`| Look up a user's primary ID.      |
| `POST` | `/upload`     | Upload a receipt image.           |
| `GET`  | `/summary`    | Aggregated spend summary.         |
| `GET`  | `/get_data`   | Raw summarised data for analysis. |
| `GET`  | `/health`     | Health check for monitoring.      |

---

## 🛠️ Extending the API

* **Additional processing** – customise `main_api.py` to add new validation or analytics.
* **Alternate storage backends** – replace `firebase_store.py` with your database of choice.
* **Custom dashboards** – modify files under `dashboard/` for a tailored UI.

