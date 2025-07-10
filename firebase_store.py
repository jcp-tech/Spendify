"""
PIP installs:
pip install firebase-admin python-dotenv
"""

import os
import logging
from datetime import datetime
from dotenv import load_dotenv
import firebase_admin
from firebase_admin import credentials, firestore
import pandas as pd

# Setup logging
logging.basicConfig(level=logging.INFO, format='[%(asctime)s] %(levelname)s: %(message)s')

load_dotenv()

cred_path = os.getenv('FIREBASE_CREDENTIALS')
logging.info(f"Loading Firebase credentials from: {cred_path}")
if not cred_path or not os.path.exists(cred_path):
    msg = f"Firebase credentials file not found at: {cred_path}"
    logging.error(msg)
    raise FileNotFoundError(msg)

cred = credentials.Certificate(cred_path)
firebase_admin.initialize_app(cred)
db = firestore.client()
logging.info("Initialized Firebase Admin SDK")

def get_primary_id(source, identifier):
    logging.info(f"get_primary_id: source={source}, identifier={identifier}")
    docs = db.collection('USERDATA').where(source, '==', identifier).limit(1).get()
    primary = docs[0].id if docs else None
    logging.info(f"Found primary_id={primary}" if primary else "No primary_id found")
    return primary

def create_user(primary_id, source, identifier):
    logging.info(f"create_user: primary_id={primary_id}, source={source}, identifier={identifier}")
    user_ref = db.collection('USERDATA').document(primary_id)
    user_ref.set({source: identifier}, merge=True)
    logging.info("User record created/merged")

def save_session_meta(session_id, timestamp, main_user, source):
    logging.info(f"save_session_meta: session_id={session_id}, main_user={main_user}, source={source}, timestamp={timestamp}")
    sess_ref = db.collection('SESSIONS').document(session_id)
    sess_ref.set({
        'timestamp': timestamp,
        'main_user': main_user,
        'source': source
    })
    logging.info("Session metadata saved")

def save_raw_data(date_str, session_id, data_dict, timestamp):
    """
    Store raw extracted data under:
      DATA -> RAW_DATA -> {date_str} -> {session_id}
    """
    logging.info(f"save_raw_data: date={date_str}, session_id={session_id}")
    raw_ref = db.collection('DATA').document('RAW_DATA').collection(date_str).document(session_id)
    payload = {'timestamp': timestamp, **data_dict}
    raw_ref.set(payload)
    logging.info("Raw data saved under DATA/RAW_DATA")

def save_receipt_data(date_str, session_id, receipt_dict, timestamp):
    """
    Store grouped receipt entities under:
      DATA -> RECEIPTS -> {date_str} -> {session_id}
    """
    logging.info(f"save_receipt_data: date={date_str}, session_id={session_id}")
    rec_ref = db.collection('DATA').document('RECEIPTS').collection(date_str).document(session_id)
    payload = {'entities': receipt_dict} # 'timestamp': timestamp, 
    rec_ref.set(payload)
    logging.info("Receipt data saved under DATA/RECEIPTS")

def save_summarised_data(date_str, session_id, summary_dict, timestamp):
    """
    Store summarised data under:
      DATA -> SUMMARISED_DATA -> {date_str} -> {session_id}
    """
    logging.info(f"save_summarised_data: date={date_str}, session_id={session_id}")
    sum_ref = db.collection('DATA').document('SUMMARISED_DATA').collection(date_str).document(session_id)
    payload = {**summary_dict} # 'timestamp': timestamp, 
    sum_ref.set(payload)
    logging.info("Summarised data saved under DATA/SUMMARISED_DATA")

def get_all_summarised_data_as_df():
    """
    Get all summarised data as a DataFrame
    """
    logging.info("get_all_summarised_data_as_df")
    all_data = []
    # Get all the Timestams and their Corresponding Session IDs
    sessions_to_check = {}
    users_for_session = {}
    collections = db.collection('SESSIONS').get()
    for doc in collections:
        session_id = doc.id
        date_str = doc.to_dict().get('timestamp', '').split('T')[0]
        if date_str in sessions_to_check.keys():
            sessions_to_check[date_str].append(session_id)
        else:
            sessions_to_check[date_str] = [session_id]
        users_for_session[session_id] = doc.to_dict().get('main_user', None)
    for date_str, session_ids in sessions_to_check.items():
        for uu_id in session_ids:
            try:
                sum_ref = db.collection('DATA').document('SUMMARISED_DATA').collection(date_str).document(uu_id)
                sum_doc = sum_ref.get().to_dict()
                if sum_doc: # sum_doc is not None and not sum_doc == {}:
                    # {'time_taken_seconds': 65.73, 'categories': [{'category': 'Fast Food', 'total': 43.85, 'items': ['Pork Quesadilla', 'Fren Onion Soup', 'Pork Chop', 'Hanger Sizzle']}, {'category': 'Groceries', 'total': 9.95, 'items': ['Mozzarella&Tomato']}, {'category': 'Others', 'total': 0, 'items': []}], 'overall_total': '86.50'}
                    items = []
                    for key in sum_doc['categories']:
                        if key['total'] != 0:
                            items.append({
                                'user_id': users_for_session[uu_id],
                                'date': date_str,
                                # 'session_id': uu_id,
                                'category': key['category'],
                                'total': key['total'],
                            })
                    all_data += items
            except Exception as e:
                logging.error(f"Error fetching summarised data for {date_str}/{uu_id}: {e}")
                continue
    return pd.DataFrame(all_data)
print(get_all_summarised_data_as_df())