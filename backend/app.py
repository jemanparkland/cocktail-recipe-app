from flask import Flask, jsonify, request
import sqlite3
import os
from flask_cors import CORS
from rapidfuzz import process

app = Flask(__name__)

# Configure Flask-CORS to handle all routes and origins
CORS(app, resources={r"/*": {"origins": "*"}})

# Correct path to the database
DB_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), 'db', 'recipes.db'))

# ✅ ADDING A ROOT ROUTE
@app.route('/')
def home():
    return "Cocktail Recipe API is Running!", 200

def get_all_cocktails():
    """Fetch all cocktails and their ingredients from the database."""
    connection = sqlite3.connect(DB_PATH)
    cursor = connection.cursor()

    query = """
        SELECT c.id, c.name, c.image_url, c.instructions, i.name AS ingredient_name, IFNULL(i.measure, 'N/A') AS ingredient_measure
        FROM cocktails c
        JOIN ingredients i ON c.id = i.cocktail_id
    """
    cursor.execute(query)
    results = cursor.fetchall()
    connection.close()

    # Organize results by cocktail
    cocktails_dict = {}
    for row in results:
        cocktail_id, name, image_url, instructions, ingredient_name, ingredient_measure = row
        if cocktail_id not in cocktails_dict:
            cocktails_dict[cocktail_id] = {
                "id": cocktail_id,
                "name": name,
                "image": image_url,
                "instructions": instructions or "No instructions available.",
                "ingredients": [],
            }
        cocktails_dict[cocktail_id]["ingredients"].append({
            "name": ingredient_name.lower(),
            "measure": ingredient_measure,
        })

    return list(cocktails_dict.values())

@app.route('/search', methods=['GET'])
def search_cocktails():
    """Search cocktails using fuzzy matching on ingredients."""
    ingredients = request.args.get('ingredients', '').split(',')
    if not ingredients:
        return jsonify({"error": "No ingredients provided"}), 400

    input_ingredients = [ingredient.strip().lower() for ingredient in ingredients if ingredient.strip()]
    cocktails = get_all_cocktails()

    matched_cocktails = []
    for cocktail in cocktails:
        ingredient_names = [ing["name"] for ing in cocktail["ingredients"]]

        # Fuzzy match input ingredients to available ingredients
        matched_ingredients = {}
        missing_ingredients = {}

        for user_ingredient in input_ingredients:
            best_match = process.extractOne(user_ingredient, ingredient_names, score_cutoff=80)
            if best_match:
                matched_ingredients[best_match[0]] = next(ing["measure"] for ing in cocktail["ingredients"] if ing["name"] == best_match[0])

        # Identify missing ingredients
        for ing in cocktail["ingredients"]:
            if ing["name"] not in matched_ingredients:
                missing_ingredients[ing["name"]] = ing["measure"]

        match_count = len(matched_ingredients)
        total_ingredients = len(cocktail["ingredients"])
        match_percentage = (match_count / total_ingredients) * 100 if total_ingredients > 0 else 0

        if match_count > 0:
            cocktail["match_count"] = match_count
            cocktail["match_percentage"] = match_percentage
            cocktail["matched_ingredients"] = [{"name": name, "measure": measure} for name, measure in matched_ingredients.items()]
            cocktail["missing_ingredients"] = [{"name": name, "measure": measure} for name, measure in missing_ingredients.items()]
            matched_cocktails.append(cocktail)

    # Sort cocktails by match percentage and count
    matched_cocktails.sort(key=lambda x: (-x["match_percentage"], -x["match_count"]))

    return jsonify({"cocktails": matched_cocktails[:3]})  # Return top 3 matches

if __name__ == "__main__":
    app.run(debug=True)
