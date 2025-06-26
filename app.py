# app.py

from flask import Flask, request, jsonify, abort, render_template, send_from_directory
import logging
import os

# Import the main analysis function and config
from analysis_logic import run_full_analysis
import config

# Initialize Flask App
app = Flask(__name__, static_folder='static', template_folder='templates')

# Configure logging to be consistent with the logic module
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

@app.route('/')
def index():
    """Serve the main frontend page."""
    return render_template('index.html')

@app.route('/static/visuals/<filename>')
def serve_visuals(filename):
    """Serve visualization images."""
    return send_from_directory(config.VISUALS_PATH, filename)

@app.route('/analyze', methods=['POST'])
def analyze_topic():
    """
    The main API endpoint. It expects a POST request with a JSON body
    containing a "topic" key.
    e.g., curl -X POST -H "Content-Type: application/json" -d '{"topic": "Fifa Club World Cup"}' http://127.0.0.1:5000/analyze
    """
    # Check if the request is JSON
    if not request.is_json:
        abort(415, description="Unsupported Media Type: Request must be JSON.")

    data = request.get_json()
    topic = data.get('topic')

    # Validate that 'topic' is present
    if not topic:
        abort(400, description="Bad Request: JSON body must contain a 'topic' key.")

    logging.info(f"Received analysis request for topic: '{topic}'")

    try:
        # Run the full analysis pipeline from our logic file
        results = run_full_analysis(topic, num_articles=25)
        
        # If the analysis returns an error (e.g., no articles found)
        if 'error' in results:
             return jsonify(results), 404 # Not Found or another appropriate status

        # Return the comprehensive results as a JSON response
        return jsonify(results)

    except ValueError as ve:
        # Catch specific errors like missing API key
        logging.error(f"Configuration error: {ve}")
        abort(500, description=str(ve))
    except Exception as e:
        # Catch any other unexpected errors during the analysis
        logging.error(f"An unexpected error occurred during analysis: {e}", exc_info=True)
        abort(500, description="An internal server error occurred.")


if __name__ == '__main__':
    # Check for NewsAPI key at startup
    if not config.NEWS_API_KEY:
        logging.warning("NEWS_API_KEY is not set. The service will not be able to fetch articles.")
    
    # Create necessary directories
    os.makedirs('templates', exist_ok=True)
    os.makedirs('static', exist_ok=True)
    os.makedirs(config.VISUALS_PATH, exist_ok=True)
    
    # Run the Flask app
    # host='0.0.0.0' makes it accessible from other devices on the same network
    app.run(host='0.0.0.0', port=5000, debug=True,threaded=True)