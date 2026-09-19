import sqlite3
import json
import time
from typing import List, Dict, Any, Optional
from .config import DB_PATH

def get_db():
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db()
    cursor = conn.cursor()
    
    # 1. Pantry Items (memory of what user has)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS pantry_items (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT UNIQUE NOT NULL,
        category TEXT DEFAULT 'General',
        quantity REAL DEFAULT 1.0,
        unit TEXT DEFAULT '',
        use_soon INTEGER DEFAULT 0,
        updated_at REAL NOT NULL
    );
    """)
    
    # 2. Pantry Staples (common kitchen basics assumed present)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS pantry_staples (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT UNIQUE NOT NULL,
        is_active INTEGER DEFAULT 1,
        updated_at REAL NOT NULL
    );
    """)
    
    # 3. Favorite Recipes
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS favorite_recipes (
        recipe_id TEXT PRIMARY KEY,
        title TEXT NOT NULL,
        image_url TEXT,
        data_json TEXT NOT NULL,
        created_at REAL NOT NULL
    );
    """)
    
    # 4. Shopping List Items
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS shopping_list (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        ingredient_name TEXT NOT NULL,
        quantity TEXT DEFAULT '',
        recipe_title TEXT DEFAULT '',
        is_checked INTEGER DEFAULT 0,
        created_at REAL NOT NULL
    );
    """)
    
    # 5. Query Cache (for external vision and recipe API queries)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS query_cache (
        cache_key TEXT PRIMARY KEY,
        cache_value TEXT NOT NULL,
        expires_at REAL NOT NULL
    );
    """)

    # Seed default staples if empty
    cursor.execute("SELECT COUNT(*) as cnt FROM pantry_staples")
    if cursor.fetchone()["cnt"] == 0:
        default_staples = [
            "salt", "black pepper", "olive oil", "vegetable oil", 
            "water", "sugar", "all-purpose flour", "garlic"
        ]
        now = time.time()
        for staple in default_staples:
            cursor.execute(
                "INSERT OR IGNORE INTO pantry_staples (name, is_active, updated_at) VALUES (?, 1, ?)",
                (staple, now)
            )

    conn.commit()
    conn.close()

# Repository helpers
class PantryRepo:
    @staticmethod
    def get_items() -> List[Dict[str, Any]]:
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM pantry_items ORDER BY use_soon DESC, name ASC")
        rows = [dict(r) for r in cursor.fetchall()]
        conn.close()
        return rows

    @staticmethod
    def upsert_item(name: str, category: str = "General", quantity: float = 1.0, unit: str = "", use_soon: bool = False):
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO pantry_items (name, category, quantity, unit, use_soon, updated_at)
            VALUES (?, ?, ?, ?, ?, ?)
            ON CONFLICT(name) DO UPDATE SET
                category = excluded.category,
                quantity = excluded.quantity,
                unit = excluded.unit,
                use_soon = excluded.use_soon,
                updated_at = excluded.updated_at
        """, (name.lower().strip(), category, quantity, unit, 1 if use_soon else 0, time.time()))
        conn.commit()
        conn.close()

    @staticmethod
    def delete_item(name: str):
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM pantry_items WHERE LOWER(name) = ?", (name.lower().strip(),))
        conn.commit()
        conn.close()

    @staticmethod
    def get_staples() -> List[Dict[str, Any]]:
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM pantry_staples ORDER BY name ASC")
        rows = [dict(r) for r in cursor.fetchall()]
        conn.close()
        return rows

    @staticmethod
    def toggle_staple(name: str, is_active: bool):
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO pantry_staples (name, is_active, updated_at)
            VALUES (?, ?, ?)
            ON CONFLICT(name) DO UPDATE SET
                is_active = excluded.is_active,
                updated_at = excluded.updated_at
        """, (name.lower().strip(), 1 if is_active else 0, time.time()))
        conn.commit()
        conn.close()

class FavoritesRepo:
    @staticmethod
    def get_all() -> List[Dict[str, Any]]:
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM favorite_recipes ORDER BY created_at DESC")
        rows = []
        for r in cursor.fetchall():
            d = dict(r)
            d["recipe"] = json.loads(d["data_json"])
            rows.append(d)
        conn.close()
        return rows

    @staticmethod
    def is_favorite(recipe_id: str) -> bool:
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute("SELECT 1 FROM favorite_recipes WHERE recipe_id = ?", (recipe_id,))
        fav = cursor.fetchone() is not None
        conn.close()
        return fav

    @staticmethod
    def toggle(recipe_id: str, title: str, image_url: str, recipe_data: dict) -> bool:
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute("SELECT 1 FROM favorite_recipes WHERE recipe_id = ?", (recipe_id,))
        if cursor.fetchone():
            cursor.execute("DELETE FROM favorite_recipes WHERE recipe_id = ?", (recipe_id,))
            is_fav = False
        else:
            cursor.execute("""
                INSERT INTO favorite_recipes (recipe_id, title, image_url, data_json, created_at)
                VALUES (?, ?, ?, ?, ?)
            """, (recipe_id, title, image_url, json.dumps(recipe_data), time.time()))
            is_fav = True
        conn.commit()
        conn.close()
        return is_fav

class ShoppingListRepo:
    @staticmethod
    def get_all() -> List[Dict[str, Any]]:
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM shopping_list ORDER BY is_checked ASC, ingredient_name ASC")
        rows = [dict(r) for r in cursor.fetchall()]
        conn.close()
        return rows

    @staticmethod
    def add_items(items: List[Dict[str, str]]):
        conn = get_db()
        cursor = conn.cursor()
        now = time.time()
        for it in items:
            cursor.execute("""
                INSERT INTO shopping_list (ingredient_name, quantity, recipe_title, is_checked, created_at)
                VALUES (?, ?, ?, 0, ?)
            """, (it.get("ingredient_name", "").strip(), it.get("quantity", ""), it.get("recipe_title", ""), now))
        conn.commit()
        conn.close()

    @staticmethod
    def toggle_check(item_id: int, is_checked: bool):
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute("UPDATE shopping_list SET is_checked = ? WHERE id = ?", (1 if is_checked else 0, item_id))
        conn.commit()
        conn.close()

    @staticmethod
    def delete_item(item_id: int):
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM shopping_list WHERE id = ?", (item_id,))
        conn.commit()
        conn.close()

    @staticmethod
    def clear():
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM shopping_list")
        conn.commit()
        conn.close()

class CacheRepo:
    @staticmethod
    def get(cache_key: str) -> Optional[Any]:
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute("SELECT cache_value, expires_at FROM query_cache WHERE cache_key = ?", (cache_key,))
        row = cursor.fetchone()
        conn.close()
        if not row:
            return None
        if row["expires_at"] < time.time():
            CacheRepo.delete(cache_key)
            return None
        try:
            return json.loads(row["cache_value"])
        except Exception:
            return row["cache_value"]

    @staticmethod
    def set(cache_key: str, cache_value: Any, ttl_seconds: int = 3600):
        conn = get_db()
        cursor = conn.cursor()
        val_str = json.dumps(cache_value) if not isinstance(cache_value, str) else cache_value
        expires_at = time.time() + ttl_seconds
        cursor.execute("""
            INSERT INTO query_cache (cache_key, cache_value, expires_at)
            VALUES (?, ?, ?)
            ON CONFLICT(cache_key) DO UPDATE SET
                cache_value = excluded.cache_value,
                expires_at = excluded.expires_at
        """, (cache_key, val_str, expires_at))
        conn.commit()
        conn.close()

    @staticmethod
    def delete(cache_key: str):
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM query_cache WHERE cache_key = ?", (cache_key,))
        conn.commit()
        conn.close()
