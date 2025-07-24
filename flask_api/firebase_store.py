import os
import logging
from datetime import datetime
import uuid
from dotenv import load_dotenv
import firebase_admin
from firebase_admin import auth, credentials, firestore # , realtime
import pandas as pd
from flask import request, jsonify

# Setup logging
logging.basicConfig(level=logging.INFO, format='[%(asctime)s] %(levelname)s: %(message)s')

load_dotenv()

cred_path = os.getenv('FIREBASE_CREDENTIALS', 'firebase_credentials.json')
logging.info(f"Loading Firebase credentials from: {cred_path}")
if not cred_path or not os.path.exists(cred_path):
    code_current_dir = os.path.dirname(os.path.abspath(__file__))
    msg = f"Firebase credentials file not found at: {cred_path}"
    logging.error(msg)
    # raise FileNotFoundError(msg)
    # Look in current directory for `firebase_credentials.json`
    cred_path = os.path.join(code_current_dir, 'firebase_credentials.json')
    if not os.path.exists(cred_path):
        logging.error(f"Firebase credentials file not found at: {cred_path}")
        raise FileNotFoundError(msg)

cred = credentials.Certificate(cred_path)
firebase_admin.initialize_app(cred)
db = firestore.client()
logging.info("Initialized Firebase Admin SDK")


def create_user(primary_id, source, identifier, session_id=None):
    logging.info(f"create_user: primary_id={primary_id}, source={source}, identifier={identifier}")
    user_ref = db.collection('USERDATA').document(primary_id)
    # Check for session_id in existing user
    if session_id is None:
        if user_ref.get().to_dict() is not None:
            if 'session_id' in user_ref.get().to_dict():
                session_id = user_ref.get().to_dict()['session_id']
                logging.info(f"Using existing session_id={session_id} for primary_id={primary_id}")
            else:
                session_id = str(uuid.uuid4())
        else:
            session_id = str(uuid.uuid4())
    user_ref.set({
        source: identifier,
        'session_id': session_id,
        'WEB': primary_id,  # Always set WEB as primary_id for web dashboard
    }, merge=True)
    logging.info("User record created/merged")
    return session_id

def authenticate(main_source, session_id):
    # Search if any db.collection('USERDATA').document(primary_id) has this session_id and return the primary_id
    primary_id = db.collection('USERDATA').where('session_id', '==', session_id).limit(1).get()[0].id
    # main_source can be 'TRUE' or 'FALSE' | it refers to wheter the source of the request is main (api) or not (e.g. web dashboard)
    id_token = request.json.get('idToken')
    # is_new_user = request.json.get('isNewUser')  # <--- NEW
    try:
        decoded_token = auth.verify_id_token(id_token)  # Verify the ID token
        # Prevent overwriting an existing auth identifier
        user_doc = db.collection('USERDATA').document(primary_id).get().to_dict() or {}
        if 'auth' in user_doc and user_doc['auth'] != decoded_token['uid']:
            logging.warning(
                f"Registration blocked for {primary_id}: already linked to another auth account"
            )
            return jsonify({'status': 'already_registered'}), 409
        elif 'auth' in user_doc and user_doc['auth'] == decoded_token['uid']:
            logging.info(f"User {primary_id} already registered with auth {decoded_token['uid']}")
        # else:
        #     pass
        create_user(primary_id, 'auth', decoded_token['uid'], session_id)
        """
            {
                'name': 'User\'s display name',
                'picture': 'URL to user\'s profile picture',
                'iss': 'Issuer of the token',
                'aud': 'Audience (project ID)',
                'auth_time': 'Authentication time (Unix timestamp)',
                'user_id': 'Firebase user ID',
                'sub': 'Subject (user ID)',
                'iat': 'Issued at (Unix timestamp)',
                'exp': 'Expiration time (Unix timestamp)',
                'email': 'User\'s email address',
                'email_verified': 'Whether email is verified (bool)',
                'firebase': {
                'identities': {
                    'google.com': 'List of Google account IDs',
                    'email': 'List of email addresses'
                },
                'sign_in_provider': 'Sign-in provider (e.g., google.com)'
                },
                'uid': 'Firebase user ID'
            }
        """
        # decoded_token = dict(decoded_token)  # Convert to dict for easier access
        decoded_token['decoded_token'] = id_token  # Store the original ID token
        create_user(primary_id, 'decoded_token', dict(decoded_token), session_id)
        return jsonify({
            "status": "success",
            # "uid": decoded_token['uid'],
            # "email": decoded_token['email'],
            # "session_id": session_id
        }), 200
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 401

