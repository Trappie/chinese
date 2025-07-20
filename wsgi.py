#!/usr/bin/env python3

"""
WSGI configuration for PythonAnywhere deployment.

This module contains the WSGI application used by PythonAnywhere's
web servers to serve your application.
"""

import sys
import os

# Add your project directory to the sys.path
project_home = '/home/yourusername/chinese'  # Update this path
if project_home not in sys.path:
    sys.path = [project_home] + sys.path

# Import your Flask application
from app import app as application

if __name__ == "__main__":
    application.run()