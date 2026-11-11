"""AI-powered voice-order processing service."""

import json
import re
from typing import Any

import httpx
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.db.models import MenuItem
from app.schemas.ai import CartAction, VoiceOrderResponse


# ── Exhaustive Multilingual Number Mapping ──────────────────────────────
_NUMBER_WORDS: dict[str, int] = {
    # English
    "a": 1, "an": 1, "one": 1, "single": 1,
    "two": 2, "couple": 2, "pair": 2, "double": 2,
    "three": 3, "triple": 3,
    "four": 4, "five": 5, "six": 6, "seven": 7, "eight": 8, "nine": 9, "ten": 10,

    # Hindi / Hinglish / Urdu
    "ek": 1, "aik": 1,
    "do": 2, "dho": 2, "dono": 2,
    "teen": 3, "tin": 3,
    "char": 4, "chaar": 4,
    "paanch": 5, "panch": 5,
    "chhe": 6, "che": 6, "chheh": 6,
    "saat": 7, "sat": 7,
    "aath": 8, "ath": 8,
    "nau": 9, "no": 9,
    "das": 10, "dus": 10,

    # Kannada
    "ondu": 1, "vandu": 1,
    "eradu": 2, "erad": 2,
    "mooru": 3, "muru": 3,
    "naalku": 4, "nalku": 4,
    "aidu": 5, "aaidu": 5,
    "aaru": 6, "aru": 6,
    "eelu": 7, "elu": 7,
    "entu": 8, "yentu": 8,
    "ombattu": 9, "ombathu": 9,
    "hattu": 10,

    # Tamil
    "ondru": 1, "oru": 1, "onnu": 1,
    "rendu": 2, "irandu": 2,
    "moonu": 3, "moondru": 3,
    "naalu": 4, "naangu": 4,
    "anju": 5, "aindhu": 5,
    "aaru_ta": 6,
    "yezhu": 7, "ezhu": 7,
    "ettu": 8,
    "ombadhu": 9, "onpathu": 9,
    "patthu": 10, "pathu": 10,

    # Telugu
    "okati": 1, "oka": 1, "okti": 1,
    "rendu_te": 2,
    "moodu": 3, "mudu": 3,
    "naalugu": 4, "nalugu": 4,
    "aidu_te": 5,
    "aaru_te": 6,
    "edu": 7, "yedu": 7,
    "enimidi": 8,
    "tommidi": 9, "thommidi": 9,
    "padi": 10,
}

# ── Common Voice Synonyms & Aliases ────────────────────────────────────
_ITEM_SYNONYMS: dict[str, list[str]] = {
    # Starters
    "Paneer Tikka": ["paneer tikka", "tikka paneer", "tandoori paneer", "panner tikka"],
    "Crispy Chilli Baby Corn": ["chilli baby corn", "baby corn", "crispy corn", "chilli corn", "babycorn"],
    "Gobi 65": ["gobi 65", "cauliflower 65", "gobi sixty five"],
    "Hara Bhara Kebab": ["hara bhara kebab", "hara bhara kabab", "veg kebab", "hara bhara"],

    # Chinese
    "Veg Hakka Noodles": ["hakka noodles", "veg noodles", "noodles", "chowmein", "noddles"],
    "Gobi Manchurian": ["gobi manchurian", "manchurian", "manchurian dry", "cauliflower manchurian"],
    "Chilli Paneer": ["chilli paneer", "paneer chilli", "chili paneer", "paneer chilly"],
    "Schezwan Fried Rice": ["schezwan fried rice", "fried rice", "schezwan rice", "chinese rice"],

    # Rotis & Breads
    "Butter Naan": ["butter naan", "naan", "butternaan"],
    "Garlic Naan": ["garlic naan", "garlic butter naan"],
    "Tandoori Roti": ["tandoori roti", "roti", "butter roti", "chapati", "rotis"],
    "Malabar Parotta": ["malabar parotta", "parotta", "kerala parotta", "paratha", "porotta"],

    # Artisan Brews & Beverages
    "Filter Coffee": ["filter coffee", "kaapi", "south indian coffee", "degree coffee", "coffee"],
    "Masala Chai": ["masala chai", "masala tea", "chai", "tea", "adrak chai", "ginger tea"],
    "Cold Coffee": ["cold coffee", "iced coffee", "chilled coffee"],
    "Biscoff Frappe": ["biscoff frappe", "biscoff shake", "lotus biscoff", "frappe", "thick shake"],
    "Lemon Soda": ["lemon soda", "fresh lime soda", "lime soda", "nimbu soda", "lemon juice"],

    # South Indian Tiffins
    "Masala Dosa": ["masala dosa", "dosa", "masale dose", "masala dose", "dosai"],
    "Ghee Roast Dosa": ["ghee roast", "ghee roast dosa", "ghee dosa", "crispy ghee dosa"],
    "Idli Sambar": ["idli sambar", "idli", "idly", "idlis", "steamed idli"],
    "Poha": ["poha", "avalakki", "kanda poha"],

    # Meals & Curries
    "Paneer Butter Masala": ["paneer butter masala", "paneer makhani", "paneer curry", "butter paneer"],
    "Dal Makhani": ["dal makhani", "dal makhni", "black dal", "makhani dal"],
    "Thali Meals": ["thali meals", "thali", "full meals", "south indian meals", "lunch thali"],
    "Curd Rice": ["curd rice", "thayir sadam", "mosaranna", "dahi chawal"],

    # Snacks & Desserts
    "Samosa": ["samosa", "samosas", "samose", "aloo samosa"],
    "Vada Pav": ["vada pav", "wada pav", "vada pao"],
    "Gulab Jamun": ["gulab jamun", "jamun", "gulab jamuns", "gulaab jamun"],
    "Ras Malai": ["ras malai", "rasmalai", "rossomalai"],
    "Sizzling Brownie": ["sizzling brownie", "brownie", "brownie with ice cream", "hot brownie"],
}


