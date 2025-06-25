# config.py

import os

# --- IMPORTANT ---
# It is highly recommended to use environment variables for sensitive keys.
# Set this in your terminal before running the app:
# export NEWS_API_KEY='your_real_newsapi_key'
NEWS_API_KEY = os.environ.get('NEWS_API_KEY') #b78e862e1bb74cdba1748cc5ef292880

# --- File Paths ---
# Base directory for storing stateful data (model, history)
PROJECT_DATA_PATH = 'project_data'

# Directory for saving generated visualization images
VISUALS_PATH = os.path.join('static', 'visuals')