# from langchain_core.runnables import RunnableSequence # from langchain.chains import LLMChain
from langchain_ollama import ChatOllama # from langchain_community.chat_models import ChatOllama
from langchain.prompts import PromptTemplate
# from langchain.tools.python.tool import PythonREPLTool
from langchain.agents import Tool, initialize_agent
import json, re, time # , math


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

# Extract clean JSON
def extract_json(text):
    cleaned = re.sub(r'//.*', '', text)
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

def run(line_items, receipt_total_value, raw_data=None, image_b64=None, optimize=True):
    start_time = time.time()

    # Initialize prompt vars
    prompt_vars = {
        "items": "",  # will be set after standardization
        "totals": json.dumps(receipt_total_value),
        "raw_data": json.dumps(raw_data) if raw_data else "",
    }

    if optimize and image_b64:
        # ---- TOOLS DEFINITION ----
        tools = [
            Tool(
                name="Standardizer",
                func=lambda args: standardize_line_items(args["raw_lines"]),
                description="Convert list of raw line items like '2 Apple 10' into structured format"
            ),
            Tool(name="VisionClassifier", func=vision_chain.bind(images=[image_b64]).invoke,
                 description="Use for image-based classification"),
            Tool(name="MainClassifier", func=main_chain.invoke,
                 description="Use to verify and improve receipt classification"),
            Tool(name="FallbackClassifier", func=fallback_chain.invoke,
                 description="Use when other results are incomplete or inconsistent"),
            Tool(name="ValidatorTool", func=lambda args: validate_classification(args["data"], args["expected"]),
                 description="Check if sum of categories ≈ receipt total"),
            Tool(
                name="ConfidenceScorer",
                func=lambda args: score_confidence(args["result_json"], args["expected_total"]),
                description="Assign a confidence score based on number of items and how close the total is"
            )
        ]

        # ---- AGENT INIT ----
        controller = initialize_agent(tools, ChatOllama(model=main_model), agent="zero-shot-react-description")

        # STEP 1: Standardize Line Items
        standardized = tools[0].func({"raw_lines": line_items})
        prompt_vars["items"] = json.dumps(standardized)

        # STEP 2: Vision Classification
        vision_result = tools[1].func(prompt_vars)
        vision_json = extract_json(vision_result.content)
        print("[Vision LLM] JSON:", vision_json)

        # STEP 3: Validate vision output
        expected_total = receipt_total_value.get("total_amount") or receipt_total_value.get("net_amount") or "0"
        val_result = tools[4].func({"data": vision_json, "expected": expected_total})
        print("[Validator] Vision Valid?", val_result)

        if val_result.get("valid"):
            confidence = tools[5].func({"result_json": vision_json, "expected_total": expected_total})
            vision_json["confidence_score"] = confidence.get("confidence_score")
            vision_json["source"] = "Vision"
            vision_json["time_taken_seconds"] = round(time.time() - start_time, 2)
            return vision_json

        # STEP 4: Main Classification
        main_result = tools[2].func(prompt_vars)
        main_json = extract_json(main_result.content)
        print("[Main LLM] JSON:", main_json)

        val_main = tools[4].func({"data": main_json, "expected": receipt_total_value[0]})
        if val_main.get("valid"):
            confidence = tools[5].func({"result_json": main_json, "expected_total": receipt_total_value[0]})
            main_json["confidence_score"] = confidence.get("confidence_score")
            main_json["source"] = "Main"
            main_json["time_taken_seconds"] = round(time.time() - start_time, 2)
            return main_json

        # STEP 5: Fallback Classification
        fallback_result = tools[3].func(prompt_vars)
        fallback_json = extract_json(fallback_result.content)
        print("[Fallback LLM] JSON:", fallback_json)

        val_fallback = tools[4].func({"data": fallback_json, "expected": receipt_total_value[0]})
        confidence = tools[5].func({"result_json": fallback_json, "expected_total": receipt_total_value[0]})
        fallback_json["confidence_score"] = confidence.get("confidence_score")
        fallback_json["source"] = "Fallback"
        fallback_json["time_taken_seconds"] = round(time.time() - start_time, 2)
        return fallback_json

    else:
        # TEXT-ONLY fallback mode
        items_text = "\n".join(line_items)
        prompt_vars["items"] = items_text
        result = main_chain.invoke(prompt_vars)
        output = extract_json(result.content)
        if isinstance(output, list):
            output = {"categories": output}
        confidence = score_confidence(output, receipt_total_value.get("total_amount", "0"))
        output["confidence_score"] = confidence.get("confidence_score")
        output["source"] = "Main (text-only)"
        output["time_taken_seconds"] = round(time.time() - start_time, 2)
        return output
