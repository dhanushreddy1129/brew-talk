import urllib.request
import json
import sys

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

english_tests = [
    "two butter naan and one chilli paneer",
    "can I get 2 masala dosa and 1 filter coffee",
    "I would like two paneer tikka, one hakka noodles and 2 biscoff frappe",
    "give me 3 garlic naan and 1 dal makhani",
    "one sizzling brownie and two cold coffee please",
    "two tandoori roti with paneer butter masala",
    "1 thali meals and 2 gulab jamun",
]

print("TESTING ENGLISH VOICE ORDERS:")
print("=" * 50)
for text in english_tests:
    data = json.dumps({'transcript': text, 'language': 'en-US', 'table_number': 1}).encode()
    req = urllib.request.Request('http://localhost:8000/api/ai/voice-order', data=data, headers={'Content-Type': 'application/json'}, method='POST')
    with urllib.request.urlopen(req) as resp:
        res = json.loads(resp.read())
        print(f'User Said: "{text}"')
        print('Barista Reply:', res['reply'])
        print('Items Added to Tray:')
        for a in res['cart_actions']:
            print(f'   -> {a["quantity"]}x {a["item_name"]} (Rs. {a["price"]})')
        print("-" * 50)
