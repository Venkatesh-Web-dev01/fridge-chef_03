# 🍳 FridgeChef AI: Multimodal Recipe Generator from Fridge Photos

> **Hackathon Edition** — Turn open fridge photos into delicious, zero-waste dinners with AI vision, match-percentage ranking, culinary substitutions, and step-by-step cooking timers.

---
<div align="center">

  <h1>🍳 FridgeChef AI: Multimodal Recipe Generator from Fridge Photos</h1>

  <p>
    <strong>Hackathon Edition</strong> — Turn open fridge photos into delicious, zero-waste dinners with AI vision, match-percentage ranking, culinary substitutions, and step-by-step cooking timers.
  </p>

  <!-- Tech Stack Badges -->
  <p>
    <img src="https://img.shields.io/badge/React_18-20232A?style=for-the-badge&logo=react&logoColor=61DAFB" alt="React 18" />
    <img src="https://img.shields.io/badge/Vite-646CFF?style=for-the-badge&logo=vite&logoColor=white" alt="Vite" />
    <img src="https://img.shields.io/badge/Tailwind_CSS-38B2AC?style=for-the-badge&logo=tailwind-css&logoColor=white" alt="Tailwind CSS" />
    <img src="https://img.shields.io/badge/FastAPI-009688?style=for-the-badge&logo=fastapi&logoColor=white" alt="FastAPI" />
    <img src="https://img.shields.io/badge/Google_Gemini-8E75B2?style=for-the-badge&logo=googlegemini&logoColor=Dark Green" alt="Google Gemini" />
    <img src="https://img.shields.io/badge/OpenAI-412991?style=for-the-badge&logo=openai&logoColor=white" alt="OpenAI" />
    <img src="https://img.shields.io/badge/SQLite-003B57?style=for-the-badge&logo=sqlite&logoColor=white" alt="SQLite" />
  </p>

</div>

---

## 🌟 Problem & Objective

Almost everyone has stood in front of an open fridge wondering what to cook while produce and leftovers quietly go bad. Traditional recipe platforms ask you to buy what's missing rather than starting from what you actually have.

**FridgeChef AI** solves this by:
1. Identifying visible ingredients from fridge and pantry photos using Multimodal Vision AI.
2. Enabling an immediate confirm-and-edit step (renaming, deleting, and marking perishable items as **`♻️ Use Soon`**).
3. Ranking recipes by how many ingredients you own with an **Expiry-Aware Priority Bonus** to minimize food waste.
4. Supplying practical, tested culinary substitutions for whatever is missing.
5. Enforcing rule-based dietary filters (**Vegan, Vegetarian, Keto, Gluten-Free**) and hard allergen exclusions.
6. Providing a clean, distraction-free **Step-by-Step Cooking Mode** with built-in interactive countdown timers and audio chime alerts.
7. Generating a consolidated, downloadable **Shopping Checklist** for missing items across chosen recipes.

---

## 📐 Architecture Overview

