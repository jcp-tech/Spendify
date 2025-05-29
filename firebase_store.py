"""
PIP installs:
pip install firebase-admin python-dotenv
"""

import os
from datetime import datetime
from dotenv import load_dotenv
import firebase_admin
from firebase_admin import credentials, firestore

load_dotenv()

cred_path = os.getenv('FIREBASE_CREDENTIALS')
if not cred_path or not os.path.exists(cred_path):
    raise FileNotFoundError(f"Firebase credentials file not found at: {cred_path}")

cred = credentials.Certificate(cred_path)
firebase_admin.initialize_app(cred)
db = firestore.client()

def save_user_source(user_id, source_dict):
    user_ref = db.collection('USERDATA').document(user_id)
    user_ref.set(source_dict, merge=True)
    print(f'[✅] User source data saved for user: {user_id}')

def save_raw_data(user_id, date_str, session_id, data_dict):
    raw_ref = db.collection('RAW_DATA') \
                .document(user_id) \
                .collection(date_str) \
                .document(session_id)
    metadata = {
        'timestamp': datetime.utcnow().isoformat(),
        'session_id': session_id
    }
    raw_ref.set({**metadata, **data_dict})
    print(f'[✅] Raw data saved for user: {user_id}, date: {date_str}, session: {session_id}')

def save_receipt_data(user_id, date_str, session_id, receipt_dict):
    receipt_ref = db.collection('RECEIPTS') \
                     .document(user_id) \
                     .collection(date_str) \
                     .document(session_id)
    metadata = {
        'timestamp': datetime.utcnow().isoformat(),
        'session_id': session_id
    }
    # Merge metadata with grouped receipt fields as keys
    receipt_ref.set({**metadata, **receipt_dict})
    print(f'[✅] Receipt data saved for user: {user_id}, date: {date_str}, session: {session_id}')

def save_summarised_data(user_id, date_str, session_id, summary_dict):
    sum_ref = db.collection('SUMMARISED_DATA') \
                .document(user_id) \
                .collection(date_str) \
                .document(session_id)
    sum_ref.set(summary_dict)
    print(f'[✅] Summarised data saved for user: {user_id}, date: {date_str}, session: {session_id}')
