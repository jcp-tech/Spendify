"""
Receipt Classification Grouping Agent
"""

# classifier_grouper/agent.py
from google.adk.agents.llm_agent import LlmAgent
from typing import List, Dict, Any
from pydantic import BaseModel, Field

# Constants
GEMINI_MODEL = "gemini-2.0-flash"

### OUTPUT SCHEMA DEFINITION ###
class ReceiptGroupingBreakdown(BaseModel):
    category: str = Field(..., description="The category of the items")
    items: List[str] = Field(..., description="A list of item names in that category")
    total_price: str = Field(..., description="The total price of all items in that category")
class ReceiptGroupingOutput(BaseModel):
    grouped: List[ReceiptGroupingBreakdown] = Field(..., description="List of grouped receipt items.")

# Define the Initial Classifier Agent
grouping_classification = LlmAgent(
    name="grouping_classification",
    model=GEMINI_MODEL,
    instruction="""
    Task:
    You are given a Classification JSON with receipt items you need to group by category

    Output:
    Return a valid JSON array (no extra text). Each element should have:
    "category": The category of the items
    "items": A list of item names in that category
    "total_price": The total price of all items in that category

    Input Format:
    {
        "classified": [
            {"item": "Apple","quantity": "1", "price":"2.50","category": "Groceries"},
            {"item": "Fren Onion Soup","quantity": "1", "price":"5.95","category": "Fast Food"},
            {"item": "Bread","quantity": "2", "price":"1.05","category": "Groceries"}
        ],
        "total_values_dict": {
            "total_amount": "9.50",
            "net_amount": "9.50",
            "total_tax_amount": "0.00"
        }
    } # NOTE: The "classified" field is the output from the initial classifier agent, which contains the classified items with their categories, That is the Key you need to use to group the items.

    Example Output:
    [
        {
            "category": "Groceries", "items": ["Apple", "Bread"], "total_price": "3.55"
        },
        {
            "category": "Fast Food", "items": ["Fren Onion Soup"], "total_price": "5.95"
        }
    ]

    
    The Input Data is in
    {stage_init_classification}
    """,
    description="Generates the Grouping JSON",
    output_schema=ReceiptGroupingOutput,
    output_key="grouped_classification",
)