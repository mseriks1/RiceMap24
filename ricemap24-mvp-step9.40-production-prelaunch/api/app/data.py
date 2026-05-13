from __future__ import annotations

from typing import Dict, Any, List

# Cuisine choices shown both to visitors and to kitchen owners.
# Public filter adds "All Asian" as a reset/default option in the frontend;
# kitchen owners choose one or two of the concrete cuisine categories below.
CUISINES = [
    {"key": "thai", "label": {"no": "Thai", "en": "Thai"}},
    {"key": "filipino", "label": {"no": "Filipinsk", "en": "Filipino"}},
    {"key": "vietnamese", "label": {"no": "Vietnamesisk", "en": "Vietnamese"}},
    {"key": "chinese", "label": {"no": "Kinesisk", "en": "Chinese"}},
    {"key": "korean", "label": {"no": "Koreansk", "en": "Korean"}},
    {"key": "japanese", "label": {"no": "Japansk", "en": "Japanese"}},
    {"key": "indonesian", "label": {"no": "Indonesisk", "en": "Indonesian"}},
    {"key": "indian", "label": {"no": "Indisk", "en": "Indian"}},
    {"key": "pan_asian", "label": {"no": "Mixed Asian", "en": "Mixed Asian"}},
]

# Mock listings (MVP Step 1)
LISTINGS: List[Dict[str, Any]] = [
    {
        "id": "l1",
        "slug": "linh-viet-kitchen",
        "name": "Linh’s Viet Kitchen",
        "area": "Sødermalm",
        "city": "Stockholm",
        "country": "SE",
        "postcode": "116 36",
        "lat": 59.313,
        "lng": 18.066,
        "cuisines": ["vietnamese"],
        "badges": ["pickup"],
        "from_price": 110,
        "currency": "SEK",
        "hero_image": "assets/hero_viet_tb.jpg",
        "intro": {
            "no": "Hjemmelaget vietnamesisk mat — laget på bestilling for små samlinger.",
            "en": "Homemade Vietnamese food — made by request for small gatherings.",
        },
        "contact": {
            "whatsapp": "+46701234567",
            "phone": "+46701234567",
            "instagram": "linhvietkitchen",
            "email": "linh@example.com",
        },
        "pickup_note": {
            "no": "Sødermalm (adresse deles etter avtale)",
            "en": "Södermalm (address shared after agreement)",
        },
        "delivery_note": {
            "no": "Levering etter avtale. Leveringspris avhenger av område.",
            "en": "Delivery by arrangement. Fee depends on area.",
        },
        "payment_note": {
            "no": "Swish eller kontant ved henting. Etter avtale ved levering.",
            "en": "Swish or cash on pickup. By agreement for delivery.",
        },
        "availability": {
            "no": {"deadline": "Fredag 18:00", "window": "Lør 12–16"},
            "en": {"deadline": "Friday 18:00", "window": "Sat 12–16"},
        },
        "menu": [
            {
                "name": {"no": "Pho bò (batch)", "en": "Pho bò (batch)"},
                "price": 145,
                "serves": "single",
                "tags": ["signature"],
                "desc": {"no": "Rik kraft, urter og oksekjøtt.", "en": "Rich broth, herbs, and beef."},
                                "ingredients": {"no": ["Oksekraft", "Risnudler", "Oksekjøtt", "Løk", "Urter"], "en": ["Beef broth", "Rice noodles", "Beef", "Onion", "Herbs"]},
"image": "assets/dish_tb_1.jpg",
            },
            {
                "name": {"no": "Bún thịt nướng", "en": "Bún thịt nướng"},
                "price": 135,
                "serves": "single",
                "tags": ["signature"],
                "desc": {"no": "Grillet svinekjøtt, nudler og urter.", "en": "Grilled pork, noodles and herbs."},
                                "ingredients": {"no": ["Risnudler", "Grillet kjøtt", "Salat", "Urter", "Nøtter"], "en": ["Rice noodles", "Grilled meat", "Greens", "Herbs", "Peanuts"]},
"image": "assets/dish_tb_2.jpg",
            },
            {
                "name": {"no": "Bánh mì (kylling)", "en": "Bánh mì (chicken)"},
                "price": 110,
                "serves": "single",
                "tags": [],
                "desc": {"no": "Sprø baguette med fyll.", "en": "Crispy baguette with fillings."},
                                "ingredients": {"no": ["Baguette", "Kylling", "Syltede grønnsaker", "Koriander", "Chili"], "en": ["Baguette", "Chicken", "Pickled veggies", "Cilantro", "Chili"]},
"image": "assets/dish_tb_3.jpg",
            },
            {
                "name": {"no": "Family Bowl Set", "en": "Family Bowl Set"},
                "price": 295,
                "serves": "family",
                "tags": ["family"],
                "desc": {"no": "2 boller + 6 vårruller.", "en": "2 bowls + 6 spring rolls."},
                                "ingredients": {"no": ["2 boller", "Vårruller", "Urter", "Saus"], "en": ["2 bowls", "Spring rolls", "Herbs", "Sauce"]},
"image": "assets/dish_family.jpg",
            },
            {
                "name": {"no": "Big Friends Box", "en": "Big Friends Box"},
                "price": 899,
                "serves": "group",
                "tags": ["group", "best_value"],
                "desc": {"no": "4 boller + 12 vårruller + urter.", "en": "4 bowls + 12 spring rolls + herbs."},
                                "ingredients": {"no": ["Boller", "Vårruller", "Urter", "Saus"], "en": ["Bowls", "Spring rolls", "Herbs", "Sauce"]},
"image": "assets/dish_group.jpg",
            },
        ],
    },
    {
        "id": "l2",
        "slug": "noks-thai-corner",
        "name": "Nok’s Thai Corner",
        "plan": "business",
        "area": "Nørrebro",
        "city": "København",
        "country": "DK",
        "lat": 55.69,
        "lng": 12.55,
        "cuisines": ["thai"],
        "badges": ["preorder", "pickup"],
        "from_price": 110,
        "currency": "DKK",
        "hero_image": "assets/hero_thai_tb.jpg",
        "intro": {
            "no": "Ekte thaismaker — laget ferskt for henting.",
            "en": "Authentic Thai flavours — cooked fresh for pickup.",
        },
        "contact": {
            "whatsapp": "+4511122233",
            "phone": "+4511122233",
            "instagram": "noksthaicorner",
            "email": "nok@example.com",
        },
        "pickup_note": {
            "no": "Nørrebro (adresse deles etter avtale)",
            "en": "Nørrebro (address shared after agreement)",
        },
        "delivery_note": {
            "no": "Levering kan avtales. Pris avhenger av område.",
            "en": "Delivery may be possible. Fee depends on area.",
        },
        "payment_note": {
            "no": "MobilePay eller kontant. Betaling avtales direkte.",
            "en": "MobilePay or cash. Payment by agreement.",
        },
        "availability": {
            "no": {"deadline": "Fredag 17:00", "window": "Lør 13–17"},
            "en": {"deadline": "Friday 17:00", "window": "Sat 13–17"},
        },
        "menu": [
            {
                "name": {"no": "Pad Kra Pao (kylling)", "en": "Pad Kra Pao (chicken)"},
                "price": 125,
                "serves": "single",
                "tags": ["signature"],
                "desc": {"no": "Basilikum, chili og ris.", "en": "Basil, chili and rice."},
                                "ingredients": {"no": ["Kylling", "Basilikum", "Chili", "Hvitløk", "Ris"], "en": ["Chicken", "Basil", "Chili", "Garlic", "Rice"]},
"image": "assets/dish_tb_4.jpg",
            },
            {
                "name": {"no": "Green Curry", "en": "Green Curry"},
                "price": 135,
                "serves": "single",
                "tags": ["signature"],
                "desc": {"no": "Kremet curry med kokos.", "en": "Creamy coconut curry."},
                                "ingredients": {"no": ["Kokosmelk", "Curry paste", "Kylling", "Grønnsaker", "Ris"], "en": ["Coconut milk", "Curry paste", "Chicken", "Vegetables", "Rice"]},
"image": "assets/dish_tb_5.jpg",
            },
            {
                "name": {"no": "Thai Family Set", "en": "Thai Family Set"},
                "price": 329,
                "serves": "family",
                "tags": ["family"],
                "desc": {"no": "Curry + wok + ris.", "en": "Curry + stir-fry + rice."},
                                "ingredients": {"no": ["Curry", "Wok", "Ris"], "en": ["Curry", "Stir-fry", "Rice"]},
"image": "assets/dish_family2.jpg",
            },
            {
                "name": {"no": "Premium Friends Feast", "en": "Premium Friends Feast"},
                "price": 949,
                "serves": "group",
                "tags": ["group", "premium"],
                "desc": {"no": "Curry + wok + pad thai + ris.", "en": "Curry + stir-fry + pad thai + rice."},
                                "ingredients": {"no": ["Curry", "Wok", "Pad thai", "Ris"], "en": ["Curry", "Stir-fry", "Pad thai", "Rice"]},
"image": "assets/dish_group2.jpg",
            },
        ],
    },
    {
        "id": "l3",
        "slug": "marias-filipino-kusina",
        "name": "Maria’s Filipino Kusina",
        "plan": "pro",
        "area": "Grünerløkka",
        "city": "Oslo",
        "country": "NO",
        "postcode": "0587",
        "lat": 59.933,
        "lng": 10.78,
        "cuisines": ["filipino"],
        "badges": ["pickup", "delivery"],
        "from_price": 95,
        "currency": "NOK",
        "hero_image": "assets/hero_filipino_tb.jpg",
        "intro": {
            "no": "Filipinsk hjemmelaget — enkelt å bestille til familie og venner.",
            "en": "Filipino home cooking — easy to order for family and friends.",
        },
        "contact": {
            "whatsapp": "+4798765432",
            "phone": "+4798765432",
            "instagram": "mariaskusina",
            "email": "maria@example.com",
        },
        "pickup_note": {
            "no": "Grünerløkka (adresse deles etter avtale)",
            "en": "Grünerløkka (address shared after agreement)",
        },
        "delivery_note": {
            "no": "Levering etter avtale (møtepunkt i nærområdet mulig).",
            "en": "Delivery by arrangement (meet-up point nearby possible).",
        },
        "payment_note": {
            "no": "Vipps eller kontant. Betaling avtales direkte.",
            "en": "Vipps or cash. Payment by agreement.",
        },
        "availability": {
            "no": {"deadline": "Fredag 18:00", "window": "Lør 12–16"},
            "en": {"deadline": "Friday 18:00", "window": "Sat 12–16"},
        },
        "menu": [
            {
                "name": {"no": "Chicken Adobo", "en": "Chicken Adobo"},
                "price": 130,
                "serves": "single",
                "dish_key": "adobo",
                "tags": ["signature"],
                "desc": {"no": "Soyasaus, eddik, hvitløk — klassiker.", "en": "Soy, vinegar, garlic — classic."},
                                "ingredients": {"no": ["Kylling", "Soyasaus", "Eddik", "Hvitløk", "Løvblad"], "en": ["Chicken", "Soy sauce", "Vinegar", "Garlic", "Bay leaf"]},
"image": "assets/dish_adobo.jpg",
            },
            {
    "name": {"no": "Chicken Adobo", "en": "Chicken Adobo"},
    "price": 290,
    "serves": "family",
    "dish_key": "adobo",
    "tags": ["popular"],
    "desc": {"no": "Soyasaus, eddik, hvitløk — klassiker.", "en": "Soy, vinegar, garlic — classic."},
    "ingredients": {"no": ["Kylling", "Soyasaus", "Eddik", "Hvitløk", "Løvblad"], "en": ["Chicken", "Soy sauce", "Vinegar", "Garlic", "Bay leaf"]},
    "image": "assets/dish_adobo.jpg",
},
            {
    "name": {"no": "Chicken Adobo", "en": "Chicken Adobo"},
    "price": 590,
    "serves": "group",
    "dish_key": "adobo",
    "tags": ["popular"],
    "desc": {"no": "Soyasaus, eddik, hvitløk — klassiker.", "en": "Soy, vinegar, garlic — classic."},
    "ingredients": {"no": ["Kylling", "Soyasaus", "Eddik", "Hvitløk", "Løvblad"], "en": ["Chicken", "Soy sauce", "Vinegar", "Garlic", "Bay leaf"]},
    "image": "assets/dish_adobo.jpg",
},
            {
                "name": {"no": "Lumpia (10 stk)", "en": "Lumpia (10 pcs)"},
                "price": 120,
                "serves": "single",
                "tags": ["popular"],
                "desc": {"no": "Sprø vårruller.", "en": "Crispy spring rolls."},
                                "ingredients": {"no": ["Vårrulldeig", "Grønnsaker", "Kjøtt (valgfritt)", "Krydder"], "en": ["Wrapper", "Vegetables", "Meat (optional)", "Seasoning"]},
"image": "assets/dish_lumpia.jpg",
            },
            {
                "name": {"no": "Barkada Set", "en": "Barkada Set"},
                "dish_key": "barkada",
                "price": 320,
                "serves": "family",
                "tags": ["family"],
                "desc": {"no": "Adobo + ris + lumpia.", "en": "Adobo + rice + lumpia."},
                                "ingredients": {"no": ["Adobo", "Ris", "Lumpia"], "en": ["Adobo", "Rice", "Lumpia"]},
"image": "assets/dish_family3.jpg",
            },
            {
                "name": {"no": "Barkada Group Set", "en": "Barkada Group Set"},
                "price": 899,
                "serves": "group",
                "tags": ["group", "best_value"],
                "desc": {"no": "For 5–6. Adobo + lumpia + ris.", "en": "Serves 5–6. Adobo + lumpia + rice."},
                                "ingredients": {"no": ["Adobo", "Ris", "Lumpia", "Ekstra sider"], "en": ["Adobo", "Rice", "Lumpia", "Extra sides"]},
"image": "assets/dish_barkada.jpg",
            },
        ],
    },
]


def get_listing(slug: str) -> Dict[str, Any] | None:
    for l in LISTINGS:
        if l["slug"] == slug:
            return l
    return None

