document.addEventListener('DOMContentLoaded', () => {
    const form = document.getElementById('ingredient-form');
    const ingredientInput = document.getElementById('ingredient-input');
    const resultsDiv = document.getElementById('results');

    form.addEventListener('submit', async (event) => {
        event.preventDefault();
        resultsDiv.innerHTML = 'Searching...';

        const input = ingredientInput.value.trim();
        if (!input) {
            resultsDiv.innerHTML = 'Please enter at least one ingredient.';
            return;
        }

        const ingredients = input.split(',').map(ingredient => ingredient.trim()).filter(Boolean);

        try {
            const response = await fetch(`http://127.0.0.1:5000/search?ingredients=${ingredients.join(',')}`, {
                method: 'GET',
                headers: { 'Content-Type': 'application/json' },
            });

            if (!response.ok) {
                throw new Error(`HTTP error! Status: ${response.status}`);
            }

            const data = await response.json();
            displayResults(data);
        } catch (error) {
            console.error('Error fetching data:', error);
            resultsDiv.innerHTML = 'Error fetching data. Please try again later.';
        }
    });

    function displayResults(data) {
        if (data.cocktails && data.cocktails.length > 0) {
            resultsDiv.innerHTML = `
                <h2>Top 3 Matching Cocktails:</h2>
                <div class="cocktail-results">
                    ${data.cocktails.map(cocktail => `
                        <div class="cocktail-item">
                            <div class="cocktail-header">
                                <img src="${cocktail.image}" alt="${cocktail.name}" class="cocktail-image">
                                <div class="cocktail-info">
                                    <h3>${cocktail.name}</h3>
                                    <p><strong>Match Count:</strong> ${cocktail.match_count}</p>
                                    <button class="toggle-ingredients">Show Recipe</button>
                                </div>
                            </div>
                            <div class="cocktail-details hidden">
                                <h4>Ingredients you already have:</h4>
                                <ul>
                                    ${(cocktail.matched_ingredients || []).map(ingredient => `
                                        <li>${ingredient.name} - ${ingredient.measure}</li>
                                    `).join('') || '<li>None</li>'}
                                </ul>
                                <h4>Other ingredients needed:</h4>
                                <ul>
                                    ${(cocktail.missing_ingredients || []).map(ingredient => `
                                        <li>${ingredient.name} - ${ingredient.measure}</li>
                                    `).join('') || '<li>None</li>'}
                                </ul>
                                <h4>Instructions:</h4>
                                <ol>
                                    ${(cocktail.instructions || "No instructions available.")
                                        .split('. ')
                                        .filter(step => step.trim() !== '')
                                        .map(step => `<li>${step.trim()}</li>`)
                                        .join('')}
                                </ol>
                            </div>
                        </div>
                    `).join('')}
                </div>
            `;

            document.querySelectorAll('.toggle-ingredients').forEach(button => {
                button.addEventListener('click', (event) => {
                    const details = event.target.closest('.cocktail-item').querySelector('.cocktail-details');
                    details.classList.toggle('hidden');
                    event.target.textContent = details.classList.contains('hidden') ? 'Show Recipe' : 'Hide Recipe';
                });
            });
        } else {
            resultsDiv.innerHTML = 'No cocktails found for the given ingredients.';
        }
    }
});
