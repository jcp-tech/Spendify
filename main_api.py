"""
PIP installs:
pip install flask python-dotenv google-cloud-documentai firebase-
pip install langchain langchain-ollama
"""

import os, logging, sys, json
from flask import Flask, request, jsonify
from dotenv import load_dotenv
from gcp_docai import extract_receipt_data
from firebase_store import (
    get_primary_id, create_user,
    save_session_meta, save_raw_data, save_receipt_data, save_summarised_data
)
from receipt_classifier import init_classifier, run as classify_run

# Load ENV
load_dotenv()
API_PORT = int(os.getenv('API_PORT', 8000))

# Set default models if not passed via CLI
DEFAULT_MAIN_MODEL = os.getenv("MAIN_MODEL", "llama3")
DEFAULT_FALLBACK_MODEL = os.getenv("FALLBACK_MODEL", "mistral")

# Setup logging
logging.basicConfig(level=logging.INFO, format='[%(asctime)s] %(levelname)s: %(message)s')
app = Flask(__name__)

# 🔁 MODELS INIT
init_classifier(primary=DEFAULT_MAIN_MODEL, fallback=DEFAULT_FALLBACK_MODEL)

@app.route('/register', methods=['POST'])
def register():
    payload = request.get_json() or {}
    source = payload.get('source')
    identifier = payload.get('identifier')
    primary_id = payload.get('primary_id') or identifier
    logging.info(f"Register request: source={source}, identifier={identifier}, primary_id={primary_id}")
    if not source or not identifier:
        return jsonify({'error': 'Missing source or identifier'}), 400
    create_user(primary_id, source, identifier)
    logging.info(f"User created/updated: {primary_id} -> {source}:{identifier}")
    return jsonify({'status': 'registered', 'primary_id': primary_id}), 200

@app.route('/get_primary', methods=['GET'])
def get_primary():
    source = request.args.get('source')
    identifier = request.args.get('identifier')
    logging.info(f"Get_primary request: source={source}, identifier={identifier}")
    if not source or not identifier:
        return jsonify({'error': 'Missing source or identifier'}), 400
    primary = get_primary_id(source, identifier)
    if primary:
        logging.info(f"Found primary_id={primary}")
        return jsonify({'primary_id': primary}), 200
    logging.warning("Primary ID not found")
    return jsonify({'error': 'not found'}), 404

@app.route('/upload', methods=['POST'])
def upload():
    logging.info("Upload endpoint hit")
    file = request.files.get('file')
    session_id = request.form.get('session_id')
    identifier = request.form.get('identifier')
    source = request.form.get('source')
    timestamp = request.form.get('timestamp')
    # --- Parse these with type safety ---
    optimize = request.form.get("optimize", "True")
    optimize = optimize if isinstance(optimize, bool) else (optimize.lower() == "true")
    num_workers = int(request.form.get("num_workers", 3))
    logging.info(f"Params: session_id={session_id}, identifier={identifier}, source={source}, timestamp={timestamp}")
    if not file or not session_id or not identifier or not source or not timestamp:
        logging.error("Missing parameters in upload request")
        return jsonify({'error': 'Missing parameters'}), 400

    # Lookup primary user
    primary = get_primary_id(source, identifier)
    if not primary:
        logging.error(f"User not registered: {source}:{identifier}")
        return jsonify({'error': 'User not registered'}), 403

    # Save session metadata
    logging.info(f"Saving session metadata for session {session_id}")
    save_session_meta(session_id, timestamp, primary, source)

    # Save uploaded file
    upload_dir = 'uploads'
    os.makedirs(upload_dir, exist_ok=True)
    save_path = os.path.join(upload_dir, f'{session_id}_{file.filename}')
    file.save(save_path)
    logging.info(f"Saved file to {save_path}")

    # Process with GCP
    try:
        logging.info("Calling GCP Document AI")
        document_dict, document_proto = extract_receipt_data(save_path)
        logging.info(f"GCP returned document with {len(document_proto.entities)} entities")
    except Exception as e:
        logging.exception("GCP processing failed")
        return jsonify({'error': 'GCP failed', 'details': str(e)}), 500

    # Organize entities by type
    grouped = {}
    for entity in document_proto.entities:
        grouped.setdefault(entity.type_, []).append(entity.mention_text)
    logging.info(f"Grouped entities: { {k: len(v) for k,v in grouped.items()} }")

    # Store raw & receipts under DATA collection
    date_str = timestamp.split('T')[0]
    logging.info("Saving raw data under DATA/RAW_DATA")
    save_raw_data(date_str, session_id, document_dict, timestamp)
    logging.info("Saving receipt data under DATA/RECEIPTS")
    save_receipt_data(date_str, session_id, grouped, timestamp)

    # === CLASSIFICATION & SUMMARY SECTION ===
    item_candidates = (
        grouped.get("line_item")
        # or grouped.get("item")
        # or grouped.get("ITEM")
        or []
    )
    if not item_candidates:
        possible_item_keys = [k for k in grouped.keys() if "item" in k.lower()]
        if possible_item_keys:
            item_candidates = grouped[possible_item_keys[0]]

    if item_candidates:
        logging.info(f"Classifying {len(item_candidates)} items for session {session_id}")
        try:
            classified = classify_run(
                item_candidates,
                optimize=optimize,
                num_workers=num_workers
            )  # From receipt_classifier.py

            # Optional: Aggregate totals per category
            category_totals = {}
            for entry in classified:
                cat = entry.get("category", "Others")
                category_totals[cat] = category_totals.get(cat, 0) + 1

            summary_dict = {
                "classified_items": classified,         # List of {item, category}
                "category_counts": category_totals,     # Simple count per category
            }
            save_summarised_data(date_str, session_id, summary_dict, timestamp)
            logging.info("Summarised (classified) data saved under DATA/SUMMARISED_DATA")
        except Exception as e:
            logging.exception(f"Classification failed for session {session_id}: {e}")
    else:
        logging.warning(f"No 'item' candidates found for classification for session {session_id}")

    logging.info(f"Completed processing for session {session_id}")
    return jsonify({'status': 'processing', 'session_id': session_id}), 200

# CLASSIFICATION ENDPOINT
@app.route("/classify", methods=["POST"])
def classify():
    data = request.get_json()
    items = data.get("items", [])
    optimize = data.get("optimize", True)
    num_workers = data.get("num_workers", 3)

    if not items or not isinstance(items, list):
        return jsonify({"error": "Invalid or missing 'items' list."}), 400

    results = classify_run(
        items,
        optimize=optimize,
        num_workers=num_workers
    )
    return jsonify(results)

if __name__ == '__main__':
    logging.info(f"🌐 Starting API on port {API_PORT}")
    app.run(host='0.0.0.0', port=API_PORT)