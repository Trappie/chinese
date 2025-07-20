# PythonAnywhere Deployment Guide

This guide will help you deploy the Chinese Character Practice Generator to PythonAnywhere.

## Prerequisites

1. Create a free account at [PythonAnywhere](https://www.pythonanywhere.com/)
2. Have your project files ready (this repository)

## Deployment Steps

### 1. Upload Your Code

**Option A: Upload via PythonAnywhere Files Tab**
1. Go to the **Files** tab in your PythonAnywhere dashboard
2. Create a new directory: `chinese`
3. Upload all project files to `/home/yourusername/chinese/`

**Option B: Clone from Git (Recommended)**
1. Go to the **Consoles** tab in PythonAnywhere
2. Open a **Bash** console
3. Clone your repository:
   ```bash
   git clone <your-repo-url> chinese
   cd chinese
   ```

### 2. Install Dependencies

In the Bash console:
```bash
cd chinese
pip3.10 install --user -r requirements.txt
```

### 3. Create a Web App

1. Go to the **Web** tab in your PythonAnywhere dashboard
2. Click **"Add a new web app"**
3. Choose **"Manual configuration"**
4. Select **Python 3.10**
5. Click **Next**

### 4. Configure WSGI File

1. In the **Web** tab, find the **"Code"** section
2. Click on the **WSGI configuration file** link (usually `/var/www/yourusername_pythonanywhere_com_wsgi.py`)
3. Replace the entire contents with:

```python
import sys
import os

# Add your project directory to the sys.path
project_home = '/home/yourusername/chinese'  # Replace 'yourusername' with your actual username
if project_home not in sys.path:
    sys.path = [project_home] + sys.path

# Import your Flask application
from app import app as application

if __name__ == "__main__":
    application.run()
```

4. **Important**: Replace `yourusername` with your actual PythonAnywhere username
5. Save the file

### 5. Configure Static Files (Optional)

If you add CSS/JS files later:
1. In the **Web** tab, find the **"Static files"** section
2. Add a mapping:
   - **URL**: `/static/`
   - **Directory**: `/home/yourusername/chinese/static/`

### 6. Reload Your Web App

1. In the **Web** tab, click the big green **"Reload"** button
2. Wait for the reload to complete

### 7. Test Your Application

1. Visit your app at: `https://yourusername.pythonanywhere.com`
2. Test the functionality:
   - Enter new characters (use characters after index 50)
   - Enter a review starting character (before the new characters)
   - Generate a PDF

## Example Test Data

For testing, use these characters from the 500-character database:

- **New characters**: `女父母` (indices 52, 53, 54)
- **Review start**: `好` (index 30)

## Troubleshooting

### Common Issues

1. **Import Errors**:
   - Check that the project path in WSGI file is correct
   - Ensure all dependencies are installed with `--user` flag

2. **Character Encoding Issues**:
   - Make sure your files are saved with UTF-8 encoding
   - PythonAnywhere supports Unicode/Chinese characters

3. **PDF Generation Issues**:
   - ReportLab should work on PythonAnywhere
   - Check the error logs in the **Web** tab

### Viewing Error Logs

1. Go to the **Web** tab
2. Click on **"Log files"**
3. Check the **error log** for any Python errors
4. Check the **server log** for HTTP errors

### Testing Locally First

Before deploying, test locally:
```bash
python app.py
# Visit http://localhost:5000
```

## Free Account Limitations

PythonAnywhere free accounts have some limitations:
- One web app at `yourusername.pythonanywhere.com`
- Limited CPU seconds per day
- Restricted outbound internet access
- No custom domains

For production use, consider upgrading to a paid plan.

## File Structure on PythonAnywhere

```
/home/yourusername/chinese/
├── app.py
├── data.txt
├── requirements.txt
├── wsgi.py
├── test_character_selection.py
└── templates/
    └── index.html
```

## Updates and Maintenance

To update your app:
1. Upload new files or pull from git
2. Reload the web app in the **Web** tab
3. No need to restart the server

## Support

- PythonAnywhere Help: [help.pythonanywhere.com](https://help.pythonanywhere.com/)
- PythonAnywhere Forums: [www.pythonanywhere.com/forums/](https://www.pythonanywhere.com/forums/)

Your Chinese Character Practice Generator should now be live and accessible to anyone with the URL!