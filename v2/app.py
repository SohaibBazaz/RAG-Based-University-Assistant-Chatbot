import os
from flask import Flask, render_template, request, jsonify
from pipeline import answer_question # Import your core logic

# --- FLASK SETUP ---
app = Flask(__name__)
# Set a secret key for session management (important for production)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'a_default_secret_key_if_not_set')

@app.route("/", methods=["GET"])
def index():
    """Renders the main chat interface."""
    return render_template("index.html")

@app.route("/api/ask", methods=["POST"])
def ask():
    """API endpoint to process the user's question."""
    
    # 1. Get the user's question from the form data
    data = request.json
    user_query = data.get("query", "").strip()

    if not user_query:
        return jsonify({"answer": "Please enter a question."})

    try:
        # 2. Call your core logic function
        # The answer_question function will handle the entire RAG pipeline
        final_answer = answer_question(user_query)
        
        # 3. Return the result as a JSON response
        return jsonify({"answer": final_answer})

    except Exception as e:
        print(f"An error occurred: {e}")
        # Provide a helpful error message to the user
        return jsonify({"answer": f"Sorry, an internal error occurred: {e}"})

if __name__ == "__main__":
    # In a production environment like a hosted .sobaz.uk service, 
    # you might use a production WSGI server (e.g., Gunicorn).
    # For local testing, this is fine.
    app.run(debug=True)