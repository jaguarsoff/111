from config import CNY_TO_RUB, SHIPPING_PER_KG, FIXED_FEE_SHOES, FIXED_FEE_CLOTHES, BULK_PRICE_FROM_3, SMALL_ITEM_MULTIPLIER
def calc_item_price_rub(price_cny, qty, category):
    base = price_cny * qty * CNY_TO_RUB
    # fixed commission by category
    fee = 0
    if category.lower() in ("shoes","обувь"):
        fee = FIXED_FEE_SHOES
    elif category.lower() in ("clothes","одежда"):
        fee = FIXED_FEE_CLOTHES
    # bulk discount: if qty >=3 set per-item fixed price? simple implementation:
    if qty >= 3 and category.lower() in ("shoes","одежда"):
        # apply per item fixed price (задан от 3 штук 350 за штуку)
        base = (BULK_PRICE_FROM_3 * qty) * CNY_TO_RUB
    return base + fee

def calc_order(cart_items):
    total_weight = sum((it['weight_kg'] or 0) * it['qty'] for it in cart_items)
    items_cost = 0
    for it in cart_items:
        items_cost += calc_item_price_rub(it['price_cny'], it['qty'], it.get('category',''))
    shipping = SHIPPING_PER_KG * (total_weight if total_weight>0 else 0)
    total = items_cost + shipping
    return {
        "items_cost": round(items_cost,2),
        "shipping": round(shipping,2),
        "total": round(total,2),
        "total_weight": round(total_weight,3)
    }
