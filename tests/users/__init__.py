import os
import unittest

def load_tests(loader, tests, pattern):
    this_dir = os.path.dirname(os.path.abspath(__file__))
    return loader.discover(start_dir=this_dir, pattern='test_*.py')
