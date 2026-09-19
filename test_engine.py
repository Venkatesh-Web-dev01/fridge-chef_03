import sys
import unittest
from pathlib import Path

# Add backend parent to sys.path
backend_dir = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(backend_dir.parent))

from backend.services.normalizer import normalize_ingredient, fuzzy_match_score, is_ingredient_match
from backend.services.safety_filter import SafetyFilter
from backend.services.matching_engine import MatchingEngine
from backend.services.substitution_service import SubstitutionService
from backend.database import init_db, PantryRepo, FavoritesRepo, ShoppingListRepo
from backend.models.schemas import RecipeSearchRequest
from backend.services.recipe_service import RecipeService

class TestFridgeChefEngine(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        init_db()

    def test_normalizer_plurals_and_units(self):
        self.assertEqual(normalize_ingredient("2 cups diced tomatoes"), "tomato")
        self.assertEqual(normalize_ingredient("3 large eggs"), "egg")
        self.assertEqual(normalize_ingredient("1 can black beans"), "black bean")
        self.assertEqual(normalize_ingredient("fresh baby spinach"), "baby spinach")
        self.assertEqual(normalize_ingredient("scallions"), "green onion")
        self.assertEqual(normalize_ingredient("aubergine"), "eggplant")
        self.assertEqual(normalize_ingredient("coriander"), "cilantro")

    def test_fuzzy_matching(self):
        self.assertTrue(is_ingredient_match("tomato", "cherry tomatoes"))
        self.assertTrue(is_ingredient_match("egg", "large farm eggs"))
        self.assertTrue(is_ingredient_match("cheddar", "sharp cheddar cheese"))
        self.assertTrue(is_ingredient_match("green onions", "scallions"))

    def test_safety_filter_allergen_exclusion(self):
        dummy_recipe = {
            "title": "Thai Peanut Noodles",
            "allergens": ["peanuts", "wheat_gluten"],
            "dietary_tags": ["vegetarian"],
            "ingredients": ["egg noodles", "peanut butter", "soy sauce"]
        }
        # Excluding peanuts should reject
        self.assertFalse(SafetyFilter.is_recipe_safe(dummy_recipe, allergies=["peanuts"]))
        # Excluding dairy should pass
        self.assertTrue(SafetyFilter.is_recipe_safe(dummy_recipe, allergies=["dairy"]))

    def test_safety_filter_dietary(self):
        meat_recipe = {
            "title": "Bacon Burger",
            "dietary_tags": [],
            "allergens": ["dairy"],
            "ingredients": ["ground beef", "bacon", "cheddar"]
        }
        self.assertFalse(SafetyFilter.is_recipe_safe(meat_recipe, allergies=[], vegetarian=True))
        self.assertFalse(SafetyFilter.is_recipe_safe(meat_recipe, allergies=[], vegan=True))

        vegan_salad = {
            "title": "Chickpea Salad",
            "dietary_tags": ["vegan", "vegetarian", "gluten-free"],
            "allergens": [],
            "ingredients": ["chickpeas", "cucumber", "olive oil"]
        }
        self.assertTrue(SafetyFilter.is_recipe_safe(vegan_salad, allergies=[], vegan=True))

    def test_expiry_aware_ranking_boost(self):
        sample_recipe = {
            "id": "test-1",
            "title": "Spinach Omelette",
            "description": "Test",
            "image_url": "",
            "prep_time_min": 5,
            "cook_time_min": 5,
            "servings": 1,
            "difficulty": "Easy",
            "cuisine": "Test",
            "ingredients": ["3 large eggs", "1 cup baby spinach", "1 tbsp butter", "1 pinch salt"],
            "instructions": [],
            "nutrition": {"calories": 200, "protein_g": 10, "carbs_g": 2, "fat_g": 15, "fiber_g": 1}
        }
        # Without expiry flag
        score1, matching1, missing1, exp1 = MatchingEngine.evaluate_recipe_match(
            recipe_dict=sample_recipe,
            user_ingredients=["eggs", "spinach", "butter"],
            staples=["salt"],
            use_soon_items=[]
        )
        self.assertEqual(score1, 100.0)
        self.assertEqual(exp1, 0)

        # With partial items, with spinach expiring
        score2, matching2, missing2, exp2 = MatchingEngine.evaluate_recipe_match(
            recipe_dict=sample_recipe,
            user_ingredients=["spinach"],
            staples=[],
            use_soon_items=["spinach"]
        )
        # 1 of 4 ingredients owned = 25% + 15% expiry boost = 40%
        self.assertEqual(exp2, 1)
        self.assertEqual(score2, 40.0)

    def test_substitutions(self):
        resp = SubstitutionService.get_substitutions("sour cream", user_pantry=["greek yogurt"])
        self.assertTrue(len(resp.substitutions) > 0)
        first_sub = resp.substitutions[0]
        self.assertIn("greek yogurt", first_sub.substitute.lower())
        self.assertIn("pantry", first_sub.notes.lower())

    def test_sqlite_persistence(self):
        # Test Pantry
        PantryRepo.upsert_item("avocado", category="Produce", use_soon=True)
        items = PantryRepo.get_items()
        item_names = [i["name"] for i in items]
        self.assertIn("avocado", item_names)

        # Test Favorites
        is_fav = FavoritesRepo.toggle("test-recipe-1", "Test Recipe", "", {"id": "test-recipe-1"})
        self.assertTrue(is_fav)
        self.assertTrue(FavoritesRepo.is_favorite("test-recipe-1"))
        is_fav_again = FavoritesRepo.toggle("test-recipe-1", "Test Recipe", "", {})
        self.assertFalse(is_fav_again)

        # Test Shopping list
        ShoppingListRepo.add_items([{"ingredient_name": "sour cream", "quantity": "1 tub", "recipe_title": "Tacos"}])
        sl = ShoppingListRepo.get_all()
        self.assertTrue(any(s["ingredient_name"] == "sour cream" for s in sl))

if __name__ == "__main__":
    unittest.main()
