from typing import Dict, Any, Optional, List
import httpx
from ..config import settings
from .cache_service import CacheService

class USDAFoodDataAdapter:
    """
    Integration point for USDA FoodData Central API.
    Enables precise macro/micro-nutrient lookup for whole groceries and raw ingredients.
    """
    BASE_URL = "https://api.nal.usda.gov/fdc/v1"

    @classmethod
    async def get_food_nutrition(cls, query: str, api_key: Optional[str] = None) -> Dict[str, Any]:
        key = api_key or settings.usda_api_key or "DEMO_KEY"
        cache_key = f"usda_{query.lower().strip()}"
        cached = CacheService.get(cache_key)
        if cached:
            return cached

        try:
            async with httpx.AsyncClient(timeout=6.0) as client:
                res = await client.get(
                    f"{cls.BASE_URL}/foods/search",
                    params={"query": query, "pageSize": 1, "api_key": key}
                )
                if res.status_code == 200:
                    data = res.json()
                    foods = data.get("foods", [])
                    if foods:
                        food = foods[0]
                        nutrients = {n.get("nutrientName", "").lower(): n.get("value", 0.0) for n in food.get("foodNutrients", [])}
                        result = {
                            "description": food.get("description"),
                            "fdcId": food.get("fdcId"),
                            "calories": nutrients.get("energy", 0.0),
                            "protein_g": nutrients.get("protein", 0.0),
                            "carbs_g": nutrients.get("carbohydrate, by difference", 0.0),
                            "fat_g": nutrients.get("total lipid (fat)", 0.0)
                        }
                        CacheService.set(cache_key, result, ttl_seconds=86400)
                        return result
        except Exception as e:
            print(f"USDA adapter error: {e}")

        # Sensible fallback nutrition
        return {"description": query, "calories": 120, "protein_g": 4.0, "carbs_g": 15.0, "fat_g": 2.0}

class OpenFoodFactsAdapter:
    """
    Integration point for Open Food Facts API (Open barcode & packaged food database).
    Allows scanning a grocery barcode to immediately ingest brand name and allergens.
    """
    BASE_URL = "https://world.openfoodfacts.org/api/v2"

    @classmethod
    async def get_product_by_barcode(cls, barcode: str) -> Optional[Dict[str, Any]]:
        cache_key = f"off_{barcode}"
        cached = CacheService.get(cache_key)
        if cached:
            return cached

        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                res = await client.get(f"{cls.BASE_URL}/product/{barcode}.json")
                if res.status_code == 200:
                    data = res.json()
                    if data.get("status") == 1:
                        prod = data.get("product", {})
                        result = {
                            "product_name": prod.get("product_name", "Unknown Item"),
                            "brands": prod.get("brands", ""),
                            "categories": prod.get("categories_tags", []),
                            "allergens": prod.get("allergens_tags", []),
                            "nutriscore": prod.get("nutriscore_grade", "c")
                        }
                        CacheService.set(cache_key, result, ttl_seconds=86400)
                        return result
        except Exception as e:
            print(f"OpenFoodFacts error: {e}")

        return None

class RecipeNLGDatasetLoader:
    """
    Loader and schema transformer for RecipeNLG / Kaggle CSV/JSON datasets.
    Can ingest offline millions of recipes into local SQLite.
    """
    @classmethod
    def parse_recipenlg_row(cls, row: Dict[str, Any]) -> Dict[str, Any]:
        """Maps RecipeNLG dataset schema to FridgeChef standard Recipe model."""
        import json
        raw_ingredients = row.get("ingredients", "[]")
        if isinstance(raw_ingredients, str):
            try:
                ingredients = json.loads(raw_ingredients)
            except Exception:
                ingredients = [i.strip() for i in raw_ingredients.strip("[]'\"").split("', '")]
        else:
            ingredients = raw_ingredients

        raw_directions = row.get("directions", "[]")
        if isinstance(raw_directions, str):
            try:
                directions = json.loads(raw_directions)
            except Exception:
                directions = [d.strip() for d in raw_directions.strip("[]'\"").split("', '")]
        else:
            directions = raw_directions

        return {
            "id": f"nlg-{row.get('id', hash(row.get('title', '')))}",
            "title": row.get("title", "Untitled Recipe"),
            "description": "Recipe from open RecipeNLG dataset",
            "image_url": "https://images.unsplash.com/photo-1498837167922-ddd27525d352?auto=format&fit=crop&w=800&q=80",
            "prep_time_min": 10,
            "cook_time_min": 20,
            "servings": 4,
            "difficulty": "Medium",
            "cuisine": "American",
            "dietary_tags": [],
            "allergens": [],
            "ingredients": ingredients,
            "instructions": [{"step_number": idx + 1, "instruction": d} for idx, d in enumerate(directions)],
            "nutrition": {"calories": 350, "protein_g": 15, "carbs_g": 40, "fat_g": 12, "fiber_g": 3}
        }
