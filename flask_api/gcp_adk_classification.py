import requests, json, logging
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
    def get_or_create_session(self, method="POST", payload={}, custom_session=False):
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
            logging.error(f"Error with {method} request to {url}: {e}")
            if hasattr(e, 'response') and e.response is not None:
                logging.error(f"Server response: {e.response.text}")
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

        logging.info(f"POST {url} with: {json.dumps(payload, indent=2)}")

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
                            logging.warning(f"Error decoding: {json_str}")
                elif line.strip():
                    logging.info(f"Non-data line: {line}")

            return all_events

        except requests.exceptions.RequestException as e:
            logging.error(f"Error in run_sse: {e}")
            return None

    def extract_json_from_events(self, all_events):
        """
        Extracts and parses JSON from the 'text' field in the last event's content['parts'].
        Returns the JSON as a dict, or {} if not found.
        """
        # logging.info(f"Events received: {all_events}")
        ''' # sample events data
                [
                    {'content': {'parts': [{'text': '{\n  "classified": [\n    {\n      "item": "Coffee",\n      "quantity": "1",\n      "price": "3.50",\n      "category": "Fast Food"\n    },\n    {\n      "item": "Glass House Wine",\n      "quantity": "1",\n      "price": "9.95",\n      "category": "Others"\n    },\n    {\n      "item": "Jumbo Coctail Shrimp",\n      "quantity": "1",\n      "price": "12.95",\n      "category": "Fast Food"\n    },\n    {\n      "item": "Escargot Bourguigonne",\n      "quantity": "1",\n      "price": "10.95",\n      "category": "Fast Food"\n    },\n    {\n      "item": "Veal Zingaria",\n      "quantity": "1",\n      "price": "23.95",\n      "category": "Fast Food"\n    },\n    {\n      "item": "Duckling ala Arancio",\n      "quantity": "1",\n      "price": "25.95",\n      "category": "Fast Food"\n    }\n  ],\n  "total_values_dict": {\n    "total_amount": "94.78",\n    "net_amount": "87.25",\n    "total_tax_amount": "7.53"\n  }\n}'}], 'role': 'model'}, 'usageMetadata': {'candidatesTokenCount': 341, 'candidatesTokensDetails': [{'modality': 'TEXT', 'tokenCount': 341}], 'promptTokenCount': 1176, 'promptTokensDetails': [{'modality': 'TEXT', 'tokenCount': 1176}], 'totalTokenCount': 1517}, 'invocationId': 'e-f23ae033-f4d6-47e8-9195-6e11710ef1de', 'author': 'InitialClassifier', 'actions': {'stateDelta': {'stage_init_classification': {'classified': [{'item': 'Coffee', 'quantity': '1', 'price': '3.50', 'category': 'Fast Food'}, {'item': 'Glass House Wine', 'quantity': '1', 'price': '9.95', 'category': 'Others'}, {'item': 'Jumbo Coctail Shrimp', 'quantity': '1', 'price': '12.95', 'category': 'Fast Food'}, {'item': 'Escargot Bourguigonne', 'quantity': '1', 'price': '10.95', 'category': 'Fast Food'}, {'item': 'Veal Zingaria', 'quantity': '1', 'price': '23.95', 'category': 'Fast Food'}, {'item': 'Duckling ala Arancio', 'quantity': '1', 'price': '25.95', 'category': 'Fast Food'}], 'total_values_dict': {'total_amount': '94.78', 'net_amount': '87.25', 'total_tax_amount': '7.53'}}}, 'artifactDelta': {}, 'requestedAuthConfigs': {}}, 'id': 'd6102c36-da55-4e64-8c9a-7a7ae0ffb6b1', 'timestamp': 1753038162.783302}, 
                    {'content': {'parts': [{'text': '{\n  "grouped": [\n    {\n      "category": "Fast Food",\n      "items": [\n        "Coffee",\n        "Jumbo Coctail Shrimp",\n        "Escargot Bourguigonne",\n        "Veal Zingaria",\n        "Duckling ala Arancio"\n      ],\n      "total_price": "77.35"\n    },\n    {\n      "category": "Others",\n      "items": [\n        "Glass House Wine"\n      ],\n      "total_price": "9.95"\n    }\n  ]\n}'}], 'role': 'model'}, 'usageMetadata': {'candidatesTokenCount': 134, 'candidatesTokensDetails': [{'modality': 'TEXT', 'tokenCount': 134}], 'promptTokenCount': 1479, 'promptTokensDetails': [{'modality': 'TEXT', 'tokenCount': 1479}], 'totalTokenCount': 1613}, 'invocationId': 'e-f23ae033-f4d6-47e8-9195-6e11710ef1de', 'author': 'grouping_classification', 'actions': {'stateDelta': {'grouped_classification': {'grouped': [{'category': 'Fast Food', 'items': ['Coffee', 'Jumbo Coctail Shrimp', 'Escargot Bourguigonne', 'Veal Zingaria', 'Duckling ala Arancio'], 'total_price': '77.35'}, {'category': 'Others', 'items': ['Glass House Wine'], 'total_price': '9.95'}]}}, 'artifactDelta': {}, 'requestedAuthConfigs': {}}, 'id': '8e447eaa-567f-45b3-9e2b-de937c6b59b7', 'timestamp': 1753038164.712276}, 
                    {'content': {'parts': [{'functionCall': {'id': 'adk-97975a57-959f-4a1b-a255-4a2f352a367d', 'args': {'data': [{'items': ['Coffee', 'Jumbo Coctail Shrimp', 'Escargot Bourguigonne', 'Veal Zingaria', 'Duckling ala Arancio'], 'category': 'Fast Food', 'total_price': '77.35'}, {'items': ['Glass House Wine'], 'category': 'Others', 'total_price': '9.95'}]}, 'name': 'calculate_final_total'}}], 'role': 'model'}, 'usageMetadata': {'candidatesTokenCount': 52, 'candidatesTokensDetails': [{'modality': 'TEXT', 'tokenCount': 52}], 'promptTokenCount': 1697, 'promptTokensDetails': [{'modality': 'TEXT', 'tokenCount': 1697}], 'totalTokenCount': 1749}, 'invocationId': 'e-f23ae033-f4d6-47e8-9195-6e11710ef1de', 'author': 'validate_classification', 'actions': {'stateDelta': {}, 'artifactDelta': {}, 'requestedAuthConfigs': {}}, 'longRunningToolIds': [], 'id': 'f388d72f-1fbc-40e8-a128-34e72be84a63', 'timestamp': 1753038165.859556}, 
                    {'content': {'parts': [{'functionResponse': {'id': 'adk-97975a57-959f-4a1b-a255-4a2f352a367d', 'name': 'calculate_final_total', 'response': {'result': 'success', 'final_total': 87.3, 'message': 'Successfully calculated final total: 87.3'}}}], 'role': 'user'}, 'invocationId': 'e-f23ae033-f4d6-47e8-9195-6e11710ef1de', 'author': 'validate_classification', 'actions': {'stateDelta': {'calculation_status': 'success'}, 'artifactDelta': {}, 'requestedAuthConfigs': {}}, 'id': 'a0dd4caa-5762-4ad9-845b-0510eee5f5d9', 'timestamp': 1753038166.732343},
                    {'content': {'parts': [{'functionCall': {'id': 'adk-008f71a6-f0c6-4470-8de4-1e7f9a34da57', 'args': {'data': {'classified': [{'price': '3.50', 'category': 'Fast Food', 'item': 'Coffee', 'quantity': '1'}, {'price': '9.95', 'category': 'Others', 'quantity': '1', 'item': 'Glass House Wine'}, {'quantity': '1', 'price': '12.95', 'category': 'Fast Food', 'item': 'Jumbo Coctail Shrimp'}, {'category': 'Fast Food', 'item': 'Escargot Bourguigonne', 'quantity': '1', 'price': '10.95'}, {'price': '23.95', 'item': 'Veal Zingaria', 'category': 'Fast Food', 'quantity': '1'}, {'category': 'Fast Food', 'price': '25.95', 'item': 'Duckling ala Arancio', 'quantity': '1'}], 'total_values_dict': {'net_amount': '87.25', 'total_amount': '94.78', 'total_tax_amount': '7.53'}}, 'final_total': 87.3}, 'name': 'exit_function'}}], 'role': 'model'}, 'usageMetadata': {'candidatesTokenCount': 132, 'candidatesTokensDetails': [{'modality': 'TEXT', 'tokenCount': 132}], 'promptTokenCount': 1771, 'promptTokensDetails': [{'modality': 'TEXT', 'tokenCount': 1771}], 'totalTokenCount': 1903}, 'invocationId': 'e-f23ae033-f4d6-47e8-9195-6e11710ef1de', 'author': 'validate_classification', 'actions': {'stateDelta': {}, 'artifactDelta': {}, 'requestedAuthConfigs': {}}, 'longRunningToolIds': [], 'id': 'fade21b1-50f4-4ef8-a5d1-032318a61b29', 'timestamp': 1753038166.736968},
                    {'content': {'parts': [{'functionResponse': {'id': 'adk-008f71a6-f0c6-4470-8de4-1e7f9a34da57', 'name': 'exit_function', 'response': {'status': 0, 'details': 'Computed total is 87.3, but expected 94.78 or 87.25. Please check the following categories and their prices for inconsistencies.'}}}], 'role': 'user'}, 'invocationId': 'e-f23ae033-f4d6-47e8-9195-6e11710ef1de', 'author': 'validate_classification', 'actions': {'stateDelta': {}, 'artifactDelta': {}, 'requestedAuthConfigs': {}}, 'id': 'f75c85fb-1dc7-495e-9172-5f585685134c', 'timestamp': 1753038168.2792},
                    {'content': {'parts': [{'text': '```json\n{"details": "Computed total is 87.3, but expected 94.78 or 87.25. Please check the following categories and their prices for inconsistencies.", "status": 0}\n```'}], 'role': 'model'}, 'usageMetadata': {'candidatesTokenCount': 51, 'candidatesTokensDetails': [{'modality': 'TEXT', 'tokenCount': 51}], 'promptTokenCount': 1945, 'promptTokensDetails': [{'modality': 'TEXT', 'tokenCount': 1945}], 'totalTokenCount': 1996}, 'invocationId': 'e-f23ae033-f4d6-47e8-9195-6e11710ef1de', 'author': 'validate_classification', 'actions': {'stateDelta': {'validation_result': '```json\n{"details": "Computed total is 87.3, but expected 94.78 or 87.25. Please check the following categories and their prices for inconsistencies.", "status": 0}\n```'}, 'artifactDelta': {}, 'requestedAuthConfigs': {}}, 'id': 'b1650b75-1e12-4a2e-b445-2263d09551a9', 'timestamp': 1753038168.282202},
                    {'content': {'parts': [{'text': '```json\n[\n    {\n      "category": "Fast Food",\n      "items": [\n        "Coffee",\n        "Jumbo Coctail Shrimp",\n        "Escargot Bourguigonne",\n        "Veal Zingaria",\n        "Duckling ala Arancio"\n      ],\n      "total_price": "77.35"\n    },\n    {\n      "category": "Others",\n      "items": [\n        "Glass House Wine"\n      ],\n      "total_price": "17.43"\n    }\n  ]\n```'}], 'role': 'model'}, 'usageMetadata': {'candidatesTokenCount': 132, 'candidatesTokensDetails': [{'modality': 'TEXT', 'tokenCount': 132}], 'promptTokenCount': 2449, 'promptTokensDetails': [{'modality': 'TEXT', 'tokenCount': 2449}], 'totalTokenCount': 2581}, 'invocationId': 'e-f23ae033-f4d6-47e8-9195-6e11710ef1de', 'author': 'refine_classifier', 'actions': {'stateDelta': {'grouped': '```json\n[\n    {\n      "category": "Fast Food",\n      "items": [\n        "Coffee",\n        "Jumbo Coctail Shrimp",\n        "Escargot Bourguigonne",\n        "Veal Zingaria",\n        "Duckling ala Arancio"\n      ],\n      "total_price": "77.35"\n    },\n    {\n      "category": "Others",\n      "items": [\n        "Glass House Wine"\n      ],\n      "total_price": "17.43"\n    }\n  ]\n```'}, 'artifactDelta': {}, 'requestedAuthConfigs': {}}, 'id': '415de8df-8a13-4eac-9673-db3775bcadf7', 'timestamp': 1753038168.93875},
                    {'content': {'parts': [{'functionCall': {'id': 'adk-34d7ad4c-1384-433e-b671-8f38b7f8bb99', 'args': {'data': [{'category': 'Fast Food', 'total_price': '77.35', 'items': ['Coffee', 'Jumbo Coctail Shrimp', 'Escargot Bourguigonne', 'Veal Zingaria', 'Duckling ala Arancio']}, {'total_price': '17.43', 'items': ['Glass House Wine'], 'category': 'Others'}]}, 'name': 'calculate_final_total'}}], 'role': 'model'}, 'usageMetadata': {'candidatesTokenCount': 53, 'candidatesTokensDetails': [{'modality': 'TEXT', 'tokenCount': 53}], 'promptTokenCount': 2138, 'promptTokensDetails': [{'modality': 'TEXT', 'tokenCount': 2138}], 'totalTokenCount': 2191}, 'invocationId': 'e-f23ae033-f4d6-47e8-9195-6e11710ef1de', 'author': 'validate_classification', 'actions': {'stateDelta': {}, 'artifactDelta': {}, 'requestedAuthConfigs': {}}, 'longRunningToolIds': [], 'id': '1d43f5a0-4692-4802-b579-9533c4db4483', 'timestamp': 1753038170.02081},
                    {'content': {'parts': [{'functionResponse': {'id': 'adk-34d7ad4c-1384-433e-b671-8f38b7f8bb99', 'name': 'calculate_final_total', 'response': {'result': 'success', 'final_total': 94.78, 'message': 'Successfully calculated final total: 94.78'}}}], 'role': 'user'}, 'invocationId': 'e-f23ae033-f4d6-47e8-9195-6e11710ef1de', 'author': 'validate_classification', 'actions': {'stateDelta': {'calculation_status': 'success'}, 'artifactDelta': {}, 'requestedAuthConfigs': {}}, 'id': '55a200be-7ecb-43bf-9cbe-47b2a3b9cb94', 'timestamp': 1753038170.921309},
                    {'content': {'parts': [{'functionCall': {'id': 'adk-5a6d4032-4e5b-479b-aa9f-e0abb9d7dba7', 'args': {'final_total': 94.78, 'data': {'total_values_dict': {'net_amount': '87.25', 'total_tax_amount': '7.53', 'total_amount': '94.78'}, 'classified': [{'category': 'Fast Food', 'item': 'Coffee', 'quantity': '1', 'price': '3.50'}, {'category': 'Others', 'item': 'Glass House Wine', 'price': '9.95', 'quantity': '1'}, {'price': '12.95', 'quantity': '1', 'category': 'Fast Food', 'item': 'Jumbo Coctail Shrimp'}, {'category': 'Fast Food', 'quantity': '1', 'price': '10.95', 'item': 'Escargot Bourguigonne'}, {'category': 'Fast Food', 'price': '23.95', 'quantity': '1', 'item': 'Veal Zingaria'}, {'item': 'Duckling ala Arancio', 'price': '25.95', 'category': 'Fast Food', 'quantity': '1'}]}}, 'name': 'exit_function'}}], 'role': 'model'}, 'usageMetadata': {'candidatesTokenCount': 132, 'candidatesTokensDetails': [{'modality': 'TEXT', 'tokenCount': 132}], 'promptTokenCount': 2214, 'promptTokensDetails': [{'modality': 'TEXT', 'tokenCount': 2214}], 'totalTokenCount': 2346}, 'invocationId': 'e-f23ae033-f4d6-47e8-9195-6e11710ef1de', 'author': 'validate_classification', 'actions': {'stateDelta': {}, 'artifactDelta': {}, 'requestedAuthConfigs': {}}, 'longRunningToolIds': [], 'id': '7963d837-d482-41ba-b816-cf9ec70bfb80', 'timestamp': 1753038170.924978},
                    {'content': {'parts': [{'functionResponse': {'id': 'adk-5a6d4032-4e5b-479b-aa9f-e0abb9d7dba7', 'name': 'exit_function', 'response': {'status': 1, 'details': 'Computed total matches the receipt total. Classification is valid. Exiting the refinement loop.'}}}], 'role': 'user'}, 'invocationId': 'e-f23ae033-f4d6-47e8-9195-6e11710ef1de', 'author': 'validate_classification', 'actions': {'stateDelta': {}, 'artifactDelta': {}, 'escalate': True, 'requestedAuthConfigs': {}}, 'id': '6daa1cc5-8aac-4b43-ad1b-9316ba937d27', 'timestamp': 1753038172.507788},
                    {'content': {'parts': [{'text': '```json\n{\n  "summary": "Final receipt classification summary.",\n  "categories": [\n    {\n      "category": "Fast Food",\n      "items": [\n        "Coffee",\n        "Jumbo Coctail Shrimp",\n        "Escargot Bourguigonne",\n        "Veal Zingaria",\n        "Duckling ala Arancio"\n      ],\n      "total_price": "77.35"\n    },\n    {\n      "category": "Others",\n      "items": [\n        "Glass House Wine"\n      ],\n      "total_price": "17.43"\n    }\n  ],\n  "final_total": 94.78,\n  "status": 1,\n  "notes": "Computed total matches the receipt total. Classification is valid."\n}\n```\n\n'}, {'functionCall': {'id': 'adk-0d52d981-0be9-4620-b5d8-011f980794e2', 'args': {'data': [{'category': 'Fast Food', 'total_price': '77.35', 'items': ['Coffee', 'Jumbo Coctail Shrimp', 'Escargot Bourguigonne', 'Veal Zingaria', 'Duckling ala Arancio']}, {'category': 'Others', 'items': ['Glass House Wine'], 'total_price': '17.43'}]}, 'name': 'save_to_firebase'}}], 'role': 'model'}, 'usageMetadata': {'candidatesTokenCount': 244, 'candidatesTokensDetails': [{'modality': 'TEXT', 'tokenCount': 244}], 'promptTokenCount': 2686, 'promptTokensDetails': [{'modality': 'TEXT', 'tokenCount': 2686}], 'totalTokenCount': 2930}, 'invocationId': 'e-f23ae033-f4d6-47e8-9195-6e11710ef1de', 'author': 'response_agent', 'actions': {'stateDelta': {}, 'artifactDelta': {}, 'requestedAuthConfigs': {}}, 'longRunningToolIds': [], 'id': '7dc62df5-2203-432b-af42-1109537ae9c7', 'timestamp': 1753038172.510478},
                    {
                        'content': {
                            'parts': [
                                {
                                    'functionResponse': {
                                        'id': 'adk-0d52d981-0be9-4620-b5d8-011f980794e2',
                                        'name': 'save_to_firebase',
                                        'response': {
                                            'result': 'success',
                                            'message': 'Data saved to Firebase.',
                                            'data': '[
                                                {
                                                    "category": "Fast Food",
                                                    "total_price": "77.35",
                                                    "items": [
                                                        "Coffee",
                                                        "Jumbo Coctail Shrimp",
                                                        "Escargot Bourguigonne",
                                                        "Veal Zingaria",
                                                        "Duckling ala Arancio"
                                                    ]
                                                },
                                                {
                                                    "category": "Others",
                                                    "items": [
                                                        "Glass House Wine"
                                                    ],
                                                    "total_price": "17.43"
                                                }
                                            ]'
                                        }
                                    }
                                }
                            ],
                            'role': 'user'
                        },
                        'invocationId': 'e-f23ae033-f4d6-47e8-9195-6e11710ef1de',
                        'author': 'response_agent',
                        'actions': {
                            'stateDelta': {},
                            'artifactDelta': {},
                            'requestedAuthConfigs': {}
                        },
                        'id': '1f2f6371-cad2-4f53-80b2-feb58cdb6442',
                        'timestamp': 1753038174.434992
                    },
                    {
                        'content': {
                            'parts': [
                                {
                                    'text': '```json\n{"save_to_firebase_response": {"data": "[{\\"category\\": \\"Fast Food\\", \\"total_price\\": \\"77.35\\", \\"items\\": [\\"Coffee\\", \\"Jumbo Coctail Shrimp\\", \\"Escargot Bourguigonne\\", \\"Veal Zingaria\\", \\"Duckling ala Arancio\\"]}, {\\"category\\": \\"Others\\", \\"items\\": [\\"Glass House Wine\\"], \\"total_price\\": \\"17.43\\"}]", "message": "Data saved to Firebase.", "result": "success"}}\n```'
                                }
                            ], 'role': 'model'
                        },
                        'usageMetadata': {
                            'candidatesTokenCount': 119,
                            'candidatesTokensDetails': [
                                {
                                    'modality': 'TEXT',
                                    'tokenCount': 119
                                }
                            ],
                            'promptTokenCount': 3026,
                            'promptTokensDetails': [
                                {
                                    'modality': 'TEXT',
                                    'tokenCount': 3026
                                }
                            ],
                            'totalTokenCount': 3145
                        }, 
                        'invocationId': 'e-f23ae033-f4d6-47e8-9195-6e11710ef1de',
                        'author': 'response_agent',
                        'actions': {
                            'stateDelta': {
                                'firebase_save_result': '```json\n{"save_to_firebase_response": {"data": "[{\\"category\\": \\"Fast Food\\", \\"total_price\\": \\"77.35\\", \\"items\\": [\\"Coffee\\", \\"Jumbo Coctail Shrimp\\", \\"Escargot Bourguigonne\\", \\"Veal Zingaria\\", \\"Duckling ala Arancio\\"]}, {\\"category\\": \\"Others\\", \\"items\\": [\\"Glass House Wine\\"], \\"total_price\\": \\"17.43\\"}]", "message": "Data saved to Firebase.", "result": "success"}}\n```'
                            }, 
                            'artifactDelta': {},
                            'requestedAuthConfigs': {}
                        },
                        'id': '1a378154-8f88-4640-b3b9-847547999391',
                        'timestamp': 1753038174.438933
                    }
                ]
        '''
        if not all_events:
            return {}
        last_event = all_events[-1]
        logging.info(f"Last event: {last_event}")
        content = last_event.get('content', {})
        parts = content.get('parts', [])
        if not parts:
            return {}
        part = parts[0]  # usually only one, else loop if you want all
        if 'text' in part: # Handle text part
            text = part['text']
        elif 'functionResponse' in part: # Handle functionResponse part
            fr = part['functionResponse']['response']
            # text = fr.get('data', '')
            # if isinstance(text, dict) or isinstance(text, list):
            #     text = json.dumps(text)
            # else: # elif isinstance(text, str):
            #     # text = text.strip()
            #     pass
            logging.info(f"Extracted functionCall: {fc}")
            return {'type': 'functionCall', 'value': fc}
        elif 'functionCall' in part: # Handle functionCall part
            fc = part['functionCall']
            logging.info(f"Extracted functionResponse: {fr}")
            return {'type': 'functionResponse', 'value': fr}
        else:
            text = None
        if not text:
            return {}
        logging.info(f"Extracted text: {text}")
        # If the text is a Markdown code block, remove the ```json ... ```
        if text.startswith('```json'):
            text = text.replace('```json\n', '').replace('\n```', '').strip()
        try:
            value = json.loads(text)
            logging.info(f"Parsed JSON: {value}")
            return value
        except Exception as e:
            logging.warning(f"Failed to parse JSON: {e}")
            return {}