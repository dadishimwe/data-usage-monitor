import os
import sys
# DON'T CHANGE THIS !!!
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from flask import Flask, send_from_directory
from flask_cors import CORS
from src.routes.data_usage import data_usage_bp
from src.routes.dashboard import dashboard_bp
from src.routes.system import system_bp

app = Flask(__name__, static_folder=os.path.join(os.path.dirname(__file__), 'static'))
app.config['SECRET_KEY'] = 'data-usage-monitor-secret-key-2024'

# Enable CORS for all routes
CORS(app)

# Register blueprints
app.register_blueprint(data_usage_bp, url_prefix='/api/data')
app.register_blueprint(dashboard_bp, url_prefix='/api/dashboard')
app.register_blueprint(system_bp, url_prefix='/api/system')

# Database configuration - using our custom SQLite database
DATABASE_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data_usage.db')

@app.route('/', defaults={'path': ''})
@app.route('/<path:path>')
def serve(path):
    static_folder_path = app.static_folder
    if static_folder_path is None:
        return "Static folder not configured", 404

    if path != "" and os.path.exists(os.path.join(static_folder_path, path)):
        return send_from_directory(static_folder_path, path)
    else:
        index_path = os.path.join(static_folder_path, 'index.html')
        if os.path.exists(index_path):
            return send_from_directory(static_folder_path, 'index.html')
        else:
            return "index.html not found", 404

@app.route('/health')
def health_check():
    return {'status': 'healthy', 'service': 'Data Usage Monitor API'}

if __name__ == '__main__':
    port = int(os.environ.get('FLASK_PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=True)

