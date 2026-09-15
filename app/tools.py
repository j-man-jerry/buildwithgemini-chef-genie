"""Custom tool definitions for ChefGenie agent including Firestore integration."""

import datetime
from typing import List, Optional
from google.adk.tools import ToolContext
from google import genai
from google.genai import types
from google.cloud import firestore
from google.cloud import storage

PROJECT_ID = "qwiklabs-gcp-01-1294b1272871"



def get_firestore_client() -> firestore.Client:
    """Get initialized Firestore client using hardcoded GCP Project ID."""
    return firestore.Client(project=PROJECT_ID)


def convert_currency(amount: float, from_curr: str, to_curr: str) -> str:
    """Converts currency amounts between USD, EUR, GBP, and JPY using mock conversion rates.

    Args:
        amount: The monetary amount to convert.
        from_curr: The source 3-letter currency code (e.g. USD, EUR, GBP, JPY).
        to_curr: The target 3-letter currency code (e.g. USD, EUR, GBP, JPY).

    Returns:
        A string describing the converted amount.
    """
    rates = {
        "USD": 1.0,
        "EUR": 0.92,
        "GBP": 0.78,
        "JPY": 155.0,
    }

    from_code = from_curr.upper()
    to_code = to_curr.upper()

    if from_code not in rates or to_code not in rates:
        return f"Unsupported currency conversion from {from_curr} to {to_curr}. Supported: {list(rates.keys())}"

    amount_in_usd = amount / rates[from_code]
    converted = amount_in_usd * rates[to_code]

    return f"{amount:.2f} {from_code} = {converted:.2f} {to_code}"


def search_recipes_firestore(
    query: str = "", category: str = "", dietary_tag: str = ""
) -> str:
    """Searches and reads recipes from the Firestore 'recipes' collection.

    Args:
        query: Optional search keyword to filter by title or ingredients.
        category: Optional category filter (e.g. "Dinner", "Breakfast", "Lunch").
        dietary_tag: Optional dietary tag filter (e.g. "gluten-free", "dairy-free", "vegan").

    Returns:
        A string summarizing matching recipes found in Firestore.
    """
    db = get_firestore_client()
    recipes_ref = db.collection("recipes")
    docs = recipes_ref.stream()

    results = []
    for doc in docs:
        data = doc.to_dict()
        doc_id = doc.id
        title = data.get("title", "Untitled")
        cat = data.get("category", "")
        tags = data.get("dietary_tags", [])
        ingredients = data.get("ingredients", [])

        # Filter by category if specified
        if category and category.lower() not in cat.lower():
            continue

        # Filter by dietary tag if specified
        if dietary_tag and not any(dietary_tag.lower() in t.lower() for t in tags):
            continue

        # Filter by search query if specified
        if query:
            q = query.lower()
            in_title = q in title.lower()
            in_ing = any(q in ing.lower() for ing in ingredients)
            if not (in_title or in_ing):
                continue

        results.append(
            f"ID: {doc_id}\n"
            f"Title: {title}\n"
            f"Category: {cat}\n"
            f"Dietary Tags: {', '.join(tags)}\n"
            f"Prep Time: {data.get('prep_time_minutes', 0)} mins | Cook Time: {data.get('cook_time_minutes', 0)} mins | Calories: {data.get('calories', 0)}\n"
            f"Ingredients:\n  - " + "\n  - ".join(ingredients) + "\n"
            f"Instructions: {data.get('instructions', '')}\n"
        )

    if not results:
        return "No matching recipes found in Firestore database."

    return f"Found {len(results)} recipe(s) in Firestore:\n\n" + "\n---\n".join(results)


