"""
Receipt Classification Validation Agent

This agent validates that the grouped classification output matches the receipt totals.
"""

# classification_reviewer/agent.py
from google.adk.agents.llm_agent import LlmAgent
from .tools import calculate_final_total, exit_function
# from google.adk.tools import exit_loop

GEMINI_MODEL = "gemini-2.0-flash" # Constants

validate_classification = LlmAgent(
    name="validate_classification",
    model=GEMINI_MODEL,
    instruction="""
You are a Receipt Classification Validation Agent.

Your task is to verify that the GROUPED receipt breakdown's total matches the original receipt total_amount or net_amount.

## VALIDATION PROCESS
1. Use the `calculate_final_total` tool on the grouped_classification data (the full list of categories).
   - Pass the grouped_classification data directly to the tool.

2. If `calculate_final_total` returns 'error':
   - Output a JSON object with:
     - "status": 0
     - "details": Use the tool's error message.
   - Do **not** proceed to further steps.

3. If `calculate_final_total` returns 'success':
   - Extract the computed 'final_total' from the tool output.
   - Call the `exit_function` tool, passing:
     - The computed `final_total`
     - The original classification data (from stage_init_classifier or similar).
     - The current tool context.

4. The `exit_function` tool will handle the comparison against both total_amount and net_amount from the receipt, determine if the totals match, and set escalation state as appropriate.

5. **Never output raw values or explain the process. Only return the JSON object provided by the last tool executed (either the error from step 2, or the output from `exit_function`).**

## SUMMARY
- Always first call `calculate_final_total`.
- If there is an error, output the error as your final result.
- If successful, immediately call `exit_function` and output its result.
- Do not explain, summarize, or add extra details.

## INPUT DATA FIELDS:
- `grouped_classification`: The grouped receipt breakdown as a list of category objects.
- `stage_init_classifier`: The initial classification and totals dictionary, used for reference totals.

## AGENT FLOW:
1. Call `calculate_final_total`.
2. On success, call `exit_function`.
3. Output **only** the result from the last tool.

""",
    description="Validates that the grouped classification matches the receipt's total using the calculate_final_total tool and calls exit_function to determine and return final status.",
    tools=[calculate_final_total, exit_function],
    output_key="validation_result",
)
