#!/usr/bin/env python
"""Run unit tests"""
from os import path, getcwd

def main():
    """Run all tests"""
    try:
        import pytest
    except ImportError:
        raise ImportError("The pytest package is needed to run the tests.")

    # get folder of Python source files
    src_dir = path.join(path.dirname(__file__), path.pardir)

    # stop if running from source directory
    if getcwd() == path.abspath(path.join(src_dir, path.pardir)):
        raise RuntimeError("Can't run tests from source directory.\n"
                           "Run 'py.test' from the command line.")
    # Run tests
    pytest.main(['icarus'])

if __name__ == "__main__":
    main()

