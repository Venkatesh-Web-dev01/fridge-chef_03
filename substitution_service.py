from typing import List, Dict, Any, Optional
from ..models.schemas import SubstitutionItem, SubstitutionResponse
from .normalizer import normalize_ingredient
from .cache_service import CacheService

# Curated culinary substitution database
COMMON_SUBSTITUTIONS = {
    "sour cream": [
        {"substitute": "plain greek yogurt", "ratio": "1:1", "notes": "Identical tangy acidity and creamy texture with extra protein.", "dietary": ["vegetarian", "gluten-free"]},
        {"substitute": "heavy cream + lemon juice", "ratio": "1 cup cream + 1 tbsp lemon juice", "notes": "Let sit for 5 minutes to curdle slightly.", "dietary": ["gluten-free"]}
    ],
    "buttermilk": [
        {"substitute": "milk + lemon juice or white vinegar", "ratio": "1 cup milk + 1 tbsp acid", "notes": "Stir and let sit 5-10 minutes until curdled.", "dietary": ["vegetarian", "gluten-free"]},
        {"substitute": "plain yogurt thinned with water", "ratio": "3/4 cup yogurt + 1/4 cup water", "notes": "Whisk until liquid and smooth.", "dietary": ["vegetarian", "gluten-free"]}
    ],
    "heavy cream": [
        {"substitute": "milk + melted butter", "ratio": "3/4 cup milk + 1/4 cup melted butter", "notes": "Whisk thoroughly; best for cooking and sauces, not whipping.", "dietary": ["vegetarian", "gluten-free"]},
        {"substitute": "coconut cream", "ratio": "1:1", "notes": "Excellent dairy-free and vegan alternative with a subtle coconut note.", "dietary": ["vegan", "dairy-free"]}
    ],
    "butter": [
        {"substitute": "olive oil or vegetable oil", "ratio": "3/4 cup oil for 1 cup butter", "notes": "Great for sautéing and rustic baking.", "dietary": ["vegan", "dairy-free"]},
        {"substitute": "ghee or coconut oil", "ratio": "1:1", "notes": "Solid at room temp with high smoke point.", "dietary": ["keto"]}
    ],
    "large egg": [
        {"substitute": "ground flaxseed + water (flax egg)", "ratio": "1 tbsp flaxseed meal + 3 tbsp water", "notes": "Whisk and rest 5 minutes to form gel. Superb for baking.", "dietary": ["vegan", "dairy-free", "gluten-free"]},
        {"substitute": "unsweetened applesauce", "ratio": "1/4 cup applesauce per egg", "notes": "Adds moisture to muffins, pancakes, and quick breads.", "dietary": ["vegan"]}
    ],
    "egg": [
        {"substitute": "ground flaxseed + water (flax egg)", "ratio": "1 tbsp flaxseed + 3 tbsp water", "notes": "Whisk and rest 5 minutes until gelled.", "dietary": ["vegan", "dairy-free"]},
        {"substitute": "mashed ripe banana", "ratio": "1/2 medium banana per egg", "notes": "Best in sweet baking like pancakes or banana bread.", "dietary": ["vegan"]}
    ],
    "breadcrumbs": [
        {"substitute": "crushed oats or cracker crumbs", "ratio": "1:1", "notes": "Pulse in blender for identical binding power.", "dietary": ["vegetarian"]},
        {"substitute": "crushed pork rinds or almond flour", "ratio": "1:1", "notes": "Perfect low-carb and keto crunch substitute for cutlets.", "dietary": ["keto", "gluten-free"]}
    ],
    "soy sauce": [
        {"substitute": "tamari", "ratio": "1:1", "notes": "Naturally gluten-free Japanese brewed soy sauce with richer umami.", "dietary": ["gluten-free"]},
        {"substitute": "coconut aminos", "ratio": "1:1", "notes": "Soy-free and lower sodium alternative with gentle sweetness.", "dietary": ["soy-free", "gluten-free"]}
    ],
    "white wine": [
        {"substitute": "chicken or vegetable broth + splash of lemon juice", "ratio": "1:1 ratio with 1 tsp lemon juice", "notes": "Replaces acidity and depth without alcohol.", "dietary": ["alcohol-free"]}
    ],
    "lemon juice": [
        {"substitute": "apple cider vinegar or lime juice", "ratio": "1:1", "notes": "Matches bright acidity in dressings, marinades, and sauces.", "dietary": ["vegan", "gluten-free"]}
    ],
    "parmesan cheese": [
        {"substitute": "nutritional yeast flakes", "ratio": "1:1", "notes": "Savory, nutty cheesy flavor that is 100% vegan and dairy-free.", "dietary": ["vegan", "dairy-free"]},
        {"substitute": "pecorino romano", "ratio": "1:1", "notes": "Slightly sharper sheep milk cheese.", "dietary": ["gluten-free"]}
    ],
    "arborio rice": [
        {"substitute": "sushi rice or pearl barley", "ratio": "1:1", "notes": "High starch content delivers similar risotto creaminess.", "dietary": ["vegetarian"]}
    ],
    "white beans": [
        {"substitute": "chickpeas (garbanzo) or pinto beans", "ratio": "1:1", "notes": "Maintains earthy texture and fiber content in soups and skillets.", "dietary": ["vegan", "gluten-free"]}
    ],
    "dijon mustard": [
        {"substitute": "yellow mustard + pinch of white pepper", "ratio": "1:1", "notes": "Gives similar emulsion and vinegary bite in dressings.", "dietary": ["vegan"]}
    ],
    "tahini": [
        {"substitute": "sunflower seed butter or almond butter", "ratio": "1:1 thinned with warm water", "notes": "Creamy nutty texture without sesame allergen.", "dietary": ["sesame-free"]}
    ]
}

class SubstitutionService:
    @staticmethod
    def get_substitutions(ingredient_raw: str, user_pantry: List[str] = None) -> SubstitutionResponse:
        cache_key = f"sub_{normalize_ingredient(ingredient_raw)}"
        cached = CacheService.get(cache_key)
        if cached:
            return SubstitutionResponse(**cached)

        norm_name = normalize_ingredient(ingredient_raw)
        user_pantry_norm = [normalize_ingredient(p) for p in (user_pantry or [])]

        # Check in curated rule database
        items = []
        for key, subs in COMMON_SUBSTITUTIONS.items():
            if key in norm_name or norm_name in key:
                for sub in subs:
                    sub_norm = normalize_ingredient(sub["substitute"])
                    # Check if user has this in pantry
                    has_it = any(p in sub_norm or sub_norm in p for p in user_pantry_norm)
                    notes = sub["notes"]
                    if has_it:
                        notes = f"⭐ You have this in your pantry! {notes}"

                    items.append(SubstitutionItem(
                        original_ingredient=ingredient_raw,
                        substitute=sub["substitute"],
                        ratio=sub["ratio"],
                        notes=notes,
                        dietary_compatibility=sub.get("dietary", [])
                    ))
                break

        # If no rule match, provide intelligent culinary heuristic
        if not items:
            items.append(SubstitutionItem(
                original_ingredient=ingredient_raw,
                substitute=f"Any mild neutral oil or vegetable stock",
                ratio="As needed",
                notes="Adapt according to moisture or seasoning requirements.",
                dietary_compatibility=["vegan", "gluten-free"]
            ))

        response = SubstitutionResponse(
            ingredient=ingredient_raw,
            substitutions=items,
            source="rule_base"
        )
        
        # Cache for 2 hours
        CacheService.set(cache_key, response.model_dump(), ttl_seconds=7200)
        return response
