import os
import time
from typing import List, Optional, Dict, Any
from fastapi import FastAPI, UploadFile, File, Form, Query, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from .config import settings
from .database import (
    init_db, PantryRepo, FavoritesRepo, ShoppingListRepo
)
from .models.schemas import (
    VisionDetectResponse, RecipeSearchRequest, Recipe,
    SubstitutionRequest, SubstitutionResponse, ShoppingListAddRequest,
    ShoppingListItem, SystemStatusResponse, IngredientItem
)
from .services.vision_service import VisionService, MOCK_PRESETS
from .services.recipe_service import RecipeService
from .services.substitution_service import SubstitutionService
from .services.cache_service import CacheService
from .services.external_adapters import USDAFoodDataAdapter, OpenFoodFactsAdapter

app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description="Multimodal AI Recipe Generator from Fridge Photos with Expiry-Aware Ranking and Substitutions"
)

# Enable CORS for frontend Vite dev server and production origins
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
def on_startup():
    init_db()

@app.get("/")
def root():
    return {
        "message": "Welcome to FridgeChef AI API",
        "docs_url": "/docs",
        "version": settings.app_version,
        "status": "online"
    }

# ==========================================
# 1. Vision AI Endpoints
# ==========================================
@app.post("/api/vision/detect", response_model=VisionDetectResponse)
async def detect_ingredients_endpoint(
    image: Optional[UploadFile] = File(None),
    preset_id: Optional[str] = Form(None),
    gemini_key: Optional[str] = Form(None),
    openai_key: Optional[str] = Form(None)
):
    """
    Accepts an uploaded fridge/pantry photo or preset identifier,
    runs multimodal vision detection (Gemini/OpenAI or smart mock fallback),
    and returns a structured list of detected food ingredients.
    """
    if preset_id and preset_id in MOCK_PRESETS:
        return await VisionService.detect_ingredients(
            image_bytes=b"", preset_id=preset_id
        )

    if not image:
        # If no image or preset provided, default to family_fridge demo preset
        return await VisionService.detect_ingredients(
            image_bytes=b"", preset_id="family_fridge"
        )

    image_bytes = await image.read()
    if not image_bytes:
        raise HTTPException(status_code=400, detail="Empty image file uploaded.")

    return await VisionService.detect_ingredients(
        image_bytes=image_bytes,
        preset_id=None,
        custom_gemini_key=gemini_key,
        custom_openai_key=openai_key
    )

@app.get("/api/sample-images")
def get_sample_images():
    """Returns preset fridge scenes for 1-click hackathon demonstration."""
    return [
        {
            "id": "family_fridge",
            "title": "Family Refrigerator",
            "description": "Eggs, whole milk, baby spinach, cheddar, chicken breast, butter, lemons.",
            "image_url": "https://images.unsplash.com/photo-1584269600464-37b1b58a9fe7?auto=format&fit=crop&w=800&q=80",
            "items_count": len(MOCK_PRESETS["family_fridge"])
        },
        {
            "id": "college_pantry",
            "title": "College Dorm Pantry",
            "description": "Penne pasta, black beans, firm tofu, broccoli, red bell pepper, rice, soy sauce.",
            "image_url": "https://images.unsplash.com/photo-1590779033100-9f60a05a013d?auto=format&fit=crop&w=800&q=80",
            "items_count": len(MOCK_PRESETS["college_pantry"])
        },
        {
            "id": "produce_crisper",
            "title": "Fresh Produce Crisper",
            "description": "Ripe avocados, cucumber, zucchini, green beans, mushrooms, cilantro, limes.",
            "image_url": "https://images.unsplash.com/photo-1610348725531-843dff563e2c?auto=format&fit=crop&w=800&q=80",
            "items_count": len(MOCK_PRESETS["produce_crisper"])
        }
    ]

# ==========================================
# 2. Recipe Search & Ranking Endpoints
# ==========================================
@app.post("/api/recipes/search", response_model=List[Recipe])
async def search_recipes_endpoint(
    req: RecipeSearchRequest,
    spoonacular_key: Optional[str] = Query(None)
):
    """
    Ranks recipes against confirmed ingredients and pantry staples,
    applies rule-based dietary/allergy safety filters,
    and applies a priority bonus to recipes using expiring ("use soon") items.
    """
    key = spoonacular_key or settings.spoonacular_api_key or None
    return await RecipeService.search_recipes(req, spoonacular_key=key)

# ==========================================
# 3. Culinary Substitutions Endpoints
# ==========================================
@app.post("/api/substitutions", response_model=SubstitutionResponse)
def get_substitutions_endpoint(req: SubstitutionRequest):
    """
    Returns verified cooking substitutions for missing ingredients,
    with pantry-awareness highlighting what the user already owns.
    """
    return SubstitutionService.get_substitutions(req.ingredient, req.user_pantry)

