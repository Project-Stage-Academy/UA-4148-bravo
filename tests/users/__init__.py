<<<<<<< HEAD
import unittest

def load_tests(loader, tests, pattern):
    return loader.discover(start_dir=__name__, pattern='test_*.py')
=======
import os
import unittest

def load_tests(loader, tests, pattern):
    this_dir = os.path.dirname(os.path.abspath(__file__))
    return loader.discover(start_dir=this_dir, pattern='test_*.py')
>>>>>>> 29354e87ea4e1fe07cbab918b932b5ee970e5775
