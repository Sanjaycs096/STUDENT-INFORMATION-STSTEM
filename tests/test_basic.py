import unittest
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

class BasicAppTest(unittest.TestCase):
    def test_imports(self):
        # Simply testing that the app can be imported without syntax errors
        try:
            from api.app import app
            self.assertIsNotNone(app)
        except Exception as e:
            self.fail(f"App import failed: {e}")

if __name__ == '__main__':
    unittest.main()
