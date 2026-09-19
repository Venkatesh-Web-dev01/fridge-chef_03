from typing import List, Dict, Any, Tuple
from .normalizer import normalize_ingredient, is_ingredient_match
from ..models.schemas import Recipe

class MatchingEngine:
    @staticmethod
    def evaluate_recipe_match(
        recipe_dict: Dict[str, Any],
        user_ingredients: List[str],
        staples: List[str],
        use_soon_items: List[str]
    ) -> Tuple[float, List[str], List[str], int]:
        """
        Calculates match score, list of matching items, list of missing items,
        and count of expiring items utilized.
        """
        # Combine user pantry and staples
        user_pool = list(set(user_ingredients + staples))
        recipe_ingredients = recipe_dict.get("ingredients", [])
        
        if not recipe_ingredients:
            return 0.0, [], [], 0

        matching = []
        missing = []
        matched_user_items = set()

        for rec_ing in recipe_ingredients:
            found_match = False
            for u_ing in user_pool:
                if is_ingredient_match(u_ing, rec_ing):
                    matching.append(rec_ing)
                    matched_user_items.add(u_ing.lower())
                    found_match = True
                    break
            if not found_match:
                missing.append(rec_ing)

        total_req = len(recipe_ingredients)
        raw_score = (len(matching) / total_req) * 100.0 if total_req > 0 else 0.0

        # Expiry ("use soon") boost
        expiring_used = 0
        norm_use_soon = [normalize_ingredient(x) for x in use_soon_items]
        
        for matched_u in matched_user_items:
            norm_u = normalize_ingredient(matched_u)
            for exp_item in norm_use_soon:
                if norm_u == exp_item or exp_item in norm_u:
                    expiring_used += 1
                    break

        # +15% boost per expiring item used (max +30%)
        expiry_boost = min(30.0, expiring_used * 15.0)
        final_score = min(100.0, raw_score + expiry_boost)

        return round(final_score, 1), matching, missing, expiring_used

    @staticmethod
    def rank_recipes(
        recipes: List[Dict[str, Any]],
        user_ingredients: List[str],
        staples: List[str],
        use_soon_items: List[str],
        max_missing: int = 6,
        sort_by: str = "best_match"
    ) -> List[Recipe]:
        scored_recipes = []

        for rec in recipes:
            score, matching, missing, expiring_count = MatchingEngine.evaluate_recipe_match(
                rec, user_ingredients, staples, use_soon_items
            )

            # Filter out recipes with too many missing items
            if len(missing) > max_missing:
                continue

            rec_obj = Recipe(
                id=rec["id"],
                title=rec["title"],
                description=rec["description"],
                image_url=rec["image_url"],
                prep_time_min=rec["prep_time_min"],
                cook_time_min=rec["cook_time_min"],
                servings=rec["servings"],
                difficulty=rec["difficulty"],
                cuisine=rec["cuisine"],
                dietary_tags=rec.get("dietary_tags", []),
                allergens=rec.get("allergens", []),
                ingredients=rec["ingredients"],
                instructions=rec["instructions"],
                nutrition=rec["nutrition"],
                match_score=score,
                matching_ingredients=matching,
                missing_ingredients=missing,
                uses_expiring_count=expiring_count
            )
            scored_recipes.append(rec_obj)

        # Sorting strategy
        if sort_by == "expiry_first":
            scored_recipes.sort(key=lambda r: (r.uses_expiring_count, r.match_score), reverse=True)
        elif sort_by == "fastest":
            scored_recipes.sort(key=lambda r: (r.prep_time_min + r.cook_time_min, -r.match_score))
        else: # "best_match"
            scored_recipes.sort(key=lambda r: (r.match_score, r.uses_expiring_count, -len(r.missing_ingredients)), reverse=True)

        return scored_recipes
