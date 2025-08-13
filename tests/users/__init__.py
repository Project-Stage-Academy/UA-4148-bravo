import unittest

def load_tests(loader, tests, pattern):
    return loader.discover(start_dir=__name__, pattern='test_*.py')