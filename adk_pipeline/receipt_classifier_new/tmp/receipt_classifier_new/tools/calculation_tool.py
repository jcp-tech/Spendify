from typing import Any, Dict, List
from google.adk.tools.tool_context import ToolContext

def calculate_final_total(
    data: List[Dict[str, Any]]
) -> Dict[str, Any]:
    """
    Calculates the sum of all total_price values from grouped categories.

    Args:
        data: List of dicts, where each dict is a category containing a
              "total_price" key.

    Returns:
        A dictionary containing the result of the calculation.
    """
    final_total = 0.0
    if not isinstance(data, list):
        return {"result": "error", "message": "Invalid input: data must be a list of categories."}

    for category_data in data:
        if not isinstance(category_data, dict):
            return {"result": "error", "message": f"Invalid item in list: {category_data}"}
        try:
            price_str = category_data.get("total_price", "0")
            final_total += float(price_str)
        except (ValueError, KeyError) as e:
            return {"result": "error", "message": f"Error processing item {category_data}: {e}"}

    return {
        "result": "success",
        "final_total": round(final_total, 2),
        "message": f"Successfully calculated final total: {final_total:.2f}"
    }
