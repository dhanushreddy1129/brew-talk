"""Seed the database with initial menu items and settings."""

from sqlalchemy.orm import Session

from app.db.models import MenuItem, Setting


def seed_database(db: Session) -> None:
    """Populate the database with default data ONLY if menu_items is empty."""

    # Check if menu items already exist
    if db.query(MenuItem).first() is not None:
        return

    # ── Settings ───────────────────────────────────────────────────────
    settings_data = [
        # Branding
        ("cafe_name", "Brew Talk", "branding", "Name of the café"),
        ("cafe_tagline", "Artisanal Voice-Order Cafe", "branding", "Tagline shown across pages"),
        # Pricing
        ("currency", "₹", "pricing", "Currency symbol"),
        ("tax_percent", "5", "pricing", "Tax percentage applied to subtotal"),
        ("service_charge_percent", "3", "pricing", "Service charge percentage applied to subtotal"),
        # Colors
        ("color_primary", "#3C2415", "branding", "Primary color — espresso brown"),
        ("color_secondary", "#D4A574", "branding", "Secondary color — warm tan"),
        ("color_accent", "#7FB685", "branding", "Accent color — mint"),
        ("color_background", "#FDF6EC", "branding", "Background color — cream"),
        ("color_surface", "#FFFFFF", "branding", "Surface / card color"),
        ("color_text", "#2C1810", "branding", "Main text color"),
        ("color_text_light", "#8B7355", "branding", "Secondary text color"),
        # General
        ("total_tables", "12", "general", "Total number of tables in the café"),
        ("order_statuses", "New,Preparing,Ready,Delivered", "general", "Comma-separated list of order statuses"),
        ("status_labels", "Order Received,In Kitchen,Ready for Pickup,Delivered to Table", "labels", "Customer-facing status labels"),
        # AI / Groq
        ("groq_api_key", "", "ai", "Groq API key — get a free key at console.groq.com"),
        ("groq_model", "llama3-8b-8192", "ai", "Groq model to use (e.g. llama3-8b-8192, mixtral-8x7b-32768)"),
    ]

    for key, value, category, description in settings_data:
        existing = db.query(Setting).filter(Setting.key == key).first()
        if not existing:
            db.add(Setting(key=key, value=value, category=category, description=description))

    # ── Menu Items (Starters, Chinese, Rotis, Brews, Tiffins, Meals, Desserts) ──
    menu_items = [
        # 🥗 STARTERS
        MenuItem(
            name="Paneer Tikka", category="Starters", price=160,
            description="Tender cubes of fresh cottage cheese marinated in hung curd, Kashmiri spices & charred in the tandoor",
            emoji="🧀", image_url="https://images.unsplash.com/photo-1567188040759-fb8a883dc6d8?auto=format&fit=crop&w=600&q=80", sort_order=1,
        ),
        MenuItem(
            name="Crispy Chilli Baby Corn", category="Starters", price=140,
            description="Golden battered baby corn tossed in a spicy, tangy wok sauce with spring onions & capsicum",
            emoji="🌽", image_url="https://images.unsplash.com/photo-1540420773420-3366772f4999?auto=format&fit=crop&w=600&q=80", sort_order=2,
        ),
        MenuItem(
            name="Gobi 65", category="Starters", price=120,
            description="Crispy spiced cauliflower florets tossed with aromatic curry leaves, mustard seeds & crushed peppercorns",
            emoji="🥦", image_url="https://images.unsplash.com/photo-1546833999-b9f581a1996d?auto=format&fit=crop&w=600&q=80", sort_order=3,
        ),
        MenuItem(
            name="Hara Bhara Kebab", category="Starters", price=130,
            description="Pan-seared spinach, green pea & potato patties infused with roasted cumin & chaat masala",
            emoji="🥙", image_url="https://images.unsplash.com/photo-1601050690597-df0568f70950?auto=format&fit=crop&w=600&q=80", sort_order=4,
        ),

        # 🥢 CHINESE
        MenuItem(
            name="Veg Hakka Noodles", category="Chinese", price=130,
            description="Wok-tossed noodles with crunchy julienned vegetables, white pepper, dark soy & aromatic sesame oil",
            emoji="🍜", image_url="https://images.unsplash.com/photo-1585032226651-759b368d7246?auto=format&fit=crop&w=600&q=80", sort_order=5,
        ),
        MenuItem(
            name="Gobi Manchurian", category="Chinese", price=125,
            description="Crunchy cauliflower fritters tossed with fresh ginger, garlic, green chillies & spicy Manchurian glaze",
            emoji="🥡", image_url="https://images.unsplash.com/photo-1546833999-b9f581a1996d?auto=format&fit=crop&w=600&q=80", sort_order=6,
        ),
        MenuItem(
            name="Chilli Paneer", category="Chinese", price=150,
            description="Crispy paneer cubes sautéed with green bell peppers, shallots & fiery Indo-Chinese chilli garlic sauce",
            emoji="🌶️", image_url="https://images.unsplash.com/photo-1567188040759-fb8a883dc6d8?auto=format&fit=crop&w=600&q=80", sort_order=7,
        ),
        MenuItem(
            name="Schezwan Fried Rice", category="Chinese", price=135,
            description="Fragrant long-grain rice tossed in house Schezwan chili paste with garden vegetables & scallions",
            emoji="🍚", image_url="https://images.unsplash.com/photo-1603133872878-684f208fb84b?auto=format&fit=crop&w=600&q=80", sort_order=8,
        ),

        # 🫓 ROTIS & BREADS
        MenuItem(
            name="Butter Naan", category="Rotis & Breads", price=45,
            description="Traditional clay-oven flatbread brushed with generous melted farm butter",
            emoji="🫓", image_url="https://images.unsplash.com/photo-1601050690597-df0568f70950?auto=format&fit=crop&w=600&q=80", sort_order=9,
        ),
        MenuItem(
            name="Garlic Naan", category="Rotis & Breads", price=55,
            description="Fluffy tandoor naan topped with minced roasted garlic cloves, fresh cilantro & ghee",
            emoji="🧄", image_url="https://images.unsplash.com/photo-1601050690597-df0568f70950?auto=format&fit=crop&w=600&q=80", sort_order=10,
        ),
        MenuItem(
            name="Tandoori Roti", category="Rotis & Breads", price=30,
            description="Wholesome whole-wheat bread baked to perfection in the fiery clay oven",
            emoji="🥖", image_url="https://images.unsplash.com/photo-1509722747041-616f39b57569?auto=format&fit=crop&w=600&q=80", sort_order=11,
        ),
        MenuItem(
            name="Malabar Parotta", category="Rotis & Breads", price=40,
            description="Flaky, layered South Indian ribbon parotta kneaded with ghee and griddled golden",
            emoji="🥐", image_url="https://images.unsplash.com/photo-1589301760014-d929f3979dbc?auto=format&fit=crop&w=600&q=80", sort_order=12,
        ),

        # ☕ ARTISAN BREWS & BEVERAGES
        MenuItem(
            name="Filter Coffee", category="Beverages", price=40,
            description="Authentic South Indian degree filter coffee brewed with freshly roasted chicory beans & frothed milk",
            emoji="☕", image_url="https://images.unsplash.com/photo-1514432324607-a09d9b4aefdd?auto=format&fit=crop&w=600&q=80", sort_order=13,
        ),
        MenuItem(
            name="Masala Chai", category="Beverages", price=30,
            description="Rich spiced tea simmered with fresh crushed ginger, green cardamom, and cloves",
            emoji="🍵", image_url="https://images.unsplash.com/photo-1576092768241-dec231879fc3?auto=format&fit=crop&w=600&q=80", sort_order=14,
        ),
        MenuItem(
            name="Cold Coffee", category="Beverages", price=80,
            description="Creamy chilled espresso blended with artisanal vanilla bean ice cream & chocolate drizzle",
            emoji="🧋", image_url="https://images.unsplash.com/photo-1517701550927-30cf4ba1dba5?auto=format&fit=crop&w=600&q=80", sort_order=15,
        ),
        MenuItem(
            name="Biscoff Frappe", category="Beverages", price=120,
            description="Decadent thick blended coffee frappe topped with crushed Lotus Biscoff cookies and caramel swirl",
            emoji="🥤", image_url="https://images.unsplash.com/photo-1572490122747-3968b75cc699?auto=format&fit=crop&w=600&q=80", sort_order=16,
        ),
        MenuItem(
            name="Lemon Soda", category="Beverages", price=50,
            description="Fizzy refreshing lime soda prepared sweet or salted with fresh garden mint leaves",
            emoji="🍋", image_url="https://images.unsplash.com/photo-1513558161293-cdaf765ed2fd?auto=format&fit=crop&w=600&q=80", sort_order=17,
        ),

        # 🍳 SOUTH INDIAN TIFFINS
        MenuItem(
            name="Masala Dosa", category="Breakfast", price=70,
            description="Crispy golden fermented crepe stuffed with fragrant spiced potato masala & served with trio chutneys",
            emoji="🫓", image_url="https://images.unsplash.com/photo-1668236543090-82eba5ee5976?auto=format&fit=crop&w=600&q=80", sort_order=18,
        ),
        MenuItem(
            name="Ghee Roast Dosa", category="Breakfast", price=85,
            description="Paper-thin cone dosa roasted in pure desi ghee until deep golden and fragrant",
            emoji="🥞", image_url="https://images.unsplash.com/photo-1668236543090-82eba5ee5976?auto=format&fit=crop&w=600&q=80", sort_order=19,
        ),
        MenuItem(
            name="Idli Sambar", category="Breakfast", price=50,
            description="Melt-in-mouth steamed rice cakes served with piping hot lentil sambar & coconut chutney",
            emoji="🍚", image_url="https://images.unsplash.com/photo-1589301760014-d929f3979dbc?auto=format&fit=crop&w=600&q=80", sort_order=20,
        ),
        MenuItem(
            name="Poha", category="Breakfast", price=40,
            description="Flattened rice tossed with roasted peanuts, turmeric, mild chillies & fresh coriander",
            emoji="🍛", image_url="https://images.unsplash.com/photo-1601050690597-df0568f70950?auto=format&fit=crop&w=600&q=80", sort_order=21,
        ),
        MenuItem(
            name="Samosa", category="Snacks", price=30,
            description="Two crispy flaky pastry pockets filled with savoury spiced potatoes, tender peas & tamarind dip",
            emoji="🥟", image_url="https://images.unsplash.com/photo-1601050690597-df0568f70950?auto=format&fit=crop&w=600&q=80", sort_order=22,
        ),
        MenuItem(
            name="Vada Pav", category="Snacks", price=35,
            description="Mumbai batata vada sandwiched in soft pav with spicy red garlic chutney & green chilli",
            emoji="🍔", image_url="https://images.unsplash.com/photo-1606491956689-2ea866880c84?auto=format&fit=crop&w=600&q=80", sort_order=23,
        ),

        # 🍲 CURRIES & MEALS
        MenuItem(
            name="Paneer Butter Masala", category="Meals", price=170,
            description="Rich, buttery tomato-cashew makhani gravy loaded with soft paneer cubes & cream",
            emoji="🍲", image_url="https://images.unsplash.com/photo-1631452180519-c014fe946bc7?auto=format&fit=crop&w=600&q=80", sort_order=24,
        ),
        MenuItem(
            name="Dal Makhani", category="Meals", price=150,
            description="Slow-cooked black lentils simmered overnight with butter, cream, and subtle smoky spices",
            emoji="🥣", image_url="https://images.unsplash.com/photo-1546833999-b9f581a1996d?auto=format&fit=crop&w=600&q=80", sort_order=25,
        ),
        MenuItem(
            name="Thali Meals", category="Meals", price=120,
            description="Wholesome platter of steamed rice, sambar, rasam, 2 curries, curd, papad & pickle",
            emoji="🍱", image_url="https://images.unsplash.com/photo-1610057099443-fde8c4d50f91?auto=format&fit=crop&w=600&q=80", sort_order=26,
        ),
        MenuItem(
            name="Curd Rice", category="Meals", price=60,
            description="Comforting South Indian yogurt rice tempered with mustard, ginger, green chillies & pomegranate",
            emoji="🍚", image_url="https://images.unsplash.com/photo-1546833999-b9f581a1996d?auto=format&fit=crop&w=600&q=80", sort_order=27,
        ),

        # 🍨 DESSERTS
        MenuItem(
            name="Gulab Jamun", category="Desserts", price=50,
            description="Two warm melt-in-mouth milk dumplings steeped in pure saffron and rose petal syrup",
            emoji="🍩", image_url="https://images.unsplash.com/photo-1605197143977-90c0efad57ce?auto=format&fit=crop&w=600&q=80", sort_order=28,
        ),
        MenuItem(
            name="Ras Malai", category="Desserts", price=70,
            description="Two delicate cottage cheese discs poached in thickened cardamom-infused clotted saffron cream",
            emoji="🍮", image_url="https://images.unsplash.com/photo-1596797038530-2c107229654b?auto=format&fit=crop&w=600&q=80", sort_order=29,
        ),
        MenuItem(
            name="Sizzling Brownie", category="Desserts", price=140,
            description="Warm fudge walnut brownie served on a smoking hot sizzler plate with vanilla ice cream & hot chocolate fudge",
            emoji="🍫", image_url="https://images.unsplash.com/photo-1606313564200-e75d5e30476c?auto=format&fit=crop&w=600&q=80", sort_order=30,
        ),
    ]

    db.add_all(menu_items)
    db.commit()
