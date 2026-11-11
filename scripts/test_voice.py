import urllib.request
import json
import sys

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

tests = [
    ('do butter naan aur ek chilli paneer', 'hi-IN'),
    ('2 paneer tikka, hakka noodles 1, aur biscoff frappe ek', 'hi-IN'),
    ('eradu tandoori roti mathu gobi manchurian', 'kn-IN'),
    ('rendu filter coffee', 'ta-IN'),
    ('1 sizzling brownie and 2 masala chai', 'en-IN'),
]

for transcript, lang in tests:
    data = json.dumps({'transcript': transcript, 'language': lang, 'table_number': 1}).encode()
    req = urllib.request.Request('http://localhost:8000/api/ai/voice-order', data=data, headers={'Content-Type': 'application/json'}, method='POST')
    with urllib.request.urlopen(req) as resp:
        res = json.loads(resp.read())
        print(f'=== INPUT ({lang}): "{transcript}" ===')
        print('REPLY:', res['reply'])
        print('CART ACTIONS:')
        for a in res['cart_actions']:
            print(f'   -> {a["quantity"]}x {a["item_name"]} (@ Rs.{a["price"]})')
        print()
