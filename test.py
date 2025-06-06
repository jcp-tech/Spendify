line_items=['1 g1 Imp White 7.75', '1 Blue Moon Tap 6.00', 'Mozzarella&Tomato 9.95', 'Pork Quesadilla 9.95', '1 Fren Onion Soup 5.95', '1 Pork Chop 21.95', '1 Hanger Sizzle 24.95']
receipt_total_value={"total_amount": "94.18", "net_amount": "86.50", "total_tax_amount": "7.68"}
grouped={"net_amount": ["86.50"], "total_amount": ["94.18"], "total_tax_amount": ["7.68"], "currency": ["$"], "purchase_time": ["08:22PM"], "receipt_date": ["09/24/2016"], "supplier_name": ["Nancy"], "supplier_phone": ["718.343-4616"], "supplier_address": ["255-41 Jericho Turnpike\nFloral Park, NY 11001"], "line_item": ["1 g1 Imp White 7.75", "1 Blue Moon Tap 6.00", "Mozzarella&Tomato 9.95", "Pork Quesadilla 9.95", "1 Fren Onion Soup 5.95", "1 Pork Chop 21.95", "1 Hanger Sizzle 24.95"], "supplier_city": [""]}
optimize=True
image_path = r"C:\Users\JonathanChackoPattas\OneDrive - Maritime Support Solutions\Desktop\Spendify\uploads\c9408662-4457-4621-8187-483022e58f80_c9408662-4457-4621-8187-483022e58f80.png"
import os, base64
from dotenv import load_dotenv
from receipt_classifier import init_classifier, run as classify_run
from io import BytesIO
from PIL import Image

# Load ENV
load_dotenv()

# Set default models if not passed via CLI
DEFAULT_MAIN_MODEL = os.getenv("MAIN_MODEL", "llama3")
DEFAULT_FALLBACK_MODEL = os.getenv("FALLBACK_MODEL", "mistral")
DEFAULT_VISION_MODEL = os.getenv("VISION_MODEL", "llava")

init_classifier(primary=DEFAULT_MAIN_MODEL, fallback=DEFAULT_FALLBACK_MODEL, vision=DEFAULT_VISION_MODEL)

def image_to_base64(image_path):
    with Image.open(image_path) as img:
        buffered = BytesIO()
        img.save(buffered, format="JPEG")
        return base64.b64encode(buffered.getvalue()).decode("utf-8")

dictval = classify_run(
    line_items,
    receipt_total_value=receipt_total_value,
    raw_data=grouped,
    image_b64=image_to_base64(image_path),
    optimize=optimize,
)

print(dictval)