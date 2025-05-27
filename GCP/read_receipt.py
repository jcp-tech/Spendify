# pip install --upgrade google-cloud-documentai
import os # , json
from urllib.parse import urlparse
from dotenv import load_dotenv
from google.cloud import documentai_v1 as documentai
from google.protobuf.json_format import MessageToDict

load_dotenv()

# === CONFIGURATION ===
service_account_file = os.getenv('GOOGLE_APPLICATION_CREDENTIALS')
processor_url = os.getenv('DOCUMENT_AI_PROCESSOR_URL')
file_path = r"C:\Users\JonathanChackoPattas\OneDrive - Maritime Support Solutions\Desktop\Class Notes\Seneca\Semester 2\AIG200 - Capstone Project\Code\ignore\large-receipt-image-dataset-SRD\1000-receipt.jpg"
mime_type = "image/jpeg"
# ======================

def parse_processor_url(url):
    parts = urlparse(url).path.strip("/").split('/')
    print(f"🔗 Parsed URL parts: {parts}")
    return {
        "project_id": parts[2],
        "location": parts[4],
        "processor_id": parts[6].split(":")[0]  # remove :process
    }

def set_gc_credentials():
    if os.path.exists(service_account_file):
        os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = service_account_file
        print("✅ Google Cloud credentials set.")
    else:
        raise FileNotFoundError(f"❌ Service account file not found at: {service_account_file}")

def process_receipt(file_path, project_id, location, processor_id, mime_type="image/jpeg"):
    print(f"📄 Processing receipt from: {file_path}")
    print(f"Project ID: {project_id}, Location: {location}, Processor ID: {processor_id}, MIME Type: {mime_type}")

    client = documentai.DocumentProcessorServiceClient()
    name = f"projects/{project_id}/locations/{location}/processors/{processor_id}"
    print(f"📤 Sending to processor: {name}")

    with open(file_path, "rb") as f:
        image_data = f.read()
    raw_document = documentai.RawDocument(content=image_data, mime_type=mime_type)
    request = documentai.ProcessRequest(name=name, raw_document=raw_document)
    result = client.process_document(request=request) # Going Wrong Here.
    document = result.document

    # print("\n=== FULL TEXT ===")
    # print(document.text)

    print("\n=== EXTRACTED ENTITIES ===")
    for entity in document.entities:
        print(f"{entity.type_:<20}: {entity.mention_text}") #  (confidence: {entity.confidence:.2f})

    # print("\n=== RAW JSON OUTPUT ===")
    # document_dict = MessageToDict(result._pb.document, preserving_proto_field_name=True)
    # print(json.dumps(document_dict, indent=2))
    # with open("parsed_receipt_output.json", "w") as f:
    #     json.dump(document_dict, f, indent=2)

    return document

# === MAIN EXECUTION ===
if __name__ == '__main__':
    set_gc_credentials()
    config = parse_processor_url(processor_url)
    process_receipt(
        file_path=file_path,
        project_id=config["project_id"],
        location=config["location"],
        processor_id=config["processor_id"],
        mime_type=mime_type
    )