```mermaid
flowchart TD
    subgraph Client ["Frontend: React 18 + Vite + Tailwind CSS"]
        UI_Upload["📷 Image Upload / Canvas Resizer / Presets"]
        UI_Editor["✏️ Confirmed Ingredients Editor & Use-Soon Tagger"]
        UI_Safety["🥬 Dietary & ⚠️ Allergen Exclusion Bar"]
        UI_Rank["📊 Ranked Recipe Grid & Match Badges"]
        UI_Detail["🔍 Recipe Details & 🔄 Substitutions Drawer"]
        UI_Cook["👨🍳 Distraction-Free Cooking Mode & ⏱️ Web Audio Timers"]
        UI_Shop["🛒 Smart Shopping Checklist (Copy / Download)"]
        UI_Pantry["🏠 Pantry Memory & 🧂 Kitchen Staples"]
    end

    subgraph Server ["Backend: Python FastAPI"]
        API["📡 FastAPI REST Endpoints & OpenAPI Docs"]
        Cache["⚡ Two-Tier Cache (In-Memory + SQLite)"]
        Resizer["🖼️ Pillow Pre-processing & Downscaling"]

        subgraph VisionEngine ["Vision Detection Engine"]
            V_Gemini["🧠 Google Gemini 1.5/2.0 Flash"]
            V_OpenAI["🧠 OpenAI GPT-4o Vision"]
            V_YOLO["🧩 YOLOv8 / HuggingFace Offline Stub"]
            V_Mock["🛟 Zero-Config Smart Mock Engine"]
        end

        subgraph CoreEngine ["Culinary Intelligence Engine"]
            Norm["🔤 Lemmatizer & Plural/Unit Stripper"]
            Fuzzy["🔎 Synonym Dictionary & RapidFuzz Matcher"]
            Ranker["📊 Match Scoring & ♻️ 'Use Soon' Bonus"]
            Subs["🔄 Contextual Substitutions Engine"]
            Safety["⚠️ Rule-Based Allergy & Diet Exclusion"]
        end

        subgraph DataAdapters ["Recipe & Data Adapters"]
            DB_Local["💾 SQLite Database & 36 Curated Recipes"]
            P_MealDB["🍽️ TheMealDB Free API Adapter"]
            P_Spoon["🍽️ Spoonacular Live Adapter"]
            P_USDA["🥦 USDA FoodData Central Hook"]
            P_OFF["📦 Open Food Facts Barcode Hook"]
            P_NLG["📚 RecipeNLG / Kaggle Dataset Loader"]
        end
    end

    UI_Upload --> Resizer --> VisionEngine
    VisionEngine --> API
    API --> CoreEngine
    CoreEngine --> DataAdapters
    DataAdapters --> DB_Local
    API --> Cache
```

---
graph TD
    User Photo/Input --> |Uploads Image| VisionEngine[Vision Detection Engine]
    VisionEngine --> |Gemini / GPT-4o / Fallback| ConfirmedItems[Confirmed Ingredients Editor]
    ConfirmedItems --> |Tag Expiry| ExpiryBoost[Use Soon Priority Bonus]
    ConfirmedItems --> |Apply Preferences| RulesEngine[Dietary & Allergen Filters]
    
    RulesEngine --> |Filtered Items| MatchingEngine[Matching & Ranking Engine]
    MatchingEngine --> |Fuzzy Match / Normalizer| DB[(Recipes DB & APIs)]
    
    DB --> |Ranked Results| UI[Frontend UI]
    UI --> |Missing Items| Subs[Substitution Engine]
    UI --> |Cooking Step| CookingMode[Interactive Step Cooking Mode]
    UI --> |Export| ShoppingList[Smart Shopping List]
## 🚀 Features Checklist

