# classification_response/tools.py
import json
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
    # Simulate success:
    return {"result": "success", "message": "Data saved to Firebase.", "data": json.dumps(data)}
