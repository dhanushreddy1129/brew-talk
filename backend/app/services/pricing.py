"""
Pricing rules live ONLY here. Change tax, service charge, discounts etc.
The frontend never computes totals — it calls /api/quote.
"""


def compute_quote(
    items_with_prices: list[dict],
    tax_percent: float,
    service_charge_percent: float,
) -> dict:
    """
    Compute a full price breakdown.

    Args:
        items_with_prices: List of dicts with keys:
            name (str), price (float), quantity (int), menu_item_id (int)
        tax_percent: Tax percentage (e.g. 5 for 5%).
        service_charge_percent: Service charge percentage (e.g. 3 for 3%).

    Returns:
        Dict with: items (with line_total), subtotal, tax_percent, tax_amount,
        service_charge_percent, service_charge_amount, total.
    """
    enriched_items = []
    subtotal = 0.0

    for item in items_with_prices:
        line_total = round(item["price"] * item["quantity"], 2)
        subtotal += line_total
        enriched_items.append({
            "menu_item_id": item["menu_item_id"],
            "name": item["name"],
            "price": item["price"],
            "quantity": item["quantity"],
            "line_total": line_total,
        })

    subtotal = round(subtotal, 2)
    tax_amount = round(subtotal * tax_percent / 100, 2)
    service_charge_amount = round(subtotal * service_charge_percent / 100, 2)
    total = round(subtotal + tax_amount + service_charge_amount, 2)

    return {
        "items": enriched_items,
        "subtotal": subtotal,
        "tax_percent": tax_percent,
        "tax_amount": tax_amount,
        "service_charge_percent": service_charge_percent,
        "service_charge_amount": service_charge_amount,
        "total": total,
    }
