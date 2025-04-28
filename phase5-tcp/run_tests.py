import unittest
import sys
import os

# Add the src folder to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

if __name__ == "__main__":
    # Discover and run all tests in the 'tests' folder
    test_loader = unittest.TestLoader()
    test_suite = test_loader.discover(start_dir=os.path.join(os.path.dirname(__file__), 'tests'), pattern="test_*.py")
    
    # Run the test suite
    test_runner = unittest.TextTestRunner(verbosity=2)
    test_runner.run(test_suite)