- [x] 📷 **Fridge/Pantry Photo Upload**: Drag-and-drop, file picker, and camera capture simulation.
- [x] ✍️ **Manual Ingredient Entry**: Quick chip input or comma-separated batch pasting.
- [x] 🤖 **AI/Vision Ingredient Detection**: Multimodal LLM (Gemini / OpenAI) with automatic fallback to high-accuracy offline smart mock.
- [x] ✏️ **Edit, Rename, Add, & Delete**: Full confirm-and-edit workflow with category badges and confidence indicators.
- [x] 🍳 **Recipe Generation & Retrieval**: 36+ curated authentic recipes + live TheMealDB & Spoonacular integrations.
- [x] 📊 **Ingredient Match Scoring & Ranking**: Percentages computed using owned items and pantry staples.
- [x] 🔄 **Culinary Substitutions**: 50+ tested cooking swaps with pantry-awareness.
- [x] 🥬 **Vegan**: Strict exclusion of all animal products.
- [x] 🥗 **Vegetarian**: Exclusion of meat, poultry, seafood, and gelatin.
- [x] 🥑 **Keto**: Net-carbs threshold ($\le 15$g/serving) and keto-tagged recipes.
- [x] 🌾 **Gluten-Free**: Strict wheat/gluten exclusion.
- [x] ⚠️ **Allergy Exclusion**: Rule-based exclusion for Peanuts, Tree Nuts, Dairy, Eggs, Soy, Shellfish, Fish, Wheat, and Sesame.
- [x] 🛒 **Shopping-List Generation**: One-click missing item rollup, checkbox tracking, clipboard copy, and `.txt` file download.
- [x] ♻️ **Expiry / "Use Soon" Concept**: Marking perishable items boosts recipe ranking score by $+15\%$ per expiring item to eliminate food waste.
- [x] ⭐ **Saved Favorites**: Bookmarking stored in SQLite.
- [x] 🏠 **Pantry Memory**: Persistent items stored across sessions.
- [x] 🧂 **Pantry Staples**: Toggleable kitchen basics (salt, pepper, olive oil, flour, garlic, etc.).
- [x] 🥗 **Nutrition Summary**: Calories, protein, carbs, fat, and fiber per serving with visual macro cards.
- [x] 👨🍳 **Step-by-Step Cooking Mode**: Clean, high-contrast, large-text counter view with keyboard navigation.
- [x] ⏱️ **Cooking Timers**: Interactive countdown timers with pause/reset and Web Audio chime alerts.
- [x] 🔤 **Ingredient Normalization**: Measurement stripping, plural reduction, and lemmatization.
- [x] 🔎 **Synonym & Fuzzy Matching**: Canonical dictionary mapping + RapidFuzz token sort matching.
- [x] 💾 **SQLite Architecture Boundary**: Repositories for pantry items, staples, favorites, shopping list, and query cache.
- [x] ⚡ **Caching**: Multi-tiered in-memory and SQLite caching to eliminate duplicate API calls.
- [x] 🖼️ **Image Resizing**: Canvas client-side compression + Pillow downscaling.
- [x] 🛟 **Mock-Data Fallback**: 100% functional out-of-the-box with zero API keys required.
- [x] 📡 **FastAPI Backend Architecture**: Modular router, services, schemas, and auto-generated Swagger UI at `/docs`.
- [x] 🧠 **Multimodal LLM Architecture**: Gemini 1.5/2.0 Flash & OpenAI GPT-4o compatibility.
- [x] 🧩 **YOLO/Hugging Face Offline Stub**: Edge AI object detection pipeline architecture.
- [x] 🍽️ **Spoonacular / TheMealDB Integration Points**: Live adapters for cloud recipe lookup.
- [x] 🥦 **USDA FoodData Central Integration Point**: Macro and micronutrient lookup service.
- [x] 📦 **Open Food Facts Extension Point**: Barcode product and allergen lookup.
- [x] 📚 **RecipeNLG/Kaggle Dataset Option**: Data ingestion pipeline for open recipe datasets.
- [x] ☁️ **Vercel/Netlify + Render/Railway Deployment**: Preconfigured `render.yaml`, `Procfile`, `Dockerfile`, `vercel.json`, `netlify.toml`.
- [x] 🎬 **Complete Hackathon Demo Flow**: 1-click guided demo tour banner guiding judges through the 6 core pitch milestones!

---

## 🔮 Future Roadmap & Advanced Architectural Concepts

### 1. Intelligent Inventory & Food Waste Analytics
* **Automated Shelf-Life Estimation:** Dynamic decay curves that calculate remaining shelf life based on visual freshness and storage domain.
* **Sustainability & Impact Dashboard:** Real-time calculation of avoided $CO_2e$ emissions and money saved through waste reduction.
* **Receipt & Invoice OCR:** Instant pantry ingestion by scanning digital or paper grocery receipts.

### 2. Advanced Vision & Edge AI Pipeline
* **In-Browser WebGPU Inference:** Low-latency object detection running locally via ONNX Runtime Web, saving cloud API credits.
* **Interactive Bounding Box Editor:** Visual photo canvas overlay showing detected item boundaries for tap-to-correct human feedback.

