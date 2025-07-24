from flask import Flask, request, jsonify, send_from_directory, render_template, url_for
# from flask_cors import CORS
import os, logging, json # , base64, sys
import uuid
from dotenv import load_dotenv
from gcp_docai import extract_receipt_data #, set_gc_credentials
from firebase_store import (
    get_primary_id, create_user,
    save_session_meta, save_raw_data, save_receipt_data, # save_summarised_data,
    authenticate, login_check, get_all_summarised_data_as_df, get_user_document
)
from gcp_adk_classification import ADKClient
from datetime import datetime
import pandas as pd
import calendar

code_dir = os.path.dirname(os.path.abspath(__file__))
DASHBOARD_DIR = os.path.join(code_dir, "dashboard") # Directory to serve the dashboard HTML from

# Load ENV
load_dotenv()
API_PORT = int(os.getenv('API_PORT', 8080))
CLASSIFICATION_URL = os.getenv('CLASSIFICATION_URL', 'http://localhost:8000')

# Setup logging
logging.basicConfig(level=logging.INFO, format='[%(asctime)s] %(levelname)s: %(message)s')
app = Flask(__name__, template_folder=DASHBOARD_DIR)
# CORS(app)  # This allows all origins; restrict for production!

def safe_sum(val1, val2):
    try:
        return [str(float(val1[0]) + float(val2[0]))]
    except Exception:
        return None

# Route to serve the dashboard UI
@app.route('/', methods=['GET'])
def serve_dashboard():
    """Serve the dashboard HTML page with Firebase config"""
    with open(os.path.join(code_dir, 'firebaseConfig.json'), 'r') as f:
        firebase_config = json.load(f)
    # data = get_all_summarised_data_as_df().to_dict(orient='records')
    # logging.info(f"Serving dashboard with {data}.")
    return render_template('index.html', firebase_config=firebase_config)

app.route('/authenticate/<main_source>/<session_id>', methods=['POST'])(authenticate)
app.route('/authenticate/<main_source>/<session_id>/', methods=['POST'])(authenticate)
app.route('/login_check', methods=['POST'])(login_check)

@app.route('/login', defaults={'main_source': 'FALSE', 'session_id': None}, methods=['GET'])
@app.route('/login/', defaults={'main_source': 'FALSE', 'session_id': None}, methods=['GET'])
@app.route('/login/<main_source>/<session_id>', methods=['GET'])
@app.route('/login/<main_source>/<session_id>/', methods=['GET'])
def login(main_source, session_id):
    # main_source can be 'TRUE' or 'FALSE' | it refers to wheter the source of the request is main (api) or not (e.g. web dashboard)
    with open(os.path.join(code_dir, 'firebaseConfig.json'), 'r') as f:
        firebaseConfig = json.load(f)
    if main_source != 'TRUE':
        main_source = 'FALSE'
    if not session_id:
        session_id = str(uuid.uuid4())
    login_url = url_for('authenticate', session_id=session_id, main_source=main_source)
    return render_template('login.html', firebase_config=firebaseConfig, login_url=login_url, session_id=session_id, main_source=main_source)

@app.route('/register_user', methods=['GET'])
def register_user_page():
    """Serve the registration page for new users"""
    with open(os.path.join(code_dir, 'firebaseConfig.json'), 'r') as f:
        firebase_config = json.load(f)
    return render_template('register.html', firebase_config=firebase_config)

# Inform user when attempting to register with an existing account
@app.route('/already_registered', methods=['GET'])
def already_registered_page():
    return render_template('already_registered.html')

# Serve page for uploading receipts via the web dashboard
@app.route('/upload_page', methods=['GET'])
def upload_page():
    with open(os.path.join(code_dir, 'firebaseConfig.json'), 'r') as f:
        firebase_config = json.load(f)
    return render_template('upload.html', firebase_config=firebase_config)

# Serve simple chat interface
@app.route('/chat_page', methods=['GET'])
def chat_page():
    with open(os.path.join(code_dir, 'firebaseConfig.json'), 'r') as f:
        firebase_config = json.load(f)
    return render_template('chat.html', firebase_config=firebase_config)

# Route providing aggregated summary for a specific user
@app.route('/summary', methods=['GET'])
def summary():
    user_id = request.args.get('user_id')
    if not user_id:
        return jsonify({'error': 'Missing user_id'}), 400
    user_doc = get_user_document(user_id)
    if not user_doc or 'auth' not in user_doc:
        return jsonify({'error': 'Unauthorized'}), 401

    df = get_all_summarised_data_as_df(USERNAME=user_id)
    if df.empty:
        return jsonify({'error': 'No data found'}), 404

    total_spend = df['total'].sum()
    avg_daily_spend = total_spend / df['date'].nunique()

    category_totals = df.groupby('category')['total'].sum().to_dict()
    top_category = max(category_totals.items(), key=lambda x: x[1])

    expense_by_category = {
        'labels': list(category_totals.keys()),
        'values': [round(v, 2) for v in category_totals.values()]
    }

    df['weekday'] = pd.to_datetime(df['date']).dt.day_name()
    weekly = df.groupby('weekday')['total'].sum().to_dict()
    ordered_week = [calendar.day_name[i] for i in range(7)]
    weekly_spending = {
        'labels': ordered_week,
        'values': [round(weekly.get(day, 0.0), 2) for day in ordered_week]
    }

    return jsonify({
        'total_monthly_spend': round(total_spend, 2),
        'average_daily_spend': round(avg_daily_spend, 2),
        'top_category': top_category[0],
        'top_category_total': round(top_category[1], 2),
        'expense_by_category': expense_by_category,
        'weekly_spending': weekly_spending
    })

