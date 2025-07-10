import requests
import json

class ADKClient:
    def __init__(self, adk_url, app_name, user_id="user", session_id=None):
        self.adk_url = adk_url.rstrip('/')
        self.app_name = app_name
        self.user_id = user_id
        self.session_id = session_id
        self.headers = {"Content-Type": "application/json"}

    def random_session_url(self):
        return f"{self.adk_url}/apps/{self.app_name}/users/{self.user_id}/sessions"
    def custom_session_url(self):
        if self.session_id is None:
            return self.random_session_url()
        else:
            return f"{self.adk_url}/apps/{self.app_name}/users/{self.user_id}/sessions/{self.session_id}" 
    def get_or_create_session(self, method="POST", payload=None, custom_session=False):
        # Decide which URL to use based on session_id and custom_session flag
        if self.session_id is None or not custom_session:
            url = self.random_session_url()
        else:
            url = self.custom_session_url()

        payload = payload or {}

        try:
            if method.upper() == "POST":
                resp = requests.post(url, headers=self.headers, data=json.dumps(payload))
            elif method.upper() == "GET":
                resp = requests.get(url, headers=self.headers)
            else:
                raise ValueError("method must be 'POST' or 'GET'")
            resp.raise_for_status()
            return resp.json()
        except requests.exceptions.RequestException as e:
            print(f"Error with {method} request to {url}: {e}")
            if hasattr(e, 'response') and e.response is not None:
                print(f"Server response: {e.response.text}")
            return None


    def run_sse(self, session_id, prompt_text, streaming=False):
        """
        Sends a message to the run_sse endpoint using the given session_id and prompt_text.
        Returns a list of parsed event JSONs (raw).
        """
        url = f"{self.adk_url}/run_sse"
        payload = {
            "appName": self.app_name,
            "userId": self.user_id,
            "sessionId": session_id,
            "newMessage": {
                "role": "user",
                "parts": [{"text": prompt_text}]
            },
            "streaming": streaming
        }

        print(f"POST {url} with: {json.dumps(payload, indent=2)}")

        try:
            response = requests.post(url, headers=self.headers, data=json.dumps(payload), stream=True)
            response.raise_for_status()

            all_events = []

            for line in response.iter_lines():
                line = line.decode('utf-8')
                if line.startswith('data: '):
                    json_str = line[len('data: '):].strip()
                    if json_str:
                        try:
                            event_data = json.loads(json_str)
                            all_events.append(event_data)
                        except json.JSONDecodeError:
                            print(f"Error decoding: {json_str}")
                elif line.strip():
                    print(f"Non-data line: {line}")

            return all_events

        except requests.exceptions.RequestException as e:
            print(f"Error in run_sse: {e}")
            return None

    def extract_json_from_events(self, all_events):
        """
        Attempts to find and extract a JSON block from the 'parts' of the events.
        Returns the extracted JSON (as dict) if found, else None.
        """
        final_data = None
        for event_data in all_events or []:
            if 'content' in event_data and event_data['content'] and \
               'parts' in event_data['content'] and isinstance(event_data['content']['parts'], list):
                for part in event_data['content']['parts']:
                    if 'text' in part and isinstance(part['text'], str):
                        text_content = part['text']
                        if text_content.startswith('```json') and text_content.endswith('```'):
                            json_string = text_content.replace('```json\n', '').replace('\n```', '').strip()
                            try:
                                final_data = json.loads(json_string)
                                return final_data
                            except json.JSONDecodeError:
                                print("Warning: Could not parse JSON string in Markdown block.")
        return None

# prompt_dict = {
#     "line_items":['1 g1 Imp White 7.75', '1 Blue Moon Tap 6.00', 'Mozzarella&Tomato 9.95', 'Pork Quesadilla 9.95', '1 Fren Onion Soup 5.95', '1 Pork Chop 21.95', '1 Hanger Sizzle 24.95'],
#     "receipt_total_value":{"total_amount": "94.18", "net_amount": "86.50", "total_tax_amount": "7.68"},
#     "grouped":{"net_amount": ["86.50"], "total_amount": ["94.18"], "total_tax_amount": ["7.68"], "currency": ["$"], "purchase_time": ["08:22PM"], "receipt_date": ["09/24/2016"], "supplier_name": ["Nancy"], "supplier_phone": ["718.343-4616"], "supplier_address": ["255-41 Jericho Turnpike\nFloral Park, NY 11001"], "line_item": ["1 g1 Imp White 7.75", "1 Blue Moon Tap 6.00", "Mozzarella&Tomato 9.95", "Pork Quesadilla 9.95", "1 Fren Onion Soup 5.95", "1 Pork Chop 21.95", "1 Hanger Sizzle 24.95"], "supplier_city": [""]}
# }

# prompt_txt = json.dumps(prompt_dict, indent=2)

# # ----------------- USAGE EXAMPLE -----------------
# if __name__ == "__main__":
#     adk = ADKClient("http://localhost:8000", "receipt_classifier", user_id="user", session_id="JONATHAN_SESSIONS")

#     # Create a new session (POST)
#     session_resp = adk.get_or_create_session(method="POST", custom_session=True)
#     if session_resp and 'id' in session_resp:
#         session_id = session_resp['id']
#         print(f"Session created: {session_id}")
#     else:
#         # try:
#         #     session_id = adk.get_or_create_session(method="GET", custom_session=True)['id']
#         #     print(f"Session retrieved: {session_id}")
#         # except Exception as e:
#         #     print(f"Failed to retrieve or create session: {e}")
#         #     session_id = None
#         print("Failed to create session!")
#         exit()

#     # # Send message and get all raw events
#     # prompt = prompt_txt
#     # events = adk.run_sse(session_id, prompt)
#     # if events is not None:
#     #     # Extract JSON only if you expect a structured response
#     #     classified_data = adk.extract_json_from_events(events)
#     #     if classified_data:
#     #         print("Final classified data:\n", json.dumps(classified_data, indent=2))
#     #     else:
#     #         print("No structured JSON data found. Events received:")
#     #         print(json.dumps(events, indent=2))
#     # else:
#     #     print("No events received.")
