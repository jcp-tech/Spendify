from flask import Flask, request, jsonify
from receipt_classifier import init_classifier, run

app = Flask(__name__)

@app.route("/classify", methods=["POST"])
def classify():
    data = request.get_json()
    items = data.get("items", [])
    optimize = data.get("optimize", True)
    num_workers = data.get("num_workers", 3)

    if not items or not isinstance(items, list):
        return jsonify({"error": "Invalid or missing 'items' list."}), 400

    results = run(
        items,
        optimize=optimize,
        num_workers=num_workers
    )
    return jsonify(results)

if __name__ == "__main__":
    import sys
    if len(sys.argv) != 3:
        print("Usage: python llm_api.py <main_model> <fallback_model>")
        exit(1)

    # ✅ Initialize model once at server start
    init_classifier(primary=sys.argv[1], fallback=sys.argv[2])
    app.run(host="0.0.0.0", port=5000, debug=True)