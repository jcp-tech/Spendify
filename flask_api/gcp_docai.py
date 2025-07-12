import os
import logging
from urllib.parse import urlparse
from dotenv import load_dotenv
from google.cloud import documentai_v1 as documentai
from google.protobuf.json_format import MessageToDict

# Setup logging
logging.basicConfig(level=logging.INFO, format='[%(asctime)s] %(levelname)s: %(message)s')

load_dotenv()

def parse_processor_url(url):
    logging.info(f"Parsing processor URL: {url}")
    parts = urlparse(url).path.strip('/').split('/')
    config = {
        'project_id': parts[2],
        'location': parts[4],
        'processor_id': parts[6].split(':')[0]
    }
    logging.info(f"Parsed config: {config}")
    return config

def set_gc_credentials():
    service_account_file = os.getenv('GOOGLE_APPLICATION_PATH')
    logging.info(f"Setting Google Cloud credentials from: {service_account_file}")
    if not service_account_file or not os.path.exists(service_account_file):
        code_current_dir = os.path.dirname(os.path.abspath(__file__))
        msg = f"Service account file not found at: {service_account_file}"
        logging.error(msg)
        cred_path = os.path.join(code_current_dir, 'firebase_credentials.json')
        if not os.path.exists(cred_path):
            logging.error(f"Firebase credentials file not found at: {cred_path}")
            raise FileNotFoundError(msg)
    os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = service_account_file
    logging.info("Google Cloud credentials set")

def extract_receipt_data(file_path, mime_type='image/jpeg'):
    set_gc_credentials()
    processor_url = os.getenv('DOCUMENT_AI_PROCESSOR_URL')
    if not processor_url:
        msg = "DOCUMENT_AI_PROCESSOR_URL environment variable is not set"
        logging.error(msg)
        raise ValueError(msg)
    config = parse_processor_url(processor_url)

    client = documentai.DocumentProcessorServiceClient()
    name = f"projects/{config['project_id']}/locations/{config['location']}/processors/{config['processor_id']}"
    logging.info(f"Processor name: {name}")

    with open(file_path, 'rb') as f:
        image_data = f.read()
    logging.info(f"Read image data ({len(image_data)} bytes) from {file_path}")

    raw_document = documentai.RawDocument(content=image_data, mime_type=mime_type)
    request = documentai.ProcessRequest(name=name, raw_document=raw_document)
    logging.info("Sending request to Document AI")
    result = client.process_document(request=request)
    logging.info("Received response from Document AI")

    document_dict = MessageToDict(result._pb.document, preserving_proto_field_name=True)
    logging.info("Converted Document AI response to dict")

    return document_dict, result.document
