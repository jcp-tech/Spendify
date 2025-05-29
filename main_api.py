"""
PIP installs:
pip install flask python-dotenv google-cloud-documentai firebase-admin
"""

import os
from flask import Flask, request, jsonify
from dotenv import load_dotenv
from gcp_docai import extract_receipt_data
from firebase_store import save_user_source, save_raw_data, save_receipt_data

load_dotenv()

API_PORT = int(os.getenv('API_PORT', 8000))
app = Flask(__name__)

@app.route('/upload', methods=['POST'])
def upload():
    file = request.files.get('file')
    session_id = request.form.get('session_id')
    user_name = request.form.get('user_name')
    timestamp = request.form.get('timestamp')
    source = 'DISCORD'
    user_id = user_name

    if not file or not session_id or not user_name or not timestamp:
        return jsonify({'error': 'Missing parameters'}), 400

    # Save uploaded image
    upload_dir = 'uploads'
    os.makedirs(upload_dir, exist_ok=True)
    save_path = os.path.join(upload_dir, f'{session_id}_{file.filename}')
    file.save(save_path)

    # Extract with GCP
    try:
        document_dict, document_proto = extract_receipt_data(save_path)
    except Exception as e:
        print(f'[❌] GCP processing failed: {e}')
        return jsonify({'error': 'GCP processing failed', 'details': str(e)}), 500

    # Group entities by type into lists
    grouped = {}
    for entity in document_proto.entities:
        grouped.setdefault(entity.type_, []).append(entity.mention_text)

    # Store in Firebase
    try:
        save_user_source(user_id, {source: user_name})
        save_raw_data(user_id, timestamp.split('T')[0], session_id, document_dict)
        save_receipt_data(user_id, timestamp.split('T')[0], session_id, grouped)
    except Exception as e:
        print(f'[❌] Firebase storing failed: {e}')
        return jsonify({'error': 'Firebase storing failed', 'details': str(e)}), 500

    print(f'[✅] Processed session: {session_id}')
    return jsonify({'status': 'success', 'session_id': session_id}), 200

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=API_PORT)
