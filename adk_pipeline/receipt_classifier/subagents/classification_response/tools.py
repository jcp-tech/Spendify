# classification_response/tools.py
from google.adk.tools.tool_context import ToolContext
from pydantic import BaseModel, Field
from typing import Dict, Any, List
try:
    from .firebase_store import save_summarised_data  # Adjust import based on your project structure
except Exception as e:
    from firebase_store import save_summarised_data
from datetime import datetime
import json

class Category(BaseModel):
    category: str
    items: List[str]
    total_price: str   # Or float if you want to force numeric (see below)
class FinalOutputSchema(BaseModel):
    categories: List[Category] = Field(..., description="List of item categories with their details.")

def save_to_firebase(
    data: FinalOutputSchema,
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
    dt = datetime.now()
    session_id = tool_context._invocation_context.session.id
    print("Saving to Firebase:", data)
    save_summarised_data(dt.strftime("%Y-%m-%d"), session_id, data, dt)
    return {"result": "success", "message": "Data saved to Firebase.", "data": json.dumps(data)}
