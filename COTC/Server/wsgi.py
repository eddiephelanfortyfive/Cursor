import sys
import os

# Add your project directory to the Python path
# Update this path to match your actual PythonAnywhere directory structure
path = '/home/eddiephelan45/Cursor/COTC/Server'
if path not in sys.path:
    sys.path.append(path)

# Import your Flask application
from server import flask_app as application

# Show which path we're using for debugging
print(f"Using path: {path}")
print(f"sys.path: {sys.path}") 