def _clean_name(name: str) -> str:
    """Strip parenthesis or count info, e.g. 'Samosa (2 pcs)' -> 'Samosa'."""
    return re.sub(r"\(.*?\)", "", name).strip().lower()


def _keyword_fallback(transcript: str, menu_items: list[MenuItem]) -> list[CartAction]:
    """
    Robust NLP keyword & synonym matcher with bidirectional quantity extraction
    supporting English, Hindi, Kannada, Tamil, and Telugu expressions.
    """
    text = transcript.lower().strip()
    # Normalize punctuation and extra spaces
    text = re.sub(r"[,;!?.+]+", " ", text)
    words = text.split()

    actions: list[CartAction] = []
    matched_ids: set[int] = set()

    # Map name -> item
    item_by_name = {m.name: m for m in menu_items if m.available}

    # Match each item via synonyms or direct name
    for canonical_name, aliases in _ITEM_SYNONYMS.items():
        # Find corresponding menu item in DB
        db_item = item_by_name.get(canonical_name)
        if not db_item or db_item.id in matched_ids:
            # Try fuzzy matching canonical_name with DB items
            for item in menu_items:
                if item.id not in matched_ids and _clean_name(item.name) == _clean_name(canonical_name):
                    db_item = item
                    break
        if not db_item or db_item.id in matched_ids:
            continue

        # Check if any alias occurs in the transcript text
        matched_alias = None
        matched_idx = -1
        # Test longest alias first
        sorted_aliases = sorted(aliases, key=len, reverse=True)
        for alias in sorted_aliases:
            # Use word boundary check
            pattern = r"\b" + re.escape(alias) + r"\b"
            m = re.search(pattern, text)
            if m:
                matched_alias = alias
                matched_idx = m.start()
                break

        if not matched_alias:
            continue

        matched_ids.add(db_item.id)

        # ── Quantity Extraction (Checks Before & After) ───────────────
        quantity = 1

        # 1. Check words preceding the item (e.g. "2 masala dosa", "do cold coffee")
        preceding = text[:matched_idx].strip().split()
        if preceding:
            last = preceding[-1]
            if last.isdigit():
                quantity = int(last)
            elif last in _NUMBER_WORDS:
                quantity = _NUMBER_WORDS[last]

        # 2. If no quantity found before, check words immediately following (e.g. "masala dosa 2", "filter coffee ek")
        if quantity == 1:
            after = text[matched_idx + len(matched_alias):].strip().split()
            if after:
                first = after[0]
                if first.isdigit():
                    quantity = int(first)
                elif first in _NUMBER_WORDS:
                    quantity = _NUMBER_WORDS[first]

        quantity = max(1, min(quantity, 50))

        actions.append(CartAction(
            action="add",
            menu_item_id=db_item.id,
            item_name=db_item.name,
            quantity=quantity,
            price=db_item.price,
        ))

    # Also check any DB items not in the synonym table
    for item in sorted(menu_items, key=lambda m: len(m.name), reverse=True):
        if item.id in matched_ids or not item.available:
            continue
        cleaned = _clean_name(item.name)
        pattern = r"\b" + re.escape(cleaned) + r"\b"
        m = re.search(pattern, text)
        if m:
            matched_ids.add(item.id)
            idx = m.start()
            quantity = 1
            pre = text[:idx].strip().split()
            if pre:
                last = pre[-1]
                if last.isdigit():
                    quantity = int(last)
                elif last in _NUMBER_WORDS:
                    quantity = _NUMBER_WORDS[last]
            if quantity == 1:
                after = text[idx + len(cleaned):].strip().split()
                if after:
                    first = after[0]
                    if first.isdigit():
                        quantity = int(first)
                    elif first in _NUMBER_WORDS:
                        quantity = _NUMBER_WORDS[first]

            quantity = max(1, min(quantity, 50))
            actions.append(CartAction(
                action="add",
                menu_item_id=item.id,
                item_name=item.name,
                quantity=quantity,
                price=item.price,
            ))

    return actions


