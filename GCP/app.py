# NOTE: TODO - This needs to be Edited.
from flask import Flask, request, jsonify
from google.cloud import documentai_v1 as documentai
from google.api_core.client_options import ClientOptions
import os
from google.cloud import firestore

app = Flask(__name__)

@app.route('/process-receipt', methods=['POST'])
def process_receipt():
    if 'image' not in request.files:
        return jsonify({"error": "No image file found in the request"}), 400

    file = request.files['image']

    if file.filename == '':
        return jsonify({"error": "No selected file"}), 400

    if file:
        # At this point, you have the image file object.
        # You can access its content using file.read()
        # or save it to a temporary location.
        # Further processing with GCP Document AI will go here.
        image_data = file.read()
        mime_type = file.mimetype

        # TODO: Replace with your actual GCP project ID, location, and processor ID
        project_id = os.environ.get("GCP_PROJECT_ID", "your-gcp-project-id")
        location = os.environ.get("GCP_LOCATION", "us") # e.g., "us"
        processor_id = os.environ.get("GCP_PROCESSOR_ID", "your-processor-id") # Create a "Receipt-Parser" processor in Document AI

        opts = ClientOptions(api_endpoint=f"{location}-documentai.googleapis.com")

        client = documentai.DocumentProcessorServiceClient(client_options=opts)

        # The full resource name of the processor
        # e.g.: projects/project_id/locations/location/processors/processor_id
        name = client.processor_path(project_id, location, processor_id)

        # Read the file into memory
        document = documentai.RawDocument(content=image_data, mime_type=mime_type)

        # Configure the process request
        request_gcp = documentai.ProcessRequest(name=name, raw_document=document)

        try:
            result = client.process_document(request=request_gcp)
            document = result.document

            # Print the full result for now
            print(result.document)

            # Save to Firestore
            db = firestore.Client(project=project_id)
            # Create a new document in a collection named 'receipts'
            # You might want to use a more structured approach to extract
            # specific fields from the document object before saving.
            # For demonstration, saving a simplified representation.
            # You'll need to parse result.document to get structured data.
            # Example: Extracting text and entities
            receipt_data = {
                "filename": file.filename,
                "text": document.text,
                "entities": [{"type": entity.type, "mention_text": entity.mention_text} for entity in document.entities]
                # Add more fields as you extract them from result.document
            }
            doc_ref = db.collection('receipts').add(receipt_data)

            print(f"Document data saved to Firestore with ID: {doc_ref[1].id}")

            return jsonify({"message": "Image processed by Document AI", "filename": file.filename, "result_summary": "Check server logs for full output"}), 200
        except Exception as e:
            print(f"Error processing document with Document AI: {e}")
            return jsonify({"error": f"Error processing document with Document AI: {e}"}), 500
    return jsonify({"error": "Unexpected error processing the file"}), 500

if __name__ == '__main__':
    # In a production environment, use a more robust server like Gunicorn or uWSGI
    app.run(debug=True)