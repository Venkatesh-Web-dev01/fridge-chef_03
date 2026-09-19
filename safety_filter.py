import re
import json
from typing import List, Dict, Any
from ..config import DATA_DIR
from .normalizer import normalize_ingredient

ALLERGENS_FILE = DATA_DIR / "allergens.json"
ALLERGENS_DICT: Dict[str, List[str]] = {}

if ALLERGENS_FILE.exists():
    try:
        with open(ALLERGENS_FILE, "r", encoding="utf-8") as f:
            ALLERGENS_DICT = json.load(f)
    except Exception as e:
        print(f"Failed to load allergens dictionary: {e}")

SAFETY_DISCLAIMER = (
    "Disclaimer: Automated dietary and allergy filtering is provided as a culinary guideline and is "
    "not medical advice. Always inspect packaging and manufacturer labels for cross-contamination."
)

# False positive exceptions (e.g. peanut butter is not dairy butter)
DAIRY_EXCLUSIONS = ["peanut butter", "apple butter", "cocoa butter", "shea butter", "butternut", "coconut milk", "almond milk", "soy milk", "oat milk"]

class SafetyFilter:
    @staticmethod
    def is_recipe_safe(
        recipe: Dict[str, Any], 
        allergies: List[str], 
        vegan: bool = False, 
        vegetarian: bool = False, 
        keto: bool = False, 
        gluten_free: bool = False
    ) -> bool:
        """
        Enforces strict rule-based exclusion filters.
        Returns True if recipe passes all safety checks, False otherwise.
        """
        # 1. Allergen checks
        if allergies:
            recipe_allergens = [a.lower() for a in recipe.get("allergens", [])]
            raw_ingredients = [ing.lower() for ing in recipe.get("ingredients", [])]
            normalized_ingredients = [
                normalize_ingredient(ing) for ing in recipe.get("ingredients", [])
            ]

            for allergy in allergies:
                allergy_norm = allergy.lower().replace("-", "_").replace(" ", "_")
                
                # Check declared allergens on the recipe
                if allergy_norm in recipe_allergens:
                    return False
                
                # Check keyword triggers in ingredients
                triggers = ALLERGENS_DICT.get(allergy_norm, [allergy_norm])
                for trig in triggers:
                    for idx, ing in enumerate(normalized_ingredients):
                        raw_ing = raw_ingredients[idx]
                        
                        # Handle dairy false positives
                        if allergy_norm == "dairy":
                            if any(ex in raw_ing or ex in ing for ex in DAIRY_EXCLUSIONS):
                                continue

                        pattern = rf"\b{re.escape(trig)}\b"
                        if re.search(pattern, ing) or re.search(pattern, raw_ing):
                            return False

        # 2. Dietary Checks
        diet_tags = [t.lower() for t in recipe.get("dietary_tags", [])]
        
        if vegan and "vegan" not in diet_tags:
            return False

        if vegetarian and ("vegetarian" not in diet_tags and "vegan" not in diet_tags):
            return False

        if gluten_free and "gluten-free" not in diet_tags:
            return False

        if keto:
            # Check keto tag or calculate net carbs
            if "keto" not in diet_tags and "low-carb" not in diet_tags:
                nutrition = recipe.get("nutrition", {})
                carbs = nutrition.get("carbs_g", 50.0)
                fiber = nutrition.get("fiber_g", 0.0)
                net_carbs = max(0.0, carbs - fiber)
                if net_carbs > 15.0:
                    return False

        return True