def _build_system_prompt(menu_items: list[MenuItem]) -> str:
    """Build the system prompt for the Groq model."""
    menu_text = "\n".join(
        f"- ID:{m.id} | {m.emoji} {m.name} ({m.category}) | ₹{m.price} | {'Available' if m.available else 'Unavailable'}"
        for m in menu_items
    )

    return f"""You are Barista Arjun, the friendly, welcoming AI barista at Brew Talk Cafe.
A customer is placing their order by voice.

MENU:
{menu_text}

INSTRUCTIONS:
1. Parse the transcript into cart actions with exact menu item IDs, names, and quantities.
2. Prices MUST be exact from the menu above.
3. Quantities may be in English, Hindi, Kannada, Tamil, or Telugu. Map them accurately.
4. ALWAYS reply in English regardless of the input language. Be warm, brief, and conversational.
   Good examples: "Perfect! Adding 2 Masala Dosa to your tray ☕", "Done! Shall I add a dessert too?"
5. Keep the reply under 2 sentences.

JSON FORMAT ONLY:
{{
  "reply": "Friendly English response",
  "cart_actions": [
    {{
      "action": "add",
      "menu_item_id": 1,
      "item_name": "Exact Name",
      "quantity": 2,
      "price": 40.0
    }}
  ]
}}
"""


def _validate_cart_actions(
    raw_actions: list[dict[str, Any]],
    menu_map: dict[int, MenuItem],
) -> list[CartAction]:
    validated: list[CartAction] = []
    for action in raw_actions:
        mid = action.get("menu_item_id")
        if mid not in menu_map:
            continue
        db_item = menu_map[mid]
        if not db_item.available:
            continue
        qty = max(1, min(int(action.get("quantity", 1)), 50))
        validated.append(CartAction(
            action=action.get("action", "add"),
            menu_item_id=db_item.id,
            item_name=db_item.name,
            quantity=qty,
            price=db_item.price,  # ALWAYS from DB
        ))
    return validated