def save_recipe_firestore(
    title: str,
    category: str,
    prep_time_minutes: int,
    cook_time_minutes: int,
    servings: int,
    dietary_tags: List[str],
    ingredients: List[str],
    instructions: str,
    calories: int,
) -> str:
    """Saves a new recipe to the Firestore 'recipes' collection.

    Args:
        title: The title of the recipe.
        category: Recipe category (e.g. "Dinner", "Breakfast", "Lunch", "Snack").
        prep_time_minutes: Preparation time in minutes.
        cook_time_minutes: Cooking time in minutes.
        servings: Number of servings.
        dietary_tags: List of dietary tags (e.g. ["gluten-free", "dairy-free"]).
        ingredients: List of ingredient strings with quantities.
        instructions: Cooking step-by-step instructions.
        calories: Estimated calories per serving.

    Returns:
        A success message with the document ID of the saved recipe.
    """
    db = get_firestore_client()
    doc_slug = title.lower().replace(" ", "-").replace("&", "and")
    # Clean doc_slug
    doc_id = "".join(c for c in doc_slug if c.isalnum() or c == "-") or "recipe"

    doc_data = {
        "title": title,
        "category": category,
        "prep_time_minutes": prep_time_minutes,
        "cook_time_minutes": cook_time_minutes,
        "servings": servings,
        "dietary_tags": dietary_tags,
        "ingredients": ingredients,
        "instructions": instructions,
        "calories": calories,
    }

    db.collection("recipes").document(doc_id).set(doc_data)
    return f"Successfully saved recipe '{title}' to Firestore with ID '{doc_id}'."


import re


def parse_and_scale_quantity(ingredient_str: str, scale_factor: float) -> str:
    """Helper to scale leading numbers/fractions in an ingredient string."""

    def replace_match(match):
        val_str = match.group(0)
        if "/" in val_str:
            num, den = val_str.split("/")
            val = float(num) / float(den)
        else:
            val = float(val_str)
        scaled_val = val * scale_factor
        if scaled_val.is_integer():
            return str(int(scaled_val))
        return f"{scaled_val:.2f}".rstrip("0").rstrip(".")

    return re.sub(r"^\s*(\d+/\d+|\d+(?:\.\d+)?)", replace_match, ingredient_str)


def scale_recipe_nutrition(
    recipe_title: str,
    base_servings: int,
    target_servings: int,
    ingredients: List[str],
    calories_per_serving: float,
    protein_g: float = 0.0,
    carbs_g: float = 0.0,
    fat_g: float = 0.0,
) -> str:
    """Scales ingredient quantities and calculates macro/calorie breakdowns for a target serving size.

    Args:
        recipe_title: Title of the recipe.
        base_servings: Original serving size of the recipe (e.g., 2).
        target_servings: Target serving size required (e.g., 4 or 6).
        ingredients: List of ingredient strings with base quantities.
        calories_per_serving: Calories per single serving.
        protein_g: Protein in grams per single serving.
        carbs_g: Carbohydrates in grams per single serving.
        fat_g: Fat in grams per single serving.

    Returns:
        Formatted summary showing scaled ingredients, total batch macros, and per-serving breakdown.
    """
    if base_servings <= 0 or target_servings <= 0:
        return "Error: Servings must be positive integers."

    scale_factor = target_servings / base_servings

    scaled_ingredients = [
        parse_and_scale_quantity(ing, scale_factor) for ing in ingredients
    ]

    total_calories = calories_per_serving * target_servings
    total_protein = protein_g * target_servings
    total_carbs = carbs_g * target_servings
    total_fat = fat_g * target_servings

    lines = [
        f"📊 **Scaled Recipe & Nutrition Breakdown for '{recipe_title}'**",
        f"• Base Servings: {base_servings} ➔ **Target Servings: {target_servings}** (Scaling Factor: {scale_factor:.2f}x)",
        "",
        "🥣 **Scaled Ingredients:**",
    ]
    for ing in scaled_ingredients:
        lines.append(f"  - {ing}")

    lines.extend([
        "",
        "🔥 **Nutritional Summary:**",
        f"  - **Calories per serving:** {calories_per_serving:.0f} kcal (Total Batch: {total_calories:.0f} kcal)",
    ])

    if protein_g or carbs_g or fat_g:
        lines.extend([
            f"  - **Protein per serving:** {protein_g:.1f} g (Total Batch: {total_protein:.1f} g)",
            f"  - **Carbs per serving:** {carbs_g:.1f} g (Total Batch: {total_carbs:.1f} g)",
            f"  - **Fat per serving:** {fat_g:.1f} g (Total Batch: {total_fat:.1f} g)",
        ])

    return "\n".join(lines)


