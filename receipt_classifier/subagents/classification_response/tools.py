# classification_response/tools.py
from typing import Dict, Any
from google.adk.tools.tool_context import ToolContext

def save_to_firebase(
    data: Dict[str, Any],
    tool_context: ToolContext
) -> Dict[str, Any]:
    """
    Save the provided receipt summary data to Firebase.

    Args:
        data: The final JSON object to be stored.
        tool_context: Tool context (optional for session actions).

    Returns:
        Dict with "result" key ("success" or "error") and optional "message".
    """
    # (Your firebase logic here...)
    # e.g., firebase_admin.firestore.client().collection(...).add(data)
    print("Saving to Firebase:", data)
    for key, value in data.items():
        print(f"{key}: {value}")
    print("Data saved successfully.")
    # Simulate success:
    return {"result": "success", "message": "Data saved to Firebase."}