def login_check():
    """Verify Google ID token and check if a corresponding user exists."""
    id_token = request.json.get('idToken')
    try:
        decoded_token = auth.verify_id_token(id_token)
        uid = decoded_token['uid']
        docs = db.collection('USERDATA').where('auth', '==', uid).limit(1).get()
        if docs:
            primary_id = docs[0].id
            session_id = create_user(primary_id, 'auth', uid)
            create_user(primary_id, 'decoded_token', dict(decoded_token), session_id)
            return jsonify({
                'status': 'existing',
                'primary_id': primary_id,
                'session_id': session_id
            }), 200
        else:
            return jsonify({'status': 'new'}), 200
    except Exception as e:
        logging.exception('Login check failed')
        return jsonify({'status': 'error', 'message': str(e)}), 401

def get_primary_id(source, identifier):
    logging.info(f"get_primary_id: source={source}, identifier={identifier}")
    docs = db.collection('USERDATA').where(source, '==', identifier).limit(1).get()
    primary = docs[0].id if docs else None
    logging.info(f"Found primary_id={primary}" if primary else "No primary_id found")
    return primary

def get_user_document(primary_id):
    """Return the USERDATA document for the given primary_id or None."""
    logging.info(f"get_user_document: {primary_id}")
    doc_ref = db.collection('USERDATA').document(primary_id)
    doc = doc_ref.get()
    doc_dict = doc.to_dict() if doc.exists else None
    if doc_dict is not None:
        if 'decoded_token' in doc_dict:
            del doc_dict['decoded_token'] # Remove the decoded_token field to avoid sending sensitive data
    return doc_dict

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

def get_all_summarised_data_as_df(USERNAME=None):
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
            logging.info(f"Fetching summarised data for {date_str}/{uu_id}")
            try:
                sum_ref = db.collection('DATA').document('SUMMARISED_DATA').collection(date_str).document(uu_id)
                sum_doc = sum_ref.get().to_dict()
                if sum_doc: # sum_doc is not None and not sum_doc == {}:
                    # {'time_taken_seconds': 65.73, 'categories': [{'category': 'Fast Food', 'total': 43.85, 'items': ['Pork Quesadilla', 'Fren Onion Soup', 'Pork Chop', 'Hanger Sizzle']}, {'category': 'Groceries', 'total': 9.95, 'items': ['Mozzarella&Tomato']}, {'category': 'Others', 'total': 0, 'items': []}], 'overall_total': '86.50'}
                    items = []
                    for key in sum_doc['categories']:
                        if float(key['total_price']) != 0 and key['category'] != 'Tax':
                            items.append({
                                'user_id': users_for_session[uu_id],
                                'date': date_str,
                                # 'session_id': uu_id,
                                'category': key['category'],
                                'total': float(key['total_price']),
                            })
                    all_data += items
            except Exception as e:
                logging.error(f"Error fetching summarised data for {date_str}/{uu_id}: {e}")
                continue
    logging.info(f"Total summarised records found: {all_data}")
    df = pd.DataFrame(all_data)
    if USERNAME and not df.empty:
        df = df[df['user_id'] == USERNAME]
    return df
# print(get_all_summarised_data_as_df().to_dict(orient='records'))