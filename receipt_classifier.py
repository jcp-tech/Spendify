from langchain_core.runnables import RunnableSequence # from langchain.chains import LLMChain
from langchain_ollama import ChatOllama # from langchain_community.chat_models import ChatOllama
from langchain.prompts import PromptTemplate
import json, re
from concurrent.futures import ThreadPoolExecutor
import math
import time

start_time = time.time()
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

# ✅ Primary (faster) and fallback (more reliable) chains
main_model = "llama3"  # Primary model ~ Options are "phi3", "llama3"
main_llm = ChatOllama(model=main_model)
main_chain = prompt | main_llm # main_chain = LLMChain(llm=main_llm, prompt=prompt)
fallback_model = "mistral"  # Fallback model ~ Options are "mistral", "command-r"
fallback_llm = ChatOllama(model=fallback_model)
fallback_chain = prompt | fallback_llm # LLMChain(llm=fallback_llm, prompt=prompt)

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
        response = main_chain.invoke({"items": items_text})
        result = extract_json(response["text"])
        if result: return result
    except Exception as e:
        print("⚠️ main_chain failed:", e)

    try:
        print(f"🔁 fallback_chain ({fallback_model})...")
        response = fallback_chain.invoke({"items": items_text})
        result = extract_json(response["text"])
        return result if result else []
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

# 🧪 Sample run
if __name__ == "__main__":
    sample_items = [
        "Nestlé Pure Life Water Bottle 500ml", "McDonald's Big Mac Meal",
        "Samsung Fast Charging Adapter", "Colgate MaxFresh Toothpaste 100g",
        "Nike Air Zoom Running Shoes", "Domino's Pepperoni Pizza Medium",
        "Sony Wireless Headphones WH-CH510", "Old Spice Deodorant Stick",
        "Tide Liquid Detergent 2L", "Adidas Track Pants", "Apple Lightning Charging Cable",
        "Dove Moisturizing Body Wash", "KFC Chicken Zinger Burger", "Panasonic AAA Batteries (Pack of 4)",
        "Reebok Men’s Workout T-Shirt", "Huggies Diapers - Size M", "Pizza Hut Cheese Lover's Pizza",
        "Oral-B Electric Toothbrush", "Banana Republic Leather Wallet", "Lay's Classic Potato Chips 180g",
        "Google Chromecast 3rd Gen", "Tim Hortons Iced Cappuccino Medium",
        "Head & Shoulders Anti-Dandruff Shampoo", "HP Wireless Mouse X200",
        "Starbucks Caramel Macchiato Tall"
    ]
    optimise = False  # Set to False to run sequentially
    output = classify_items(sample_items, optimize=optimise)
    print("\n✅ Final Classified Output:\n", json.dumps(output, indent=2, ensure_ascii=False))
    end_time = time.time()
    print("\n🕒 Summary:")
    print("Models Used: `", main_model, "` and fallback with `", fallback_model, "`")
    print("Number of Items Given:", len(sample_items))
    print("Number of Items Classified:", len(output))
    print("Total Time Taken (mins):", (end_time - start_time) / 60)
    print("NOTE: Optimization is set to", optimise, "for this run.")