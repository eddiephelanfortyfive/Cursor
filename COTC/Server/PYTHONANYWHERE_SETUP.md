# Deploying to PythonAnywhere

This guide outlines the steps to deploy this application to PythonAnywhere.

## Step 1: Sign up for PythonAnywhere Account

If you don't already have one, sign up for a PythonAnywhere account at https://www.pythonanywhere.com/

## Step 2: Upload Your Application

### Option 1: Git Clone Method (Recommended)
1. Click on "Bash Console" in the PythonAnywhere dashboard
2. Clone your Git repository:
   ```bash
   git clone https://github.com/yourusername/yourrepo.git
   ```

### Option 2: Manual Upload
1. Download your code as a zip file
2. In PythonAnywhere, go to Files tab
3. Click "Upload a file" and select your zip file
4. Unzip the file in the Bash console:
   ```bash
   unzip yourfile.zip -d COTC/Server
   ```

## Step 3: Set Up a Virtual Environment

In the PythonAnywhere Bash console:

```bash
cd ~/COTC/Server
python -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
```

## Step 4: Configure the Web App

1. Go to the Web tab in your PythonAnywhere dashboard
2. Click "Add a new web app"
3. Choose "Manual configuration" (not Flask)
4. Select Python version (same as your local environment, Python 3.8+ recommended)

## Step 5: Configure WSGI File

1. In the Web tab, click on the WSGI file link
2. Replace the contents with:

```python
import sys
import os

# Add your project directory to the Python path
path = '/home/YOUR_PYTHONANYWHERE_USERNAME/COTC/Server'
if path not in sys.path:
    sys.path.append(path)

# Import your Flask application
from server import flask_app as application
```

3. Save the file

## Step 6: Configure Static Files

1. In the Web tab, go to "Static Files"
2. Add a mapping:
   - URL: /static/
   - Directory: /home/YOUR_PYTHONANYWHERE_USERNAME/COTC/Server/dashboard/assets

## Step 7: Update the Database Path

1. Open the `config/config.json` file in your PythonAnywhere dashboard
2. Update the database path to an absolute path:
   ```json
   "database_path": "/home/YOUR_PYTHONANYWHERE_USERNAME/COTC/Server/system_monitoring.db"
   ```

## Step 8: Reload and Test Your Web App

1. Click the "Reload" button in the Web tab
2. Visit your application at YOUR_PYTHONANYWHERE_USERNAME.pythonanywhere.com

## Troubleshooting

### Check the Error Logs
If your application doesn't work, check:
1. Error logs in the Web tab
2. The "General" log files for your account

### Common Issues
- **Import errors**: Make sure all dependencies are installed in your virtual environment
- **File path errors**: Ensure all file paths use `os.path.join()` rather than direct concatenation
- **Permission issues**: Make sure your database file has the correct permissions:
  ```bash
  chmod 666 /home/YOUR_PYTHONANYWHERE_USERNAME/COTC/Server/system_monitoring.db
  ```
- **Port binding errors**: Remove any code that tries to set a specific port (PythonAnywhere manages this)

### Database Initialization
If your database needs initial setup, you may need to run a setup script:
```bash
cd ~/COTC/Server
source venv/bin/activate
python -c "from database.schema import initialize_db; initialize_db('system_monitoring.db')"
``` 