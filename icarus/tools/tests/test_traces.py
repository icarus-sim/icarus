import unittest

import random

import numpy as np

import icarus.tools as traces
from icarus.tools import TruncatedZipfDist
from icarus.util import can_import

class TestZipfFit(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        pass

    @classmethod
    def tearDownClass(cls):
        pass

    @unittest.skipIf(not can_import("from scipy.optimize import minimize_scalar"),
                     "Scipy not installed or version < 0.12")
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

    @unittest.skipIf(not can_import("from scipy.optimize import minimize_scalar"),
                     "Scipy not installed or version < 0.12")
    def test_expected_fit_not_sorted(self):
        """Test that the Zipf fit function correctly estimates the alpha
        parameter of a known Zipf distribution"""
        alpha_tolerance = 0.02              # Tolerated alpha estimation error
        p_min = 0.99                        # Min p
        n = 1000                            # Number of Zipf distribution items
        alpha = np.arange(0.2, 5.0, 0.1)    # Tested range of Zipf's alpha
        for a in alpha:
            pdf = TruncatedZipfDist(a, n).pdf
            np.random.shuffle(pdf)
            est_a, p = traces.zipf_fit(pdf, need_sorting=True)
            self.assertLessEqual(np.abs(a - est_a), alpha_tolerance)
            self.assertGreaterEqual(p, p_min)

    @unittest.skipIf(not can_import("from scipy.optimize import minimize_scalar"),
                     "Scipy not installed or version < 0.12")
    def test_no_fit(self):
        """Test that the Zipf fit function correctly identifies a non-Zipfian
        distribution"""
        p_max = 0.02
        freqs = np.asarray([random.randint(0, 20) for _ in range(100)])
        _, p = traces.zipf_fit(freqs)
        self.assertLessEqual(p, p_max)


