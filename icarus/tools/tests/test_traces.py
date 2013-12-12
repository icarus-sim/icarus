import sys
if sys.version_info[:2] >= (2, 7):
    import unittest
else:
    try:
        import unittest2 as unittest
    except ImportError:
        raise ImportError("The unittest2 package is needed to run the tests.") 
del sys
import random

import numpy as np

import icarus.tools as traces
from icarus.tools import TruncatedZipfDist

class TestZipfFit(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        pass
        
    @classmethod
    def tearDownClass(cls):
        pass
    
    def test_expected_fit(self):
        """Test that the Zipf fit function correctly estimates the alpha
        parameter of a known Zipf distribution"""
        alpha_tolerance = 0.02              # Tolerated alpha estimation error
        p_min = 0.99                        # Min p
        n = 1000                            # Number of Zipf distribution items
        alpha = np.arange(0.2, 5.0, 0.1)    # Tested range of Zipf's alpha
        for a in alpha:
            z = TruncatedZipfDist(a, n)
            est_a, p = traces.zipf_fit(z.pdf)
            self.assertLessEqual(np.abs(a - est_a), alpha_tolerance)
            self.assertGreaterEqual(p, p_min)

    def test_no_fit(self):
        """Test that the Zipf fit function correctly identifies a non-Zipfian
        distribution"""
        p_max = 0.02
        freqs = np.asarray([random.randint(0, 20) for _ in range(100)])
        _, p = traces.zipf_fit(freqs)
        self.assertLessEqual(p, p_max)


