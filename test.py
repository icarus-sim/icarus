#!/usr/bin/env python
"""Run unit tests
"""
from os import path, getcwd

__all__ = ['run']

def run(verbosity=1):
    """Run tests.

    Parameters
    ----------
    verbosity: integer, optional
      Level of detail in test reports.  Higher numbers provide more detail.  

    """
    try:
        import nose
    except ImportError:
        raise ImportError("The nose package is needed to run the tests.")
    # get folder of Python source files
    src_dir = path.join(path.dirname(__file__), path.pardir)

    # stop if running from source directory
    if getcwd() == path.abspath(path.join(src_dir, path.pardir)):
        raise RuntimeError("Can't run tests from source directory.\n"
                           "Run 'nosetests' from the command line.")
    # Run tests
    nose.run()
    
if __name__=="__main__":
    run()

