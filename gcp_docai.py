"""
PIP installs:
pip install --upgrade google-cloud-documentai python-dotenv
"""

import os
from urllib.parse import urlparse
from dotenv import load_dotenv
from google.cloud import documentai_v1 as documentai
from google.protobuf.json_format import MessageToDict

load_dotenv()

def parse_processor_url(url):
    parts = urlparse(url).path.strip('/').split('/')
    return {
        'project_id': parts[2],
        'location': parts[4],
        'processor_id': parts[6].split(':')[0]
    }

def set_gc_credentials():
    service_account_file = os.getenv('GOOGLE_APPLICATION_PATH')
    if not service_account_file or not os.path.exists(service_account_file):
        raise FileNotFoundError(f"Service account file not found at: {service_account_file}")
    os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = service_account_file

def extract_receipt_data(file_path, mime_type='image/jpeg'):
    set_gc_credentials()
    processor_url = os.getenv('DOCUMENT_AI_PROCESSOR_URL')
    config = parse_processor_url(processor_url)
    client = documentai.DocumentProcessorServiceClient()
    name = f"projects/{config['project_id']}/locations/{config['location']}/processors/{config['processor_id']}"
    with open(file_path, 'rb') as f:
        image_data = f.read()
    raw_document = documentai.RawDocument(content=image_data, mime_type=mime_type)
    request = documentai.ProcessRequest(name=name, raw_document=raw_document)
    result = client.process_document(request=request)
    document_dict = MessageToDict(result._pb.document, preserving_proto_field_name=True)
    # Return both parsed dict and original Document for entity iteration
    return document_dict, result.document
