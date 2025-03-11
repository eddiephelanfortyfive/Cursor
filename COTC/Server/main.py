from api.endpoints import app
import json

if __name__ == '__main__':
    # Load configuration
    with open('config/config.json', 'r') as config_file:
        config = json.load(config_file)
    port = config['port']
    # Run Flask app - database is already initialized in endpoints.py
    app.run(debug=True, port=port)