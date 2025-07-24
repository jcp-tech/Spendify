import os, logging, sys, json, base64
import uuid
from flask import Flask, request, jsonify, send_from_directory, render_template, url_for
from dotenv import load_dotenv
from gcp_docai import extract_receipt_data #, set_gc_credentials
from firebase_store import (
    get_primary_id, create_user,
    save_session_meta, save_raw_data, save_receipt_data, save_summarised_data,
    authenticate, login_check, get_all_summarised_data_as_df, get_user_document
)
from io import BytesIO
from PIL import Image
from gcp_adk_classification import ADKClient
from datetime import datetime
from flask_cors import CORS
import calendar
import pandas as pd

code_dir = os.path.dirname(os.path.abspath(__file__))
DASHBOARD_DIR = os.path.join(code_dir, "dashboard") # Directory to serve the dashboard HTML from

# Load ENV
load_dotenv()
API_PORT = int(os.getenv('API_PORT', 8080))
CLASSIFICATION_URL = os.getenv('CLASSIFICATION_URL', 'http://localhost:8000')

# Setup logging
logging.basicConfig(level=logging.INFO, format='[%(asctime)s] %(levelname)s: %(message)s')
app = Flask(__name__, template_folder=DASHBOARD_DIR)
CORS(app)  # This allows all origins; restrict for production!

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

    session_id = create_user(primary_id, source, identifier)
    logging.info(f"User created/updated: {primary_id} -> {source}:{identifier}")
    return jsonify({'status': 'registered', 'primary_id': primary_id, 'session_id': session_id}), 200

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
def upload_receipt():
    """Save uploaded receipt image and session metadata."""
    file = request.files.get('file')
    session_id = request.form.get('session_id') or str(uuid.uuid4())
    identifier = request.form.get('identifier')
    source = request.form.get('source')
    timestamp = request.form.get('timestamp') or datetime.utcnow().isoformat()

    if not file or not identifier or not source:
        return jsonify({'error': 'Missing required fields'}), 400

    uploads_dir = os.path.join(code_dir, 'uploads')
    os.makedirs(uploads_dir, exist_ok=True)
    ext = os.path.splitext(file.filename)[1] or '.jpg'
    save_path = os.path.join(uploads_dir, f"{session_id}{ext}")
    file.save(save_path)

    save_session_meta(session_id, timestamp, identifier, source)

    logging.info(f"Stored upload at {save_path} for {identifier}")

    return jsonify({'status': 'uploaded', 'session_id': session_id})

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