"""
Student Information System - Local Development Entry Point
Run this file to start the server locally:
    python app.py
    OR
    flask run
"""

import sys
import os

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Import the Flask app from api/app.py
from api.app import app

if __name__ == '__main__':
    print("=" * 55)
    print("  Student Information System - Local Development")
    print("=" * 55)
    print()
    print("  Demo Admin  : ID=admin       | Pass=123@Admin")
    print("  Demo Student: Reg=DEMO001    | Pass=demo001")
    print()
    print("  Open: http://localhost:5000")
    print("=" * 55)
    app.run(debug=True, host='0.0.0.0', port=5000)
