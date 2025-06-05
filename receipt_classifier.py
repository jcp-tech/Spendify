from langchain_community.chat_models import ChatOllama
from langchain.chains import LLMChain
from langchain.prompts import PromptTemplate
import json
import re

# Multi-item prompt
prompt_text = """
You are an intelligent assistant for receipt classification.
Given a list of items, output a JSON array where each item is categorized as one of:
["Groceries", "Fast Food", "Electronics", "Apparel", "Personal Care", "Others"]

Return ONLY a valid JSON array like:
[
  {{"item": "Example Item", "category": "Groceries"}},
  ...
]

Do NOT add explanations or text before/after the JSON.
Items:
{items}
"""

# LangChain setup
llm = ChatOllama(model="mistral")
prompt = PromptTemplate(input_variables=["items"], template=prompt_text)
chain = LLMChain(llm=llm, prompt=prompt)

# Sample item list
sample_items = [
    "Nestlé Pure Life Water Bottle 500ml",
    "McDonald's Big Mac Meal",
    "Samsung Fast Charging Adapter",
    "Colgate MaxFresh Toothpaste 100g",
    "Nike Air Zoom Running Shoes",
    "Domino's Pepperoni Pizza Medium",
    "Sony Wireless Headphones WH-CH510",
    "Old Spice Deodorant Stick",
    "Tide Liquid Detergent 2L",
    "Adidas Track Pants",
    "Apple Lightning Charging Cable",
    "Dove Moisturizing Body Wash",
    "KFC Chicken Zinger Burger",
    "Panasonic AAA Batteries (Pack of 4)",
    "Reebok Men’s Workout T-Shirt",
    "Huggies Diapers - Size M",
    "Pizza Hut Cheese Lover's Pizza",
    "Oral-B Electric Toothbrush",
    "Banana Republic Leather Wallet",
    "Lay's Classic Potato Chips 180g",
    "Google Chromecast 3rd Gen",
    "Tim Hortons Iced Cappuccino Medium",
    "Head & Shoulders Anti-Dandruff Shampoo",
    "HP Wireless Mouse X200",
    "Starbucks Caramel Macchiato Tall"
]

# Run classification
items_formatted = "\n".join(sample_items)
response = chain.invoke({"items": items_formatted})
raw_output = response["text"]

# Optional: Clean and parse JSON safely
def extract_json(text):
    try:
        match = re.search(r"\[\s*{.*}\s*]", text, re.DOTALL)
        return json.loads(match.group()) if match else None
    except Exception as e:
        print("❌ Failed to parse JSON:", e)
        return None

parsed = extract_json(raw_output)

# Print results
print("🔍 Raw Output:\n", raw_output)
print("\n✅ Parsed:\n", json.dumps(parsed, indent=2) if parsed else "No valid JSON found")