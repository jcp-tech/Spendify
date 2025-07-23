from .flask_api.gcp_adk_classification import ADKClient
import json

prompt_dict = {
    "line_items":['1 g1 Imp White 7.75', '1 Blue Moon Tap 6.00', 'Mozzarella&Tomato 9.95', 'Pork Quesadilla 9.95', '1 Fren Onion Soup 5.95', '1 Pork Chop 21.95', '1 Hanger Sizzle 24.95'],
    "receipt_total_value":{"total_amount": "94.18", "net_amount": "86.50", "total_tax_amount": "7.68"},
    "grouped":{"net_amount": ["86.50"], "total_amount": ["94.18"], "total_tax_amount": ["7.68"], "currency": ["$"], "purchase_time": ["08:22PM"], "receipt_date": ["09/24/2016"], "supplier_name": ["Nancy"], "supplier_phone": ["718.343-4616"], "supplier_address": ["255-41 Jericho Turnpike\nFloral Park, NY 11001"], "line_item": ["1 g1 Imp White 7.75", "1 Blue Moon Tap 6.00", "Mozzarella&Tomato 9.95", "Pork Quesadilla 9.95", "1 Fren Onion Soup 5.95", "1 Pork Chop 21.95", "1 Hanger Sizzle 24.95"], "supplier_city": [""]}
}

prompt_txt = json.dumps(prompt_dict, indent=2)

# ----------------- USAGE EXAMPLE -----------------
if __name__ == "__main__":
    adk = ADKClient("http://localhost:8000", "receipt_classifier", user_id="user", session_id="JONATHAN_SESSIONS")

    # Create a new session (POST)
    session_resp = adk.get_or_create_session(method="POST", custom_session=True)
    if session_resp and 'id' in session_resp:
        session_id = session_resp['id']
        print(f"Session created: {session_id}")
    else:
        try:
            session_id = adk.get_or_create_session(method="GET", custom_session=True)['id']
            print(f"Session retrieved: {session_id}")
        except Exception as e:
            print(f"Failed to retrieve or create session: {e}")
            session_id = None
        print("Failed to create session!")
        exit()

    # Send message and get all raw events
    prompt = prompt_txt
    events = adk.run_sse(session_id, prompt)
    # if events is not None:
    #     # Extract JSON only if you expect a structured response
    #     classified_data = adk.extract_json_from_events(events)
    #     if classified_data:
    #         print("Final classified data:\n", json.dumps(classified_data, indent=2))
    #     else:
    #         print("No structured JSON data found. Events received:")
    #         print(json.dumps(events, indent=2))
    # else:
    #     print("No events received.")
    print("Events received:", json.dumps(events, indent=2))