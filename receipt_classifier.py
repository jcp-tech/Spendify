# from langchain_core.runnables import RunnableSequence, Runnable # from langchain.chains import LLMChain
from langchain_ollama import ChatOllama # from langchain_community.chat_models import ChatOllama
from langchain.prompts import PromptTemplate
# from langchain.tools.python.tool import PythonREPLTool
# from langchain.agents import Tool, initialize_agent
from langgraph.graph import StateGraph, END
from langchain_core.messages import HumanMessage
import json, re, time # , math
from typing import TypedDict, Optional, Any

class ReceiptState(TypedDict):
    items_raw: str            # Raw input (stringified list)
    items_structured: str     # Structured after standardizer
    items: str                # For LLM model input (just a copy of items_structured)
    totals: str
    raw_data: str
    image_b64: Optional[str]
    result: Optional[Any]
    stage: str
    valid: Optional[bool]
    confidence_score: Optional[float]


TEXT_PROMPT_TEMPLATE = """
Given a structured list of items with quantity and price like:

{items}

Classify each item into one of the following categories:
["Groceries", "Fast Food", "Electronics", "Apparel", "Personal Care", "Others"]

Instructions:
- Use item names to decide the category.
- For each category, list all matching items and compute total price.
- Use the given quantity and price data; do not guess missing values.
- Sum all item prices and compare with receipt total candidates.

Return ONLY a JSON object in the format:
{{
  "categories": [
    {{"category": "Fast Food", "total": 32.90, "items": ["..."]}},
    ...
  ],
  "overall_total": <selected_best_total>
}}
Inputs:
- Receipt Totals (candidates): {totals}
- Raw OCR Data for reference only: {raw_data}
"""

VISION_PROMPT_TEMPLATE = """
This is an image of a restaurant receipt.

Extract all line items (with item name, quantity if present, and price).
Classify each item into one of:
["Groceries", "Fast Food", "Electronics", "Apparel", "Personal Care", "Others"]

Instructions:
- If item shows "2 Apple 4", that means 2 units for $4 total.
- Return structured JSON with:
  - categories
  - item names
  - category totals
  - overall_total selected from candidates

Use this format:
{{
  "categories": [
    {{"category": "Fast Food", "total": 32.90, "items": ["..."]}},
    ...
  ],
  "overall_total": <selected_best_total>
}}

Inputs:
Receipt Totals (candidates): {totals}
Structured Line Items: {items}
OCR/Parsed Context (for guidance only): {raw_data}
"""



text_prompt = PromptTemplate(input_variables=["items", "totals", "raw_data"], template=TEXT_PROMPT_TEMPLATE)
vision_prompt = PromptTemplate(input_variables=["items", "totals", "raw_data"], template=VISION_PROMPT_TEMPLATE)

'''
📊 Final Model Benchmark Summary (with Accuracy)

| Model         | Quality     | Items Classified | Time (min) | Accuracy (Manual Evaluation)              | Notes                                                            |
| ------------- | ----------- | ---------------- | ---------- | ----------------------------------------- | -----------------------------------------------------------------|
| phi3          | ❌ Partial   | 22 / 25          | ~0.81      | ⚠️ ~88% (2 misclassified + 3 missing)      | Fast but unreliable — not suitable for full receipt batches   |
| llama3        | ✅ Reliable  | 25 / 25          | ~1.78      | ✅ ~96-98% (2 borderline cases)            | ✅ Best balance of speed + accuracy                           |
| mistral       | ✅ Excellent | 25 / 25          | ~2.23      | 🏆 100% (spot-on categories)               | Very accurate, but slow                                       |
| command-r     | ✅ Reliable  | 25 / 25          | ~7.62      | ✅ ~100% (excellent contextual decisions)  | High latency, not practical except for low-frequency fallback |
| bakllava      | 🔁 TBD       |  -----           | -----      | -----                                       | -----                                                         |
| llava         | 🔁 TBD       |  -----           | -----      | -----                                       | -----                                                         |
'''

# Will be initialized from init_classifier()
main_chain = fallback_chain = vision_chain = None
main_model = fallback_model = vision_model = None

