"""
Receipt Classification Generator Agent

This agent generates the initial Classification before grouping.
"""

from google.adk.agents.llm_agent import LlmAgent
from typing import List, Dict, Any
from pydantic import BaseModel, Field

### INPUT SCHEMA DEFINITION ###
class ReceiptTotalValue(BaseModel):
    total_amount: str = Field(..., description="Total amount shown on the receipt.")
    net_amount: str = Field(..., description="Net amount after discounts and before tax.")
    total_tax_amount: str = Field(..., description="Total tax amount applied to the receipt.")
# class GroupedFields(BaseModel):
#     net_amount: List[str]
#     total_amount: List[str]
#     total_tax_amount: List[str]
#     currency: List[str]
#     purchase_time: List[str]
#     receipt_date: List[str]
#     supplier_name: List[str]
#     supplier_phone: List[str]
#     supplier_address: List[str]
#     line_item: List[str]
#     supplier_city: List[str]
class ReceiptClassificationInput(BaseModel):
    line_items: List[str] = Field(..., description="List of line item strings from the receipt.")
    receipt_total_value: ReceiptTotalValue = Field(..., description="Total, net, and tax values from the receipt.")
    grouped: Dict[str, Any] = Field(..., description="Dictionary of grouped fields extracted from the receipt. Raw, may have any keys.") # Field(..., description="Grouped fields extracted from the receipt, as lists.")

### OUTPUT SCHEMA DEFINITION ###
class ReceiptClassificationBreakdown(BaseModel):
    item: str = Field(..., description="The full original item string, unmodified.")
    quantity: str = Field(..., description="The quantity from the item string.")
    price: str = Field(..., description="The price from the item string.")
    category: str = Field(..., description="The assigned category for the item.")
class ReceiptClassificationOutput(BaseModel):
    classified: List[ReceiptClassificationBreakdown] = Field(..., description="List of classified receipt items.") # List[Dict[str, Any]] = Field(..., description="List of classified receipt items.")
    total_values_dict: ReceiptTotalValue = Field(..., description="Total, net, and tax values from the receipt, as a dictionary. Raw, may have any keys.") # Dict[str, Any] = Field(..., description="Total, net, and tax values from the receipt, as a dictionary. Raw, may have any keys.")
# Constants
GEMINI_MODEL = "gemini-2.0-flash" # "gemini-2.5-flash"

# Define the Initial Classifier Agent
initial_classifier = LlmAgent(
    name="InitialClassifier",
    model=GEMINI_MODEL,
    instruction="""
    You are a Receipt Classifier.
    You are a receipt classification agent.

    Task:
    Given a list of receipt line items (each with quantity, item name, and price at the end), assign each item to ONE of these categories ONLY:
    ["Groceries", "Fast Food", "Electronics", "Apparel", "Personal Care", "Others"]

    - Use only the item name and context to decide the best category.
    - If an item doesn't clearly fit a category, assign it to "Others".
    - Do not group, sum, or explain—just classify.
    - If a line_item doesn't have a quantity default it to "1"
    - Identify all the line_items which doesnt have a price and see what is the pending cost (from subtracting the totals) then split the pending cost equally among the items without price
    - NOTE: That when returning "items" do not include the quantity and price, just the item name (VERY IMPORTANT)
    
    Output:
    Return a valid JSON array (no extra text). Each element should have:
    "item": The item string without quantity and price.
    "quantity": The quantity from the item string.
    "price": The price from the item string.
    "category": The assigned category.

    Input Format:
    {
        "line_items": ["1 Apple 2.50", "1 Fren Onion Soup 5.95", "2 Bread 1.05"],
        "receipt_total_value": {
            "total_amount": "9.50",
            "net_amount": "9.50",
            "total_tax_amount": "0.00"
        },
        "grouped": {
            ... # Unknown keys, raw OCR data
        }
    }
    Example Output:
    {
        "classified": [
            {"item": "Apple","quantity": "1", "price":"2.50","category": "Groceries"},
            {"item": "Fren Onion Soup","quantity": "1", "price":"5.95","category": "Fast Food"},
            {"item": "Bread","quantity": "2", "price":"1.05","category": "Groceries"}
        ],
        "receipt_total_value": {
            "total_amount": "9.50",
            "net_amount": "9.50",
            "total_tax_amount": "0.00"
        }
    }
    """,
    description="Generates the initial Classification JSON to start the refinement process",
    input_schema=ReceiptClassificationInput,
    output_schema=ReceiptClassificationOutput,
    output_key="stage_init_classification", 
)
