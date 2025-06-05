# from langchain_core.runnables import RunnableSequence # from langchain.chains import LLMChain
from langchain_ollama import ChatOllama # from langchain_community.chat_models import ChatOllama
from langchain.prompts import PromptTemplate
import json, re, math, time
from concurrent.futures import ThreadPoolExecutor

TEXT_PROMPT_TEMPLATE = """
Given the following receipt items and possible total values, classify each item into one of:
["Groceries", "Fast Food", "Electronics", "Apparel", "Personal Care", "Others"]
For each category:
- List the items that belong to it (as strings).
- Compute the sum total of prices for that category.
- Use the price from each line item (e.g., "2 Socks 3" means 2 units, $3 total).
Return ONLY a JSON object in the following format (KEEP IN MIND THIS IS A SAMPLE, DO NOT USE IT AS IS FOR YOUR OUTPUT - IMPORTANT!):
{{
  "categories": [
    {{"category": "Groceries", "total": 10.50, "items": ["Apple", "Banana"]}},
    ...
  ],
  "overall_total": (choose the most likely value from the candidates)
}}
Inputs:
Receipt Items:
{items}
Receipt Totals (candidates):
{totals}
"""

VISION_PROMPT_TEMPLATE = """
This is an image of a restaurant receipt. 
Extract all line items (each item and its price), classify each item into:
["Groceries", "Fast Food", "Electronics", "Apparel", "Personal Care", "Others"].
For each category, list all items and compute the total price.
Return ONLY a JSON object in the following format (KEEP IN MIND THIS IS A SAMPLE, DO NOT USE IT AS IS FOR YOUR OUTPUT - IMPORTANT!):
{{
  "categories": [
    {{"category": "Groceries", "total": 10.50, "items": ["Apple", "Banana"]}},
    ...
  ],
  "overall_total": ...
}}
NOTE: The below Inputs are for context of what an Alternative Extraction Source has Given utilise it for helping to Extract but Give priority to the Image.
Inputs:
Receipt Items:
{items}
Receipt Totals (candidates):
{totals}
"""


text_prompt = PromptTemplate(input_variables=["items", "totals"], template=TEXT_PROMPT_TEMPLATE)
vision_prompt = PromptTemplate(input_variables=["items", "totals"], template=VISION_PROMPT_TEMPLATE)

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
    try:
        text = text.strip().replace("```json", "").replace("```", "")
        obj_match = re.search(r"{[\s\S]+}", text)
        if obj_match:
            return json.loads(obj_match.group())
        arr_match = re.search(r"\[[\s\S]+\]", text)
        if arr_match:
            return {"categories": json.loads(arr_match.group())}
        return {"error": "No valid JSON found", "raw_response": text}
    except Exception as e:
        print("❌ JSON parse error:", e)
        print("❌ Raw response:", text)
        return {"error": "JSON parse error", "raw_response": text}

def run(line_items, receipt_total_value, image_b64=None, optimize=True):
    start_time = time.time()
    items_text = "\n".join(line_items)
    prompt_vars = {
        "items": items_text,
        "totals": json.dumps(receipt_total_value)
    }

    # MULTI-MODAL/FALLBACK FLOW
    if optimize and image_b64:
        # 1. Vision LLM
        vision_result = vision_chain.bind(images=[image_b64]).invoke(prompt_vars)
        vision_json = extract_json(vision_result.content)
        print("[Vision LLM] JSON:", vision_json)

        # 2. Main LLM double-checks vision's output using OCR text
        check_prompt = (
            f"A vision model looked at the receipt image and categorized items as follows:\n"
            f"{json.dumps(vision_json)}\n"
            f"Double-check this with the following OCR line items:\n"
            f"{items_text}\nTotals: {json.dumps(receipt_total_value)}\n"
            f"If the categories and totals are correct, return the same JSON. "
            f"If any are incorrect, return the corrected JSON."
        )
        main_result = main_chain.invoke({
            "items": items_text,
            "totals": json.dumps(receipt_total_value),
            "prompt": check_prompt,
            "vision_json": json.dumps(vision_json)
        })
        main_json = extract_json(main_result.content)
        print("[Main LLM] JSON:", main_json)

        # If main_json is None, use vision_json
        if not main_json:
            main_json = vision_json

        # If still None, stop
        if main_json is None:
            return {"error": "Both vision and main LLM failed.", "time_taken_seconds": round(time.time() - start_time, 2)}

        # 3. Fallback LLM, with all context
        fallback_prompt = (
            f"Vision LLM output: {json.dumps(vision_json)}\n"
            f"Main LLM output: {json.dumps(main_json)}\n"
            f"OCR line items: {items_text}\n"
            f"Totals: {json.dumps(receipt_total_value)}\n"
            "Compare the outputs above and return the most accurate categorization and totals as a single JSON."
        )
        fallback_result = fallback_chain.invoke({
            "items": items_text,
            "totals": json.dumps(receipt_total_value),
            "prompt": fallback_prompt,
            "vision_json": json.dumps(vision_json),
            "main_json": json.dumps(main_json)
        })
        final = extract_json(fallback_result.content)
        print("[Fallback LLM] JSON:", final)

        # If fallback is None, use main_json (if available), else vision_json
        if not final:
            final = main_json if main_json else vision_json

        # Defensive: still None? Error out
        if final is None:
            return {"error": "All classification stages failed.", "time_taken_seconds": round(time.time() - start_time, 2)}

        if isinstance(final, list):
            final = {"categories": final}
        final["time_taken_seconds"] = round(time.time() - start_time, 2)
        return final

    # ----------- TEXT-ONLY FLOW -----------
    else:
        try:
            result = main_chain.invoke(prompt_vars)
            output = extract_json(result.content)
            if not output:
                return {"error": "Text-only classification failed.", "time_taken_seconds": round(time.time() - start_time, 2)}
            if isinstance(output, list):
                output = {"categories": output}
            output["time_taken_seconds"] = round(time.time() - start_time, 2)
            return output
        except Exception as e:
            print("❌ Classification failed:", e)
            return {"error": str(e), "time_taken_seconds": round(time.time() - start_time, 2)}