def init_classifier(primary: str = "llama3", fallback: str = "mistral", vision: str = "llava"):
    """
    Initializes the main, fallback and vision chains.
    """
    global main_chain, fallback_chain, vision_chain, main_model, fallback_model, vision_model
    main_model = primary # Primary model ~ Options are "phi3", "llama3"
    fallback_model = fallback # Fallback model ~ Options are "mistral", "command-r"
    vision_model = vision # Vision model ~ Options are "bakllava", "llava"
    main_chain = text_prompt | ChatOllama(model=main_model)
    fallback_chain = text_prompt | ChatOllama(model=fallback_model)
    vision_chain = vision_prompt | ChatOllama(model=vision_model)
    return main_chain, fallback_chain, vision_chain

def extract_json(text):
    cleaned = text.replace("\\_", "_")  # fix LLM-escaped underscores
    cleaned = re.sub(r'//.*', '', cleaned)
    cleaned = re.sub(r'/\*[\s\S]*?\*/', '', cleaned)
    cleaned = re.sub(r',(\s*[\]}])', r'\1', cleaned)
    try:
        obj_match = re.search(r"{[\s\S]+}", cleaned)
        if obj_match:
            return json.loads(obj_match.group())
        arr_match = re.search(r"\[[\s\S]+\]", cleaned)
        if arr_match:
            return {"categories": json.loads(arr_match.group())}
    except Exception as e:
        print("❌ JSON parse error:", e)
        print("❌ Raw response:", text)
    return {"error": "JSON parsing failed", "raw_response": text}

def validate_classification(json_data, expected_total):
    try:
        expected = float(expected_total)
        actual = sum(cat["total"] for cat in json_data.get("categories", []))
        delta = abs(actual - expected)
        return {"valid": delta <= 1.0, "delta": delta, "actual": actual, "expected": expected}
    except Exception as e:
        return {"error": str(e)}

def standardize_line_items(raw_lines):
    result = {}
    for entry in raw_lines:
        parts = entry.strip().split()
        try:
            if len(parts) >= 3 and parts[0].isdigit():
                qty = int(parts[0])
                price = float(parts[-1])
                name = " ".join(parts[1:-1])
            else:
                qty = 1
                price = float(parts[-1])
                name = " ".join(parts[:-1])
            result[name] = {"QTY": qty, "PRICE": price}
        except:
            continue
    return result

def score_confidence(result_json, expected_total):
    try:
        total = sum(c["total"] for c in result_json.get("categories", []))
        total_diff = abs(total - float(expected_total))
        item_count = sum(len(c["items"]) for c in result_json.get("categories", []))
        confidence = 1.0
        if total_diff > 5:
            confidence -= 0.3
        elif total_diff > 2:
            confidence -= 0.1
        if item_count < 4:
            confidence -= 0.2
        return {
            "confidence_score": round(confidence, 2),
            "total_diff": round(total_diff, 2),
            "item_count": item_count
        }
    except Exception as e:
        return {"error": str(e)}

def standardizer_node(state: ReceiptState):
    print("➡️ [Graph] Standardizing line items...")
    structured = standardize_line_items(json.loads(state["items_raw"]))
    state["items_structured"] = json.dumps(structured)
    state["items"] = state["items_structured"]
    state["stage"] = "standardized"
    return state

def vision_node(state: ReceiptState):
    print("🖼️ [Graph] Running Vision Model...")
    response = vision_chain.bind(images=[state["image_b64"]]).invoke({
        "items": state["items"],
        "totals": state["totals"],
        "raw_data": state["raw_data"]
    })
    state["result"] = extract_json(response.content)
    state["stage"] = "vision"
    return state

def validator_node(state: ReceiptState):
    print("🔍 [Graph] Validating classification results...")
    expected_total = json.loads(state["totals"]).get("total_amount") or "0"
    is_valid = validate_classification(state["result"], expected_total)
    confidence = score_confidence(state["result"], expected_total)
    state["valid"] = is_valid.get("valid", False)
    state["confidence_score"] = confidence.get("confidence_score")
    return state