# ==========================================
# 4. Pantry Memory & Staples Endpoints
# ==========================================
@app.get("/api/pantry")
def get_pantry():
    return {
        "items": PantryRepo.get_items(),
        "staples": PantryRepo.get_staples()
    }

@app.post("/api/pantry/item")
def upsert_pantry_item(item: IngredientItem):
    PantryRepo.upsert_item(
        name=item.name,
        category=item.category,
        quantity=1.0,
        unit=item.quantity or "",
        use_soon=item.use_soon
    )
    return {"status": "ok", "message": f"Updated {item.name}"}

@app.delete("/api/pantry/item/{name}")
def delete_pantry_item(name: str):
    PantryRepo.delete_item(name)
    return {"status": "ok", "message": f"Deleted {name}"}

@app.post("/api/pantry/staple/toggle")
def toggle_staple(name: str = Form(...), is_active: bool = Form(...)):
    PantryRepo.toggle_staple(name, is_active)
    return {"status": "ok", "name": name, "is_active": is_active}

# ==========================================
# 5. Favorites Endpoints
# ==========================================
@app.get("/api/favorites")
def get_favorites():
    return FavoritesRepo.get_all()

@app.post("/api/favorites/toggle")
def toggle_favorite(recipe_id: str = Form(...), title: str = Form(...), image_url: str = Form(""), data_json: str = Form("{}")):
    import json
    try:
        rec_data = json.loads(data_json)
    except Exception:
        rec_data = {"id": recipe_id, "title": title, "image_url": image_url}
        
    is_fav = FavoritesRepo.toggle(recipe_id, title, image_url, rec_data)
    return {"status": "ok", "recipe_id": recipe_id, "is_favorite": is_fav}

# ==========================================
# 6. Shopping List Endpoints
# ==========================================
@app.get("/api/shopping-list")
def get_shopping_list():
    return ShoppingListRepo.get_all()

@app.post("/api/shopping-list/add")
def add_to_shopping_list(req: ShoppingListAddRequest):
    ShoppingListRepo.add_items(req.items)
    return {"status": "ok", "added_count": len(req.items)}

@app.put("/api/shopping-list/{item_id}/toggle")
def toggle_shopping_list_item(item_id: int, is_checked: bool = Query(...)):
    ShoppingListRepo.toggle_check(item_id, is_checked)
    return {"status": "ok"}

@app.delete("/api/shopping-list/{item_id}")
def delete_shopping_list_item(item_id: int):
    ShoppingListRepo.delete_item(item_id)
    return {"status": "ok"}

@app.delete("/api/shopping-list")
def clear_shopping_list():
    ShoppingListRepo.clear()
    return {"status": "ok"}

# ==========================================
# 7. External Adapters (USDA / Barcode)
# ==========================================
@app.get("/api/external/nutrition")
async def get_nutrition(query: str = Query(...)):
    return await USDAFoodDataAdapter.get_food_nutrition(query)

@app.get("/api/external/barcode/{barcode}")
async def get_barcode_product(barcode: str):
    prod = await OpenFoodFactsAdapter.get_product_by_barcode(barcode)
    if not prod:
        raise HTTPException(status_code=404, detail="Barcode product not found.")
    return prod

# ==========================================
# 8. System Status & Health
# ==========================================
@app.get("/api/system/status", response_model=SystemStatusResponse)
def get_system_status():
    local_recipes = RecipeService.load_local_recipes()
    staples = PantryRepo.get_staples()
    active_staples = [s for s in staples if s.get("is_active")]
    
    vision_mode = "Gemini Vision (Live)" if settings.gemini_api_key else (
        "OpenAI GPT-4o (Live)" if settings.openai_api_key else "Smart Mock Vision (Zero-Config Hackathon Mode)"
    )

    return SystemStatusResponse(
        status="healthy",
        vision_provider=vision_mode,
        recipes_count=len(local_recipes),
        staples_count=len(active_staples),
        cache_entries=CacheService.count(),
        sqlite_ok=True,
        features_active=[
            "Multimodal Vision AI",
            "Plural & Unit Normalization",
            "RapidFuzz Synonym Matching",
            "Expiry 'Use Soon' Priority Boost",
            "Rule-Based Dietary & Allergy Exclusion",
            "Contextual Substitutions Engine",
            "Step-by-Step Cooking Mode with Timers",
            "Consolidated Shopping List",
            "SQLite Persistence",
            "TheMealDB / Spoonacular Adapters",
            "USDA FoodData & Open Food Facts Extension"
        ]
    )