### 3. Graph-Based Culinary Engine & Vector RAG
* **Flavor Profile Graph (FlavorDB):** Dynamic substitution suggestions based on chemical compound similarity and flavor pairing matrices.
* **Vector Embeddings & Semantic Search:** Hybrid BM25 + Dense Retrieval (Qdrant/PGVector) for contextual natural language recipe queries.

## 🎬 2-Minute Hackathon Demo Pitch Script

Follow the interactive **"Guided Demo Tour"** banner at the top of the app to demonstrate the complete pitch:

1. **Step 1: Photo Ingest**
   - Click the preset button **"Family Fridge"** (or drag in your own photo).
   - *Pitch point:* "Our vision engine identifies visible produce, dairy, and proteins in seconds with automatic image downscaling."
2. **Step 2: Confirm & Edit (Human-in-the-loop)**
   - Click to rename an item or add a manual ingredient.
   - Click **`♻️ Use Soon`** on `baby spinach`.
   - *Pitch point:* "Vision is never perfect, so users can edit any item. Tagging spinach as 'Use Soon' signals to our engine that it's going bad."
3. **Step 3: Safety & Dietary Filters**
   - Toggle **Gluten-Free** or exclude **Peanuts**.
   - *Pitch point:* "We use deterministic, rule-based ingredient blacklists—not unpredictable LLM hallucinations—for allergen safety."
4. **Step 4: Match Ranking & Substitutions**
   - Notice how recipes are ranked with high match percentages (e.g. `83% Match`), and the spinach recipe displays the glowing badge: `♻️ Uses 1 expiring item!`.
   - Click "View Details" on an item missing sour cream to reveal the **Substitutions Drawer** (e.g., plain greek yogurt).
   - *Pitch point:* "Users never hit a dead end if an ingredient is missing."
5. **Step 5: Hands-Free Cooking Mode**
   - Click **Start Step-by-Step Cooking Mode**.
   - Show the large-font counter display and start the interactive **Step Timer** with Web Audio sound alert.
6. **Step 6: Smart Shopping List**
   - Click **Add all missing to list**, open the shopping checklist, check off items, and click **Copy** or **Download as .txt**.
   - *Pitch point:* "From 'What's in my fridge?' to 'Dinner is served and here is exactly what to buy next time'."

---

## 🛠️ Quick Local Setup

### 1. Run Backend (FastAPI)
```powershell
# From project root:
cd backend
python -m pip install -r requirements.txt
python -m uvicorn main:app --reload --port 8000
```
API Documentation will be live at: **http://127.0.0.1:8000/docs**

### 2. Run Frontend (React + Vite)
```powershell
# In a separate terminal:
cd frontend
npm install
npm run dev
```
Frontend Web UI will be live at: **http://localhost:5173**

*(Or simply double-click `run_dev.bat` on Windows!)*

---

## 🧪 Automated Testing

Run the comprehensive unit test suite:
```powershell
python backend/tests/test_engine.py
```
Validates:
- Normalizer (plurals, measurement units, synonyms)
- Fuzzy matching & RapidFuzz token sort
- Allergen rule-based exclusion
- Expiry-aware ranking boost
- Contextual culinary substitutions
- SQLite database persistence

git clone https://github.com/Venkatesh-Web-dev01/fridge-chef_03.git
cd fridge-chef_03


