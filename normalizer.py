import re
import json
from pathlib import Path
from typing import Optional, List, Tuple
from ..config import DATA_DIR

try:
    from rapidfuzz import fuzz
    RAPIDFUZZ_AVAILABLE = True
except ImportError:
    import difflib
    RAPIDFUZZ_AVAILABLE = False

# Load synonyms
SYNONYMS_FILE = DATA_DIR / "synonyms.json"
SYNONYMS_MAP = {}
if SYNONYMS_FILE.exists():
    try:
        with open(SYNONYMS_FILE, "r", encoding="utf-8") as f:
            raw_synonyms = json.load(f)
            for canonical, syn_list in raw_synonyms.items():
                canonical_lower = canonical.lower().strip()
                SYNONYMS_MAP[canonical_lower] = canonical_lower
                for s in syn_list:
                    SYNONYMS_MAP[s.lower().strip()] = canonical_lower
    except Exception as e:
        print(f"Failed to load synonyms: {e}")

UNITS_AND_PREP = [
    r"\b\d+([/.]\d+)?\s*(cups?|c|tbsp|tablespoons?|tsp|teaspoons?|oz|ounces?|g|grams?|kg|kilograms?|ml|milliliters?|l|liters?|lbs?|pounds?|pinch|pinches|can|cans|slice|slices|cloves?|sprigs?|bunch|bunches|head|heads|handful|handfuls|stalk|stalks|block|blocks)\b",
    r"\b(diced|chopped|minced|sliced|crushed|grated|wilted|cooked|uncooked|fresh|frozen|canned|raw|ripe|large|medium|small|clove|cloves|boneless|skinless|warm|cold|hot|melted|beaten|divided|finely|roughly|toasted|roasted)\b",
    r"\b\d+([/.]\d+)?\b",  # isolated numbers like '2 eggs'
    r"\(.*?\)",            # parentheticals like '(about 1 cup)'
    r"[,\.\*\-]"           # punctuation
]

COMMON_PLURALS = [
    (r"berries$", "berry"),
    (r"tomatoes$", "tomato"),
    (r"potatoes$", "potato"),
    (r"leaves$", "leaf"),
    (r"halves$", "half"),
    (r"onions$", "onion"),
    (r"peppers$", "pepper"),
    (r"mushrooms$", "mushroom"),
    (r"eggs$", "egg"),
    (r"carrots$", "carrot"),
    (r"beans$", "bean"),
    (r"cloves$", "clove"),
    (r"fillets$", "fillet"),
    (r"breasts$", "breast"),
    (r"thighs$", "thigh"),
    (r"steaks$", "steak"),
    (r"noodles$", "noodle"),
    (r"ribbons$", "ribbon"),
    (r"tortillas$", "tortilla"),
    (r"lemons$", "lemon"),
    (r"limes$", "lime"),
    (r"scallions$", "scallion"),
    (r"s$", "") # general fallback singular
]

def clean_ingredient_text(raw_text: str) -> str:
    """Removes numbers, units, preparation words, and excessive whitespaces."""
    text = raw_text.lower().strip()
    for pat in UNITS_AND_PREP:
        text = re.sub(pat, " ", text, flags=re.IGNORECASE)
    # Remove extra spaces
    text = re.sub(r"\s+", " ", text).strip()
    return text

def singularize_word(word: str) -> str:
    """Reduces regular food plurals to singular form."""
    w = word.strip()
    if w in ("asparagus", "hummus", "couscous", "molasses", "citrus", "watercress", "grass"):
        return w

    for pattern, replacement in COMMON_PLURALS:
        if re.search(pattern, w):
            return re.sub(pattern, replacement, w)
    return w

def normalize_ingredient(raw_text: str) -> str:
    """
    Complete normalization pipeline:
    1. Clean prep words & numbers
    2. Check direct synonym map on raw or cleaned
    3. Singularize individual words
    4. Apply canonical culinary synonym mapping
    """
    cleaned = clean_ingredient_text(raw_text)
    if not cleaned:
        cleaned = raw_text.lower().strip()

    if cleaned in SYNONYMS_MAP:
        return SYNONYMS_MAP[cleaned]

    # Singularize individual words
    words = cleaned.split()
    singular_words = [singularize_word(w) for w in words]
    candidate = " ".join(singular_words).strip()

    if candidate in SYNONYMS_MAP:
        return SYNONYMS_MAP[candidate]

    # Check sub-phrases
    for syn_key, canonical in SYNONYMS_MAP.items():
        if f" {syn_key} " in f" {candidate} " or candidate == syn_key:
            return canonical

    return candidate

def fuzzy_match_score(term1: str, term2: str) -> float:
    """
    Calculates similarity ratio between 0 and 100.
    Uses RapidFuzz token sort ratio or difflib fallback.
    """
    t1 = normalize_ingredient(term1)
    t2 = normalize_ingredient(term2)
    
    if t1 == t2:
        return 100.0
    if t1 in t2 or t2 in t1:
        return 90.0

    if RAPIDFUZZ_AVAILABLE:
        return float(fuzz.token_sort_ratio(t1, t2))
    else:
        matcher = difflib.SequenceMatcher(None, t1, t2)
        return matcher.ratio() * 100.0

def is_ingredient_match(user_item: str, recipe_item: str, threshold: float = 75.0) -> bool:
    """Determines whether a user ingredient matches a recipe ingredient."""
    score = fuzzy_match_score(user_item, recipe_item)
    return score >= threshold
