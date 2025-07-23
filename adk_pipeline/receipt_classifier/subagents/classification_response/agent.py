"""
Receipt Classification Response Agent
"""

# response_agent/agent.py
from google.adk.agents.llm_agent import LlmAgent
from .tools import save_to_firebase

GEMINI_MODEL = "gemini-2.0-flash"

response_agent = LlmAgent(
    name="response_agent",
    model=GEMINI_MODEL,
    instruction="""
You are a Receipt Classification Finalizer Agent.

Given the validated receipt classification breakdown, perform the following steps:
1. Generate a summary JSON as described below.
2. Call the `save_to_firebase` tool, passing the summary from `grouped_classification` variable to it as the 'data' argument.
3. Output ONLY the result from the `save_to_firebase` tool.

## Summary JSON Fields:
- summary: A concise description of the classification result.
- categories: The list of categories and their items (from grouped_classification).
- final_total: The computed final total.
- status: 1 if totals matched, 0 if not.
- timestamp: Use the provided timestamp if available.
- notes: Any warnings or info.



## Example Input to `save_to_firebase` tool (VERY STRICT STRUCTURE):
    [
        {
            "category": "Groceries", "items": ["Apple", "Bread"], "total_price": "3.55"
        },
        {
            "category": "Fast Food", "items": ["Fren Onion Soup"], "total_price": "5.95"
        }
    ]

## Example Output what the `save_to_firebase` tool should return:
{
  "result": "success",
  "message": "Data saved to Firebase.",
  "data":     [
        {
            "category": "Groceries", "items": ["Apple", "Bread"], "total_price": "3.55"
        },
        {
            "category": "Fast Food", "items": ["Fren Onion Soup"], "total_price": "5.95"
        }
    ]
}


Take the Data from the 'grouped_classification' key in the input JSON and use it to generate the summary JSON.
{grouped_classification}
""",
    description="Generates and saves the final receipt classification summary to Firebase.",
    tools=[save_to_firebase],
    output_key="firebase_save_result"
)
