"""
Tools for LinkedIn Post Reviewer Agent

This module provides tools for analyzing and validating LinkedIn posts.
"""

from typing import Any, Dict, List

from google.adk.tools.tool_context import ToolContext

def calculate_final_total(
        data: List[Dict[str, Any]], # list,
        tool_context: ToolContext
    ) -> Dict[str, Any]:
    """
    Tool to calculate the final total from a list of dictionaries, where each dictionary
    represents a category with its items and total price.
    Updates the 'calculation_status' in the state based on the success of the calculation.

    Args:
        data (List[Dict]): A list of category dicts. Each has:
            - "category": (str)
            - "items": (List[str])
            - "total_price": (str)
        tool_context: ToolContext for session state.

    Returns:
        Dict[str, Any]: {
            "result": 'success' or 'error',
            "final_total": float,
            "message": str
        }
    """
    print("\n----------- TOOL DEBUG -----------")
    print(f"Calculating final total for data: {data}")
    print("----------------------------------\n")

    final_total = 0.0
    for category_data in data:
        try:
            # Convert the total_price string to a float and add it to the final_total
            final_total += float(category_data["total_price"])
        except (ValueError, KeyError) as e:
            tool_context.state["calculation_status"] = "error"
            return {
                "result": "error",
                "message": f"Error processing item: {category_data}. Invalid 'total_price' or missing key. Details: {e}"
            }
    
    tool_context.state["calculation_status"] = "success"
    return {
        "result": "success",
        "final_total": final_total,
        "message": f"Successfully calculated final total: {final_total}"
    }


def exit_function(
    final_total: float,
    data: Dict[str, Any],
    tool_context: ToolContext
) -> Dict[str, Any]:
    """
    Compares final_total to receipt totals and exits if matching.

    Args:
        final_total: The computed total value from calculate_final_total.
        data: The initial classification dict or relevant context (should include total_amount/net_amount).
        tool_context: Context for tool execution

    Returns:
        Dict with 'status' and 'details' keys.
    """
    # Adapt to your actual key structure
    receipt_totals = None

    if "stage_init_classifier" in data:
        totals_dict = data["stage_init_classifier"].get("total_values_dict", {})
    elif "receipt_total_value" in data:
        totals_dict = data["receipt_total_value"]
    elif "total_values_dict" in data:
        totals_dict = data["total_values_dict"]
    else:
        return {
            "status": 0,
            "details": f"Could not find receipt totals in the provided data => {data}"
        }

    try:
        total_amount = float(totals_dict.get("total_amount", "-99999"))
        net_amount = float(totals_dict.get("net_amount", "-99999"))
    except Exception as e:
        return {
            "status": 0,
            "details": f"Could not parse receipt totals: {e}"
        }

    # Check for match (allow for floating-point rounding)
    if abs(final_total - total_amount) < 0.01:
        tool_context.actions.escalate = True
        return {
            "status": 1,
            "details": "Computed total matches the receipt total. Classification is valid. Exiting the refinement loop."
        }
    elif abs(final_total - net_amount) < 0.01:
        tool_context.actions.escalate = True
        return {
            "status": 1,
            "details": "Computed total matches the net amount (excluding tax). Classification is valid. Exiting the refinement loop."
        }
    else:
        return {
            "status": 0,
            "details": f"Computed total is {final_total}, but expected {total_amount} or {net_amount}. Please check the following categories and their prices for inconsistencies."
        }