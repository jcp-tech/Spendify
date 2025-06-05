# from langchain_core.runnables import RunnableSequence # from langchain.chains import LLMChain
from langchain_ollama import ChatOllama # from langchain_community.chat_models import ChatOllama
from langchain.prompts import PromptTemplate
import json, re, math
from concurrent.futures import ThreadPoolExecutor

# Simple & strict JSON prompt
PROMPT_TEMPLATE = """
Classify each item below into one of:
["Groceries", "Fast Food", "Electronics", "Apparel", "Personal Care", "Others"]

Respond ONLY with a JSON array like:
[{{"item": "Sample", "category": "Groceries"}}]

Items:
{items}
"""

prompt = PromptTemplate(input_variables=["items"], template=PROMPT_TEMPLATE)

'''
📊 Final Model Benchmark Summary (with Accuracy)

| Model         | Quality     | Items Classified | Time (min) | Accuracy (Manual Evaluation)              | Notes                                                         |
| ------------- | ----------- | ---------------- | ---------- | ----------------------------------------- | ------------------------------------------------------------- |
| phi3          | ❌ Partial   | 22 / 25          | ~0.81      | ⚠️ ~88% (2 misclassified + 3 missing)      | Fast but unreliable — not suitable for full receipt batches   |
| llama3        | ✅ Reliable  | 25 / 25          | ~1.78      | ✅ ~96-98% (2 borderline cases)            | ✅ Best balance of speed + accuracy                            |
| mistral       | ✅ Excellent | 25 / 25          | ~2.23      | 🏆 100% (spot-on categories)              | Very accurate, but slow                                       |
| command-r     | ✅ Reliable  | 25 / 25          | ~7.62      | ✅ ~100% (excellent contextual decisions)  | High latency, not practical except for low-frequency fallback |
'''

# Will be initialized from init_classifier()
main_chain = fallback_chain = None
main_model = fallback_model = None

def init_classifier(primary: str = "llama3", fallback: str = "mistral"):
    """
    Initializes the main and fallback chains.
    """
    global main_chain, fallback_chain, main_model, fallback_model
    main_model = primary # Primary model ~ Options are "phi3", "llama3"
    fallback_model = fallback # Fallback model ~ Options are "mistral", "command-r"
    main_chain = prompt | ChatOllama(model=main_model)
    fallback_chain = prompt | ChatOllama(model=fallback_model)

# Extract clean JSON
def extract_json(text):
    try:
        match = re.search(r"\[\s*{.*?}\s*]", text, re.DOTALL)  # non-greedy match
        if match:
            json_text = match.group()
            return json.loads(json_text)
        return None
    except Exception as e:
        print("❌ JSON parse error:", e)
        return None


# Classify one batch (try main, fallback to fallback_chain)
def classify_batch(batch):
    items_text = "\n".join(batch)
    try:
        print(f"⚡ main_chain ({main_model})...")
        result = main_chain.invoke({"items": items_text})
        parsed = extract_json(result.content) # extract_json(result["text"])
        if parsed: return parsed
    except Exception as e:
        print("⚠️ main_chain failed:", e)

    try:
        print(f"🔁 fallback_chain ({fallback_model})...")
        result = fallback_chain.invoke({"items": items_text})
        return extract_json(result.content) or [] # extract_json(result["text"]) or []
    except Exception as e:
        print("❌ fallback_chain failed too:", e)
        return []

# Run in parallel
def classify_items(item_list, optimize=True, num_workers=3):
    results = []
    if not optimize:
        # Run sequentially (item_list is already a list of strings)
        print("🔄 Running sequential classification (optimize=False)...")
        batch_result = classify_batch(item_list)
        if batch_result:
            results.extend(batch_result)
    else:
        # Run in parallel
        print(f"⚡ Running optimized parallel classification with {num_workers} threads...")
        chunk_size = math.ceil(len(item_list) / num_workers)
        batches = [item_list[i:i + chunk_size] for i in range(0, len(item_list), chunk_size)]
        with ThreadPoolExecutor(max_workers=num_workers) as executor:
            for batch_result in executor.map(classify_batch, batches):
                if batch_result:
                    results.extend(batch_result)
    return results

def run(sample_items, optimize=True, num_workers=3):
    """
    Run the classification process with given items.
    :param sample_items: List of items to classify.
    :param optimize: Whether to run in parallel or sequentially.
    :param num_workers: Number of threads for parallel execution.
    :return: Classified items as a list of dictionaries.
    """
    # import time
    # start_time = time.time()
    output = classify_items(sample_items, optimize=optimize, num_workers=num_workers)
    # print("\n✅ Final Classified Output:\n", json.dumps(output, indent=2, ensure_ascii=False))
    # end_time = time.time()
    # print("\n🕒 Summary:")
    # print("Models Used: `", main_model, "` and fallback with `", fallback_model, "`")
    # print("Number of Items Given:", len(sample_items))
    # print("Number of Items Classified:", len(output))
    # print("Total Time Taken (mins):", (end_time - start_time) / 60)
    # print("NOTE: Optimization is set to", optimise, "for this run.")
    return output #, (end_time - start_time) / 60