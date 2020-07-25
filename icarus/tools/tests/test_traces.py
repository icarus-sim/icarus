import random

import numpy as np
import pytest

import icarus.tools as traces
from icarus.tools import TruncatedZipfDist

try:
    from scipy.optimize import minimize_scalar
except ImportError:
    minimize_scalar = None


class TestZipfFit(object):

    @pytest.mark.skipif(not minimize_scalar, reason="scipy not installed")
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
            assert np.abs(a - est_a) <= alpha_tolerance
            assert p >= p_min

    @pytest.mark.skipif(not minimize_scalar, reason="scipy not installed")
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
            assert np.abs(a - est_a) <= alpha_tolerance
            assert p >= p_min

    @pytest.mark.skipif(not minimize_scalar, reason="scipy not installed")
    def test_no_fit(self):
        """Test that the Zipf fit function correctly identifies a non-Zipfian
        distribution"""
        p_max = 0.02
        freqs = np.asarray([random.randint(0, 20) for _ in range(100)])
        _, p = traces.zipf_fit(freqs)
        assert p <= p_max
