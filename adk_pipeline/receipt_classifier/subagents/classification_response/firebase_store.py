# classification_response/firebase_store.py
import os
import firebase_admin
from firebase_admin import credentials, firestore # , realtime

cred_path = os.getenv('FIREBASE_CREDENTIALS', 'firebase_credentials.json')
print(f"Loading Firebase credentials from: {cred_path}")
if not cred_path or not os.path.exists(cred_path):
    code_current_dir = os.path.dirname(os.path.abspath(__file__))
    msg = f"Firebase credentials file not found at: {cred_path}"
    print(msg)
    cred_path = os.path.join(code_current_dir, 'firebase_credentials.json')
    if not os.path.exists(cred_path):
        print(f"Firebase credentials file not found at: {cred_path}")
        raise FileNotFoundError(msg)

cred = credentials.Certificate(cred_path)
firebase_admin.initialize_app(cred)
db = firestore.client()

def save_summarised_data(date_str, session_id, summary_dict, timestamp): # , final_total
    """
    Store summarised data under:
      DATA -> SUMMARISED_DATA -> {date_str} -> {session_id}
    """
    sum_ref = db.collection('DATA').document('SUMMARISED_DATA').collection(date_str).document(session_id)
    print(f"Saving summarised data to: DATA/SUMMARISED_DATA/{date_str}/{session_id}")
    print(f"Summary data: {summary_dict}")
    # [{'category': 'Others', 'items': ['g1 Imp White', 'Blue Moon Tap'], 'total_price': '13.75'}, {'items': ['Mozzarella&Tomato', 'Pork Quesadilla', 'Fren Onion Soup', 'Pork Chop', 'Hanger Sizzle'], 'category': 'Fast Food', 'total_price': '72.75'}]
    final_total = sum(float(item['total_price']) for item in summary_dict if 'total_price' in item)
    payload = {"categories": summary_dict, 'timestamp': timestamp, 'final_total': final_total}
    sum_ref.set(payload)
    print(f"Data saved successfully for session {session_id} on {date_str}.")