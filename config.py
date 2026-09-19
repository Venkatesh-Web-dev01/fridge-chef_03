import os
from pathlib import Path
from pydantic import BaseModel

BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"
STATIC_DIR = BASE_DIR / "static"
DB_PATH = BASE_DIR / "fridge_chef.db"

class Settings(BaseModel):
    app_name: str = "FridgeChef AI API"
    app_version: str = "1.0.0"
    debug: bool = True
    
    # API Keys (optional; app defaults to zero-config smart mock fallback if missing)
    gemini_api_key: str = os.getenv("GEMINI_API_KEY", "")
    openai_api_key: str = os.getenv("OPENAI_API_KEY", "")
    spoonacular_api_key: str = os.getenv("SPOONACULAR_API_KEY", "")
    edamam_app_id: str = os.getenv("EDAMAM_APP_ID", "")
    edamam_app_key: str = os.getenv("EDAMAM_APP_KEY", "")
    usda_api_key: str = os.getenv("USDA_API_KEY", "")
    
    # Cache settings
    cache_ttl_seconds: int = 3600  # 1 hour
    
    # Image resize settings
    max_image_dimension: int = 1024
    image_jpeg_quality: int = 85

settings = Settings()