async def process_voice_order(
    transcript: str,
    language: str,
    menu_items: list[MenuItem],
    db: Session,
) -> VoiceOrderResponse:
    """
    Process a voice transcript and return a localized reply with cart actions.
    Uses Groq API if key is present in DB settings or env; otherwise uses the NLP parser.
    """
    settings = get_settings()
    menu_map = {m.id: m for m in menu_items if m.available}

    # Read Groq API key from DB first (live, no restart needed), fall back to env
    db_groq_key = ""
    db_groq_model = ""
    try:
        from app.db.models import Setting as SettingModel
        key_row = db.query(SettingModel).filter(SettingModel.key == "groq_api_key").first()
        model_row = db.query(SettingModel).filter(SettingModel.key == "groq_model").first()
        db_groq_key = (key_row.value or "").strip() if key_row else ""
        db_groq_model = (model_row.value or "").strip() if model_row else ""
    except Exception:
        pass

    groq_api_key = db_groq_key or settings.GROQ_API_KEY
    groq_model = db_groq_model or settings.GROQ_MODEL or "llama3-8b-8192"

    # ── Groq AI path ──────────────────────────────────────────────────
    if groq_api_key:
        try:
            system_prompt = _build_system_prompt(menu_items)
            async with httpx.AsyncClient(timeout=12.0) as client:
                response = await client.post(
                    "https://api.groq.com/openai/v1/chat/completions",
                    headers={
                        "Authorization": f"Bearer {groq_api_key}",
                        "Content-Type": "application/json",
                    },
                    json={
                        "model": groq_model,
                        "messages": [
                            {"role": "system", "content": system_prompt},
                            {"role": "user", "content": transcript},
                        ],
                        "temperature": 0.2,
                        "max_tokens": 800,
                    },
                )
                response.raise_for_status()

            data = response.json()
            content = data["choices"][0]["message"]["content"].strip()
            if content.startswith("```"):
                content = re.sub(r"^```(?:json)?\s*", "", content)
                content = re.sub(r"\s*```$", "", content)

            parsed = json.loads(content)
            reply = parsed.get("reply", "I've added the items to your tray!")
            raw_actions = parsed.get("cart_actions", [])
            validated_actions = _validate_cart_actions(raw_actions, menu_map)

            if validated_actions:
                return VoiceOrderResponse(
                    reply=reply,
                    cart_actions=validated_actions,
                    language=language,
                )
        except Exception:
            # Fall through to robust keyword matcher
            pass

    # ── Advanced Multilingual NLP Fallback ────────────────────────────
    actions = _keyword_fallback(transcript, [m for m in menu_items if m.available])

    if actions:
        items_summary = ", ".join(f"{a.quantity}x {a.item_name}" for a in actions)
        reply = f"Perfect! I've added {items_summary} to your tray. Anything else? ☕"
    else:
        reply = "I couldn't match that to our menu. Try saying something like '2 Masala Dosa and one Filter Coffee' or tap any item on the menu!"

    return VoiceOrderResponse(
        reply=reply,
        cart_actions=actions,
        language=language,
    )


async def process_audio_order(
    audio_base64: str,
    mime_type: str,
    language: str,
    menu_items: list[MenuItem],
    db: Session,
) -> VoiceOrderResponse:
    """
    Transcribe raw recorded audio using Groq Whisper (whisper-large-v3),
    then parse and process the order.
    """
    import base64
    settings = get_settings()
    db_groq_key = ""
    try:
        from app.db.models import Setting as SettingModel
        key_row = db.query(SettingModel).filter(SettingModel.key == "groq_api_key").first()
        db_groq_key = (key_row.value or "").strip() if key_row else ""
    except Exception:
        pass

    groq_api_key = db_groq_key or settings.GROQ_API_KEY
    if not groq_api_key:
        return VoiceOrderResponse(
            reply="To use direct mic recording, add your free Groq API key in Admin Settings, or use the quick buttons below! ☕",
            cart_actions=[],
            language=language,
        )

    try:
        audio_bytes = base64.b64decode(audio_base64)
        ext = "webm" if "webm" in mime_type else ("wav" if "wav" in mime_type else "mp4")
        filename = f"voice_order.{ext}"

        async with httpx.AsyncClient(timeout=15.0) as client:
            response = await client.post(
                "https://api.groq.com/openai/v1/audio/transcriptions",
                headers={"Authorization": f"Bearer {groq_api_key}"},
                files={"file": (filename, audio_bytes, mime_type)},
                data={"model": "whisper-large-v3", "language": "en"},
            )
            response.raise_for_status()
            transcription = response.json().get("text", "").strip()

        if transcription:
            return await process_voice_order(
                transcript=transcription,
                language=language,
                menu_items=menu_items,
                db=db,
            )
    except Exception as e:
        print(f"[audio_order] Whisper error: {e}")

    return VoiceOrderResponse(
        reply="Could not transcribe audio. Please tap mic again and speak clearly, or use the quick buttons below!",
        cart_actions=[],
        language=language,
    )

