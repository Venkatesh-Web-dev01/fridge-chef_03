import json
from pathlib import Path
from typing import List, Dict, Any, Optional
import httpx
from ..config import DATA_DIR, settings
from ..models.schemas import Recipe, RecipeSearchRequest, RecipeInstructionStep, NutritionInfo
from ..database import FavoritesRepo
from .safety_filter import SafetyFilter
from .matching_engine import MatchingEngine
from .cache_service import CacheService

RECIPES_FILE = DATA_DIR / "recipes.json"

class RecipeService:
    _cached_recipes: Optional[List[Dict[str, Any]]] = None

    @classmethod
    def load_local_recipes(cls) -> List[Dict[str, Any]]:
        if cls._cached_recipes is None:
            if RECIPES_FILE.exists():
                with open(RECIPES_FILE, "r", encoding="utf-8") as f:
                    cls._cached_recipes = json.load(f)
            else:
                cls._cached_recipes = []
        return cls._cached_recipes

    @classmethod
    async def fetch_themealdb_recipes(cls, main_ingredient: str) -> List[Dict[str, Any]]:
        """
        Queries TheMealDB free open API for recipes matching an ingredient.
        """
        cache_key = f"themealdb_{main_ingredient.lower().strip()}"
        cached = CacheService.get(cache_key)
        if cached:
            return cached

        url = f"https://www.themealdb.com/api/json/v1/1/filter.php?i={main_ingredient.lower().strip()}"
        results = []
        try:
            async with httpx.AsyncClient(timeout=8.0) as client:
                res = await client.get(url)
                if res.status_code == 200:
                    data = res.json()
                    meals = data.get("meals") or []
                    # Fetch top 2 meals in detail
                    for m in meals[:2]:
                        detail_url = f"https://www.themealdb.com/api/json/v1/1/lookup.php?i={m['idMeal']}"
                        d_res = await client.get(detail_url)
                        if d_res.status_code == 200:
                            meal_data = d_res.json().get("meals", [{}])[0]
                            # parse ingredients
                            ingredients = []
                            for idx in range(1, 21):
                                ing = meal_data.get(f"strIngredient{idx}")
                                measure = meal_data.get(f"strMeasure{idx}")
                                if ing and ing.strip():
                                    ingredients.append(f"{measure or ''} {ing}".strip())
                            
                            steps_raw = meal_data.get("strInstructions", "").split("\r\n")
                            instructions = [
                                RecipeInstructionStep(
                                    step_number=i + 1,
                                    instruction=s.strip(),
                                    timer_minutes=5 if "simmer" in s.lower() or "boil" in s.lower() else None
                                )
                                for i, s in enumerate([s for s in steps_raw if len(s.strip()) > 15])
                            ]
                            
                            results.append({
                                "id": f"themealdb-{meal_data['idMeal']}",
                                "title": meal_data.get("strMeal", "International Dish"),
                                "description": f"Traditional {meal_data.get('strArea', 'World')} meal from TheMealDB.",
                                "image_url": meal_data.get("strMealThumb", ""),
                                "prep_time_min": 15,
                                "cook_time_min": 25,
                                "servings": 4,
                                "difficulty": "Medium",
                                "cuisine": meal_data.get("strArea", "International"),
                                "dietary_tags": [],
                                "allergens": [],
                                "ingredients": ingredients,
                                "instructions": [ins.model_dump() for ins in instructions],
                                "nutrition": {"calories": 450, "protein_g": 25, "carbs_g": 40, "fat_g": 18, "fiber_g": 4}
                            })
            CacheService.set(cache_key, results, ttl_seconds=3600)
        except Exception as e:
            print(f"TheMealDB fetch error: {e}")

        return results

    @classmethod
    async def fetch_spoonacular_recipes(cls, ingredients: List[str], api_key: str) -> List[Dict[str, Any]]:
        """
        Spoonacular findByIngredients live API adapter.
        """
        if not api_key:
            return []
        
        cache_key = f"spoonacular_{','.join(sorted(ingredients))}"
        cached = CacheService.get(cache_key)
        if cached:
            return cached

        ing_param = ",".join(ingredients[:5])
        url = f"https://api.spoonacular.com/recipes/findByIngredients?ingredients={ing_param}&number=4&ranking=1&apiKey={api_key}"
        results = []
        try:
            async with httpx.AsyncClient(timeout=8.0) as client:
                res = await client.get(url)
                if res.status_code == 200:
                    for item in res.json():
                        rec_id = str(item.get("id"))
                        # Fetch full recipe details
                        detail_url = f"https://api.spoonacular.com/recipes/{rec_id}/information?includeNutrition=true&apiKey={api_key}"
                        d_res = await client.get(detail_url)
                        if d_res.status_code == 200:
                            data = d_res.json()
                            ing_list = [i.get("original", "") for i in data.get("extendedIngredients", [])]
                            instructions = [
                                RecipeInstructionStep(
                                    step_number=s.get("number", idx + 1),
                                    instruction=s.get("step", ""),
                                    timer_minutes=s.get("length", {}).get("number") if s.get("length") else None
                                )
                                for idx, s in enumerate(data.get("analyzedInstructions", [{}])[0].get("steps", []))
                            ] if data.get("analyzedInstructions") else [RecipeInstructionStep(step_number=1, instruction="Cook as directed.")]

                            nut = data.get("nutrition", {}).get("nutrients", [])
                            get_nut = lambda n: next((x.get("amount", 0.0) for x in nut if x.get("name", "").lower() == n.lower()), 0.0)

                            results.append({
                                "id": f"spoon-{rec_id}",
                                "title": data.get("title", ""),
                                "description": "Recipe fetched via Spoonacular Food API.",
                                "image_url": data.get("image", ""),
                                "prep_time_min": data.get("readyInMinutes", 20) // 2,
                                "cook_time_min": data.get("readyInMinutes", 20) // 2,
                                "servings": data.get("servings", 2),
                                "difficulty": "Medium",
                                "cuisine": (data.get("cuisines") or ["Global"])[0],
                                "dietary_tags": [d for d in ["vegan", "vegetarian", "gluten-free", "dairy-free"] if data.get(d.replace("-", ""))],
                                "allergens": [],
                                "ingredients": ing_list,
                                "instructions": [ins.model_dump() for ins in instructions],
                                "nutrition": {
                                    "calories": int(get_nut("calories") or 350),
                                    "protein_g": float(get_nut("protein") or 15),
                                    "carbs_g": float(get_nut("carbohydrates") or 30),
                                    "fat_g": float(get_nut("fat") or 12),
                                    "fiber_g": float(get_nut("fiber") or 3)
                                }
                            })
            CacheService.set(cache_key, results, ttl_seconds=3600)
        except Exception as e:
            print(f"Spoonacular fetch error: {e}")

        return results

    @classmethod
    async def search_recipes(cls, req: RecipeSearchRequest, spoonacular_key: Optional[str] = None) -> List[Recipe]:
        all_candidate_recipes = list(cls.load_local_recipes())

        # Spoonacular integration if key supplied
        if spoonacular_key:
            spoon_recs = await cls.fetch_spoonacular_recipes(req.ingredients, spoonacular_key)
            all_candidate_recipes.extend(spoon_recs)

        # 1. Apply rule-based safety filter (Allergies + Diets)
        safe_recipes = [
            r for r in all_candidate_recipes
            if SafetyFilter.is_recipe_safe(
                recipe=r,
                allergies=req.allergies,
                vegan=req.vegan,
                vegetarian=req.vegetarian,
                keto=req.keto,
                gluten_free=req.gluten_free
            )
        ]

        # 2. Evaluate matches and rank
        ranked = MatchingEngine.rank_recipes(
            recipes=safe_recipes,
            user_ingredients=req.ingredients,
            staples=req.staples,
            use_soon_items=req.use_soon,
            max_missing=req.max_missing,
            sort_by=req.sort_by
        )

        # 3. Populate is_favorite from database
        for r in ranked:
            r.is_favorite = FavoritesRepo.is_favorite(r.id)

        return ranked
