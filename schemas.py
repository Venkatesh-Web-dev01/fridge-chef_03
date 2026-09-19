from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field

class IngredientItem(BaseModel):
    name: str
    category: str = "Pantry"
    confidence: float = 0.95
    is_staple: bool = False
    use_soon: bool = False
    quantity: Optional[str] = None

class VisionDetectResponse(BaseModel):
    ingredients: List[IngredientItem]
    detected_count: int
    raw_summary: str
    provider_used: str
    execution_time_ms: float

class RecipeInstructionStep(BaseModel):
    step_number: int
    instruction: str
    timer_minutes: Optional[int] = None
    tip: Optional[str] = None

class NutritionInfo(BaseModel):
    calories: int
    protein_g: float
    carbs_g: float
    fat_g: float
    fiber_g: float

class Recipe(BaseModel):
    id: str
    title: str
    description: str
    image_url: str
    prep_time_min: int
    cook_time_min: int
    servings: int
    difficulty: str  # Easy, Medium, Hard
    cuisine: str
    dietary_tags: List[str] = [] # vegan, vegetarian, keto, gluten-free, etc.
    allergens: List[str] = []    # dairy, nuts, eggs, gluten, etc.
    ingredients: List[str]       # raw recipe ingredients e.g. ["2 eggs", "1 cup milk"]
    instructions: List[RecipeInstructionStep]
    nutrition: NutritionInfo
    
    # Dynamic computed fields during search
    match_score: float = 0.0
    matching_ingredients: List[str] = []
    missing_ingredients: List[str] = []
    uses_expiring_count: int = 0
    is_favorite: bool = False

class RecipeSearchRequest(BaseModel):
    ingredients: List[str] = []
    staples: List[str] = []
    use_soon: List[str] = []
    vegan: bool = False
    vegetarian: bool = False
    keto: bool = False
    gluten_free: bool = False
    allergies: List[str] = []
    max_missing: int = 6
    sort_by: str = "best_match" # "best_match", "expiry_first", "fastest"

class SubstitutionItem(BaseModel):
    original_ingredient: str
    substitute: str
    ratio: str
    notes: str
    dietary_compatibility: List[str] = []

class SubstitutionRequest(BaseModel):
    ingredient: str
    user_pantry: List[str] = []

class SubstitutionResponse(BaseModel):
    ingredient: str
    substitutions: List[SubstitutionItem]
    source: str  # "rule_base" or "llm_generated"

class ShoppingListItem(BaseModel):
    id: Optional[int] = None
    ingredient_name: str
    quantity: str = ""
    recipe_title: str = ""
    is_checked: bool = False

class ShoppingListAddRequest(BaseModel):
    items: List[Dict[str, str]]

class SystemStatusResponse(BaseModel):
    status: str
    vision_provider: str
    recipes_count: int
    staples_count: int
    cache_entries: int
    sqlite_ok: bool
    features_active: List[str]