RAG_CORPUS_NAME = "projects/178057287160/locations/us-central1/ragCorpora/1849668828988964864"


def consult_herbal_corpus(query: str) -> str:
    """Searches Culpeper's Complete Herbal reference corpus for traditional herbal remedies, plant uses, recipes, and botanical knowledge.

    Args:
        query: What to look up (a plant, herb, ailment, ingredient, or recipe).

    Returns:
        Matched passages from the herbal reference book, or a note if none were found.
    """
    import vertexai
    from vertexai.preview import rag

    try:
        vertexai.init(project=PROJECT_ID, location="us-central1")
        resp = rag.retrieval_query(
            text=query,
            rag_resources=[rag.RagResource(rag_corpus=RAG_CORPUS_NAME)],
            rag_retrieval_config=rag.RagRetrievalConfig(top_k=5),
        )
    except Exception as e:
        return f"Retrieval failed: {e}"

    contexts = getattr(resp.contexts, "contexts", [])
    passages = [c.text.strip() for c in contexts if getattr(c, "text", "").strip()]
    return "\n\n---\n\n".join(passages) or "No relevant passages found in herbal corpus."


BUCKET_NAME = "chef-genie-media-qwiklabs-gcp-01-1294b1272871"


async def generate_dish_image(prompt: str, tool_context: ToolContext) -> str:
    """Generates a vibrant, appetizing visual image of a custom dish or recipe, saves it as an artifact, and uploads it to public Cloud Storage.

    Args:
        prompt: A detailed, appetizing description of the food item, dish, or plating presentation to generate.

    Returns:
        The public HTTPS URL of the generated image.
    """
    client = genai.Client(vertexai=True, project=PROJECT_ID, location="global")

    try:
        res = client.models.generate_content(
            model="gemini-3.1-flash-lite-image",
            contents=prompt,
            config=types.GenerateContentConfig(
                response_modalities=["IMAGE"],
            )
        )
    except Exception as e:
        return f"Image generation failed: {e}"

    if not res.candidates or not res.candidates[0].content.parts:
        return "Failed to generate image: no content parts returned from model."

    part = res.candidates[0].content.parts[0]
    if not part.inline_data or not part.inline_data.data:
        return "Failed to generate image: part does not contain image bytes."

    img_bytes = part.inline_data.data
    mime_type = part.inline_data.mime_type or "image/jpeg"

    # Define unique filename/object name
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"food_{timestamp}.jpg"

    # Save to Playground Artifacts panel
    try:
        artifact_part = types.Part.from_bytes(data=img_bytes, mime_type=mime_type)
        await tool_context.save_artifact(filename=filename, artifact=artifact_part)
    except Exception as e:
        print(f"Warning: Failed to save artifact: {e}")

    # Upload directly to GCS bucket
    try:
        storage_client = storage.Client(project=PROJECT_ID)
        bucket = storage_client.bucket(BUCKET_NAME)
        blob_name = f"images/{filename}"
        blob = bucket.blob(blob_name)
        blob.upload_from_string(img_bytes, content_type=mime_type)
        public_url = f"https://storage.googleapis.com/{BUCKET_NAME}/{blob_name}"
        return f"Successfully generated dish image. Public GCS URL:\n{public_url}"
    except Exception as e:
        return f"Dish image saved to artifacts, but public Cloud Storage upload failed: {e}"