# def image_to_base64(image_path):
#     with Image.open(image_path) as img:
#         buffered = BytesIO()
#         if img.mode == 'RGBA':
#             img = img.convert('RGB')
#         img.save(buffered, format="JPEG")
#         return base64.b64encode(buffered.getvalue()).decode("utf-8")

@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint for monitoring and load balancers"""
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.now().isoformat(),
        'service': 'spendify-api'
    }), 200

@app.route('/register', methods=['POST'])
def register():
    payload = request.get_json() or {}
    source = payload.get('source')
    if source in ['auth', 'decoded_token']:
        return jsonify({'error': 'Invalid source for registration'}), 400
    identifier = payload.get('identifier')
    primary_id = payload.get('primary_id') or identifier
    logging.info(f"Register request: source={source}, identifier={identifier}, primary_id={primary_id}")
    if not source or not identifier:
        return jsonify({'error': 'Missing source or identifier'}), 400
    existing_doc = get_user_document(primary_id)
    if existing_doc and 'auth' in existing_doc:
        logging.warning(f"Registration attempt for existing user {primary_id}")
        return jsonify({'status': 'already_registered'}), 409
    try:
        session_id = create_user(primary_id, source, identifier)
        logging.info(f"User created/updated: {primary_id} -> {source}:{identifier}")
        return jsonify({'status': 'registered', 'primary_id': primary_id, 'session_id': session_id}), 200
    except Exception as e:
        logging.exception(f"Error in create_user for primary_id {primary_id}")
        return jsonify({'error': 'Failed to create user in database', 'details': str(e)}), 500

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

@app.route('/get_user', methods=['GET'])
def get_user():
    primary_id = request.args.get('primary_id')
    if not primary_id:
        return jsonify({'error': 'Missing primary_id'}), 400
    user_doc = get_user_document(primary_id)
    if not user_doc:
        return jsonify({'error': 'not found'}), 404
    return jsonify(user_doc), 200

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
        print(f"Processing file: {save_path}")
        document_dict, document_proto = extract_receipt_data(save_path)
        logging.info(f"GCP returned document with {len(document_proto.entities)} entities")

        # Sanitize document_dict to ensure Firestore compatibility
        try:
            # Convert non-serializable parts to strings or standard Python dicts/lists.
            # default=str helps convert types like datetime objects to strings if they are not already.
            json_string = json.dumps(document_dict, default=str)
            sanitized_document_dict = json.loads(json_string)
        except Exception as e:
            logging.error(f"Error sanitizing document_dict for Firestore using json.dumps/loads: {e}. Original type: {type(document_dict)}. Falling back to a basic error structure.")
            # Fallback to a simple error structure to avoid passing potentially complex/problematic original dict
            sanitized_document_dict = {
                "error_message": "Failed to sanitize document_dict for Firestore.",
                "original_type": str(type(document_dict)),
                "exception_details": str(e)
            }

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
    def replace_nested_lists_with_json(obj):
            if isinstance(obj, list):
                new_list = []
                for item in obj:
                    if isinstance(item, list):
                        # If the item is a list, replace with its JSON string
                        new_list.append(json.dumps(item))
                    elif isinstance(item, dict):
                        new_list.append(replace_nested_lists_with_json(item))
                    else:
                        new_list.append(item)
                return new_list
            elif isinstance(obj, dict):
                # For each dict value, check for lists, dicts, or other types
                return {k: replace_nested_lists_with_json(v) for k, v in obj.items()}
            else:
                return obj
    sanitized_payload = replace_nested_lists_with_json(sanitized_document_dict)
    try:
        save_raw_data(date_str, session_id, sanitized_payload, timestamp) # Use sanitized_payload
    except Exception as e:
        logging.error(f"Error saving raw data: {e}")
        save_raw_data(date_str, session_id, {
            "error": "Failed to save raw data",
            "details": str(e),
            "summary": str(type(e)),
            "original_keys": list(sanitized_payload.keys()),
            "needed_values": grouped
        }, timestamp)
    logging.info("Saving receipt data under DATA/RECEIPTS")
    save_receipt_data(date_str, session_id, grouped, timestamp)

    # # === CLASSIFICATION & SUMMARY SECTION ===
    # logging.info("Converting image to base64 for classification")
    # image_b64 = image_to_base64(save_path)

    # 1. Extract line_items (flexible key search)
    line_items = (
        grouped.get("line_item")
        or grouped.get("item")
        or grouped.get("ITEM")
        or []
    )
    if not line_items:
        possible_item_keys = [k for k in grouped.keys() if "item" in k.lower()]
        if possible_item_keys:
            line_items = grouped[possible_item_keys[0]]

    # 2. Extract receipt total (try a few key names, fallback to "0")
    
    net_amount = grouped.get("net_amount", ["0"])
    total_tax_amount = grouped.get("total_tax_amount", ["0"])
    total_amount = (
        grouped.get("total_amount") or
        safe_sum(net_amount, total_tax_amount) or
        # grouped.get("net_amount")
        ["0"]
    )

    total_candidates = {"total_amount": total_amount, "net_amount": net_amount, "total_tax_amount": total_tax_amount}

    # If it's a list, take the first value
    receipt_total_value = {k: (v[0] if isinstance(v, list) else v) for k, v in total_candidates.items()}

    if line_items:
        logging.info(f"Classifying {len(line_items)} items for session {session_id} with totals {receipt_total_value}")
        try:
            adk = ADKClient(CLASSIFICATION_URL, "receipt_classifier", user_id="user", session_id=session_id)
            prompt_txt = json.dumps({
                "line_items": line_items,
                "receipt_total_value": receipt_total_value,
                "grouped": grouped
            }, indent=2)
            # Create a new session (POST)
            session_resp = adk.get_or_create_session(method="POST", custom_session=True)
            if session_resp and 'id' in session_resp:
                session_id = session_resp['id']
                # print(f"Session created: {session_id}")
            else:
                pass # Handle session creation failure if needed | NOTE-TODO
            events = adk.run_sse(session_id, prompt_txt)
            logging.info(f"Received {len(events)} events from ADK classification for session {session_id}")
            '''
            if events is not None:
                # Extract JSON only if you expect a structured response
                classified_data = adk.extract_json_from_events(events)
                logging.info(f"Extracted classified data: {classified_data}")
                if classified_data:
                    if "result" in classified_data:
                        if classified_data["result"] == "success":
                            logging.info("Classification is said to be successful.")
                            if "data" in classified_data:
                                submission_data = classified_data["data"]
                                # logging.info("Final submission data:\n", submission_data)
                                logging.info(type(submission_data))
                                submission_data = json.loads(submission_data) if isinstance(submission_data, str) else submission_data
                                # save_summarised_data(date_str, session_id, submission_data, timestamp)
                            else:
                                logging.error(f"No 'data' field in classification response.")
                        else:
                            logging.error(f"Error from classification response: {classified_data.get('message', 'Unknown error')}")
                else:
                    logging.error("No structured JSON data found. Events received:")
                    # print(json.dumps(events, indent=2))
            else:
                logging.error("No events received.")
            '''
            logging.info("Classification completed, Summarised Data should be saved now.")
        except Exception as e:
            logging.exception(f"Classification failed for session {session_id}: {e}")
    else:
        logging.warning(f"No 'item' candidates found for classification for session {session_id}")

    logging.info(f"Completed processing for session {session_id}")
    return jsonify({'status': 'processing', 'session_id': session_id}), 200

@app.route('/get_data', methods=['GET'])
def get_data():
    # If Username is provided, return summarised data for that user
    username = request.args.get('username') or None
    df = get_all_summarised_data_as_df(USERNAME=username)
    if df.empty:
        logging.warning("No summarised data found")
        return jsonify({'error': 'No data found'}), 404
    logging.info(f"Returning summarised data for {len(df)} records")
    return jsonify(df.to_dict(orient='records'))

# # Simple chat endpoint using Gemini if available
# @app.route('/chat', methods=['POST'])
# def chat():
#     data = request.get_json() or {}
#     message = data.get('message', '')
#     if not message:
#         return jsonify({'error': 'No message provided'}), 400
#     reply = 'Hello! Ask me about your receipts.'
#     api_key = os.getenv('GEMINI_API_KEY')
#     if api_key:
#         try:
#             import google.generativeai as genai
#             genai.configure(api_key=api_key)
#             model = genai.GenerativeModel('gemini-pro')
#             resp = model.generate_content(message)
#             if resp.candidates:
#                 reply = resp.candidates[0].content.parts[0].text.strip()
#         except Exception as e:
#             logging.error(f'Gemini API error: {e}')
#     return jsonify({'response': reply})

if __name__ == '__main__':
    # This will only run when called directly (for development/testing)
    # In production, Gunicorn will import the 'app' object directly
    logging.info(f"🌐 Starting API on port {API_PORT} (Development Mode)")
    app.run(host='0.0.0.0', port=API_PORT)