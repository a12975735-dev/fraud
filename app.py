"""
Root entry point for the Flask API server.
Exposes the Flask app instance for WSGI deployment or local development.
"""

from src.flask_api import app

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
