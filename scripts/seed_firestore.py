# Copyright 2026 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""Seed initial recipes into Firestore for ChefGenie."""

from google.cloud import firestore

PROJECT_ID = "qwiklabs-gcp-01-1294b1272871"

SEED_RECIPES = [
    {
        "id": "garlic-ginger-chicken",
        "title": "Garlic Ginger Chicken & Vegetable Stir-Fry",
        "category": "Dinner",
        "prep_time_minutes": 10,
        "cook_time_minutes": 10,
        "servings": 2,
        "dietary_tags": ["gluten-free", "dairy-free", "high-protein", "quick"],
        "ingredients": [
            "1 lb boneless chicken breast, cut into bite-sized pieces",
            "2 cups broccoli florets",
            "1 red bell pepper, sliced",
            "3 tbsp Tamari or Coconut Aminos",
            "1 tbsp sesame oil",
            "2 cloves garlic, minced",
            "1 tsp fresh ginger, grated",
        ],
        "instructions": "1. Whisk sauce. 2. Cook chicken for 5-6 mins. 3. Sauté veggies. 4. Combine and simmer with sauce for 2 mins.",
        "calories": 420,
    },
    {
        "id": "mediterranean-quinoa-bowl",
        "title": "Mediterranean Quinoa & Chickpea Salad Bowl",
        "category": "Lunch",
        "prep_time_minutes": 15,
        "cook_time_minutes": 0,
        "servings": 2,
        "dietary_tags": ["gluten-free", "dairy-free", "vegan", "vegetarian"],
        "ingredients": [
            "2 cups cooked quinoa",
            "1 can (15 oz) chickpeas, rinsed and drained",
            "1 cup cherry tomatoes, halved",
            "1 cucumber, diced",
            "1/4 cup kalamata olives",
            "2 tbsp extra virgin olive oil",
            "1 tbsp lemon juice",
        ],
        "instructions": "1. Combine cooked quinoa, chickpeas, tomatoes, and cucumber. 2. Whisk olive oil and lemon juice. 3. Toss together and serve chilled.",
        "calories": 380,
    },
    {
        "id": "berry-chia-pudding",
        "title": "Overnight Berry Chia Seed Pudding",
        "category": "Breakfast",
        "prep_time_minutes": 5,
        "cook_time_minutes": 0,
        "servings": 1,
        "dietary_tags": ["gluten-free", "dairy-free", "vegan", "low-prep"],
        "ingredients": [
            "3 tbsp chia seeds",
            "1 cup almond milk or coconut milk",
            "1/2 cup fresh mixed berries",
            "1 tbsp maple syrup",
            "1/2 tsp vanilla extract",
        ],
        "instructions": "1. Mix chia seeds, almond milk, maple syrup, and vanilla in a jar. 2. Refrigerate overnight. 3. Top with berries before serving.",
        "calories": 250,
    },
]


def seed_firestore():
    """Seed recipes into the Firestore 'recipes' collection."""
    db = firestore.Client(project=PROJECT_ID)
    recipes_ref = db.collection("recipes")

    print(f"Seeding recipes into Firestore project '{PROJECT_ID}'...")
    for recipe in SEED_RECIPES:
        doc_id = recipe["id"]
        doc_data = {k: v for k, v in recipe.items() if k != "id"}
        recipes_ref.document(doc_id).set(doc_data)
        print(f"  - Seeded: {doc_id} ('{recipe['title']}')")

    print("Seeding complete!")


if __name__ == "__main__":
    seed_firestore()