def main_node(state: ReceiptState):
    print("🤖 [Graph] Running Main LLM Model...")
    response = main_chain.invoke({
        "items": state["items"],
        "totals": state["totals"],
        "raw_data": state["raw_data"]
    })
    state["result"] = extract_json(response.content)
    state["stage"] = "main"
    return state

def fallback_node(state: ReceiptState):
    print("🔁 [Graph] Running Fallback Model...")
    response = fallback_chain.invoke({
        "items": state["items"],
        "totals": state["totals"],
        "raw_data": state["raw_data"]
    })
    state["result"] = extract_json(response.content)
    state["stage"] = "fallback"
    return state

def run(line_items, receipt_total_value, raw_data=None, image_b64=None, optimize=True):
    print("📝 Running receipt classification...")
    start_time = time.time()

    if optimize and image_b64:
        graph = StateGraph(ReceiptState)

        graph.add_node("standardizer", standardizer_node)
        graph.add_node("vision", vision_node)
        graph.add_node("validator", validator_node)
        graph.add_node("main", main_node)
        graph.add_node("fallback", fallback_node)

        # Edges
        graph.set_entry_point("standardizer")
        graph.add_edge("standardizer", "vision")
        graph.add_edge("vision", "validator")
        graph.add_edge("main", "validator")      # If we reach main, its output goes to validator
        graph.add_edge("fallback", "validator")  # If we reach fallback, its output goes to validator

        # Centralized routing logic after any validation step
        def route_after_any_validation(state: ReceiptState):
            stage = state.get("stage")
            is_valid = state.get("valid", False)

            if stage == "vision":
                print(f"Routing after vision validation. Valid: {is_valid}, Confidence: {state.get('confidence_score')}")
                return "main" if not is_valid else END
            elif stage == "main":
                print(f"Routing after main validation. Valid: {is_valid}, Confidence: {state.get('confidence_score')}")
                return "fallback" if not is_valid else END
            elif stage == "fallback":
                print(f"Routing after fallback validation. Valid: {is_valid}, Confidence: {state.get('confidence_score')}")
                # Always END after fallback, regardless of validity.
                # Consider raising an error or returning a specific "failed" status if still not valid.
                return END
            else:
                # This case should ideally not be reached if stages are set correctly
                print(f"Warning: Unknown stage '{stage}' in route_after_any_validation. Ending.")
                return END

        graph.add_conditional_edges(
            "validator", # Source node for conditional routing is always "validator"
            route_after_any_validation
        )
        # The following lines are removed or replaced by the logic above:
        # def route_after_validation(state: ReceiptState):
        #     return "main" if not state.get("valid", False) and state["stage"] == "vision" else END
        # def route_after_main_validation(state: ReceiptState):
        #     return "fallback" if not state.get("valid", False) and state["stage"] == "main" else END
        # graph.add_conditional_edges("validator", route_after_validation)
        # graph.add_conditional_edges("main", route_after_main_validation)


        receipt_graph = graph.compile()

        state = {
            "items_raw": json.dumps(line_items),
            "items_structured": "",
            "items": "",
            "totals": json.dumps(receipt_total_value),
            "raw_data": json.dumps(raw_data) if raw_data else "",
            "image_b64": image_b64,
            "result": None,
            "stage": "init",
            "valid": None,
            "confidence_score": None,
        }

        final_state = receipt_graph.invoke(state)
        result = final_state.get("result", {})
        result["confidence_score"] = final_state.get("confidence_score", 0)
        result["source"] = final_state.get("stage", "unknown")
        result["time_taken_seconds"] = round(time.time() - start_time, 2)
        return result

    else:
        prompt_vars = {
            "items": "\n".join(line_items),
            "totals": json.dumps(receipt_total_value),
            "raw_data": json.dumps(raw_data) if raw_data else "",
        }
        result = main_chain.invoke(prompt_vars)
        output = extract_json(result.content)
        if isinstance(output, list):
            output = {"categories": output}
        confidence = score_confidence(output, receipt_total_value.get("total_amount", "0"))
        output["confidence_score"] = confidence.get("confidence_score")
        output["source"] = "Main (text-only)"
        output["time_taken_seconds"] = round(time.time() - start_time, 2)
        return output