git add README.md
git commit -m "Update README.md"
git push origin main`     

 ## ⚙️ Core Logic & Decision Rules

The platform follows a deterministic, rule-based processing engine before querying or ranking recipes:

### 1. Hard Exclusion Rules (Safety & Dietary)
* **Allergen Filter (Strict):** If `user.allergens` contains item $A$, any recipe containing $A$ or its canonical synonyms is assigned a match score of `0%` and removed from the candidate pool.
* **Dietary Filter (Deterministic):**
  * **Vegan:** Exclude `meat`, `poultry`, `fish`, `seafood`, `dairy`, `eggs`, `honey`, `gelatin`.
  * **Vegetarian:** Exclude `meat`, `poultry`, `fish`, `seafood`, `gelatin`.
  * **Keto:** Filter recipes where `carbs_per_serving > 15g`.
  * **Gluten-Free:** Exclude `wheat`, `barley`, `rye`, `spelt`, `couscous`.

### 2. Match Scoring & Expiry Priority Algorithm
Recipes are ranked using an **Expiry-Aware Weighted Match Index**:

$$\text{Score} = \left( \frac{\text{Owned Ingredients Matching Recipe}}{\text{Total Recipe Ingredients}} \times 100 \right) + \left( 15 \times \text{Expiring Items Used} \right)$$

* **Base Match:** Computed against `Owned Pantry Items` + `Toggleable Kitchen Staples` (salt, oil, pepper, etc.).
* **"Use Soon" Priority Boost:** Each ingredient tagged as `♻️ Use Soon` adds a **+15 point boost** to the recipe's total rank score, prioritizing waste reduction.

### 3. Fallback & Substitution Logic
* **If Match Score < 60%:** Query the `Substitution Engine` for missing non-essential ingredients (e.g., replace *Sour Cream* with *Plain Greek Yogurt*).
* **Vision Service Fallback:** 
  `Gemini / GPT-4o Vision` ➔ *(On API Failure/Timeout)* ➔ `YOLO/HuggingFace Stub` ➔ *(Offline)* ➔ `Zero-Config Smart Mock`.

🚀 Advanced Features & Concepts to Add1. Smart Household & Expiry EngineDynamic Shelf-Life Predictor: Instead of manual "Use Soon" tags, use an ML model or heuristics matrix to auto-calculate remaining shelf life based on item category, visual freshness score, and typical storage conditions (fridge vs. counter).Automated Expiry Push Alerts: Web push notifications or webhook integrations (e.g., Slack/Telegram) warning users: "Your baby spinach expires in 2 days — here are 3 quick recipes to save it."Zero-Waste Impact Metrics: Compute and display estimated money saved ($$), carbon emissions ($CO_2e$) prevented, and kilograms of food waste avoided over time.

2. Multi-Modal Vision & Perception AIReceipt & Grocery Invoice Scanning (OCR): Allow users to upload grocery receipts to auto-populate the pantry alongside fridge/pantry photos using fine-tuned OCR + Named Entity Recognition (NER).Multi-Angle Photo Stitching / Batch Ingest: Process multiple images of different fridge shelves simultaneously and merge them into a unified deduplicated inventory.Bounding Box Visual Feedback: Show detected items directly overlaid on the user's photo with confidence scores, allowing users to tap on bounding boxes to correct mistakes.

3. Hyper-Personalized Culinary IntelligencePortion & Scaling Transformer Engine: Dynamically recalculate ingredient quantities and cooking times based on selected serving counts or macro target goals.Flavor Profile & Pairing Graph: Leverage a graph structure (e.g., NetworkX or Neo4j) to suggest ingredient substitutions based on flavor similarity matrices (sweet, savory, umami, acidity) rather than static lookup tables.Pantry-Aware Grocery Budgeting: When missing items are identified, fetch real-time local store prices (via supermarket APIs or scraping) to show the estimated cost needed to complete a recipe.

4. Production & AI Infrastructure UpgradesSemantic Vector Search (RAG): Store recipe embeddings in a vector database (e.g., Qdrant, ChromaDB, or PGVector) to enable semantic natural language queries like "Quick comfort food for a cold rainy evening using chicken."Edge Vision Processing (WebGPU / WASM): Run lightweight object detection models (e.g., YOLOv8-Nano) directly inside the user's browser using WebGPU/ONNX Runtime for instant, zero-latency ingredient extraction without API usage costs.LLM Guardrails & Structured Output Enforcement: Enforce JSON schema outputs from Gemini/GPT-4o using Pydantic or Instructor to guarantee zero parsing failures.
