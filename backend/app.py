from flask import Flask, jsonify, request
import sqlite3
import os
from flask_cors import CORS

app = Flask(__name__)

# Configure Flask-CORS to handle all routes and origins
CORS(app, resources={r"/*": {"origins": "*"}})

# Correct path to the database
DB_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), 'db', 'recipes.db'))

@app.route('/search', methods=['GET'])
def search_cocktails():
    """
    Search locally stored cocktails based on available ingredients.
    """
    ingredients = request.args.get('ingredients', '').split(',')
    if not ingredients:
        return jsonify({"error": "No ingredients provided"}), 400

    # Clean and lower-case input ingredients for consistent matching
    input_ingredients = [ingredient.strip().lower() for ingredient in ingredients if ingredient.strip()]

    connection = sqlite3.connect(DB_PATH)
    cursor = connection.cursor()

    # Fetch all cocktails and their ingredients
    query = """
        SELECT c.id, c.name, c.image_url, c.instructions, i.name AS ingredient_name, IFNULL(i.measure, 'N/A') AS ingredient_measure
        FROM cocktails c
        JOIN ingredients i ON c.id = i.cocktail_id
    """
    cursor.execute(query)
    results = cursor.fetchall()

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
                "match_count": 0,
                "total_ingredients": 0,
            }

        cocktails_dict[cocktail_id]["ingredients"].append({
            "name": ingredient_name.lower(),
            "measure": ingredient_measure,
        })

    # Calculate match count and split ingredients
    cocktails = []
    for cocktail in cocktails_dict.values():
        ingredients = cocktail["ingredients"]
        unique_ingredients = {ing["name"]: ing["measure"] for ing in ingredients}

        matched_ingredients = {name: measure for name, measure in unique_ingredients.items() if name in input_ingredients}
        missing_ingredients = {name: measure for name, measure in unique_ingredients.items() if name not in input_ingredients}

        match_count = len(matched_ingredients)
        total_ingredients = len(unique_ingredients)
        match_percentage = (match_count / total_ingredients) * 100 if total_ingredients > 0 else 0

        if match_count > 0:
            cocktail["match_count"] = match_count
            cocktail["match_percentage"] = match_percentage
            cocktail["matched_ingredients"] = [{"name": name, "measure": measure} for name, measure in matched_ingredients.items()]
            cocktail["missing_ingredients"] = [{"name": name, "measure": measure} for name, measure in missing_ingredients.items()]
            cocktails.append(cocktail)

    # Sort cocktails by match percentage and count
    cocktails.sort(key=lambda x: (-x["match_percentage"], -x["match_count"]))

    connection.close()
    return jsonify({"cocktails": cocktails[:3]})  # Return top 3 matches

if __name__ == "__main__":
    app.run(debug=True)
