import unittest
import collections

import numpy as np

import icarus.tools as stats


class TestMeansConfidenceInterval(unittest.TestCase):

    def test_all_equal(self):
        mean, err = stats.means_confidence_interval([1, 1, 1, 1, 1], 0.95)
        self.assertEquals(1, mean)
        self.assertEquals(0, err)


class TestDiscreteDist(unittest.TestCase):

    def test_pdf_incorrect_sum(self):
        self.assertRaises(ValueError, stats.DiscreteDist, np.array([0.2, 0.3]))

    def test_pdf_sum(self):
        pdf_1 = np.array([0.4, 0.6])
        pdf_2 = stats.DiscreteDist(pdf_1).pdf
        self.assertTrue(all(pdf_1[i] == pdf_2[i] for i in range(len(pdf_1))))

class TestTruncatedZipfDist(unittest.TestCase):

    def test_pdf_sum(self):
        p = stats.TruncatedZipfDist(alpha=0.6, n=1000).pdf
        self.assertAlmostEqual(np.sum(p), 1.0)


class TestCdf(unittest.TestCase):

    def test_cdf_known_input(self):
        data = [-25, -25, 0.5, 1.1, 1.1, 1.1, 1.4, 1.4, 1.4, 1.4]
        # CDF(-25) = 0.2
        # CDF(0.5) = 0.3
        # CDF(1.1) = 0.6
        # CDF(1.5) = 1.0
        x, cdf = stats.cdf(data)
        exp_x = [-25, 0.5, 1.1, 1.4]
        exp_cdf = [0.2, 0.3, 0.6, 1.0]
        self.assertEqual(len(x), len(exp_x))
        self.assertEqual(len(cdf), len(exp_cdf))
        for i in range(len(exp_x)):
            self.assertAlmostEqual(x[i], exp_x[i])
            self.assertAlmostEqual(cdf[i], exp_cdf[i])

    def test_cdf_deque_input(self):
        data = collections.deque(range(2000))
        x, cdf = stats.cdf(data)
        self.assertEqual(len(x), 2000)
        self.assertAlmostEqual(cdf[-1], 1.0)

    def test_cdf_list_input(self):
        data = list(range(2000))
        x, cdf = stats.cdf(data)
        self.assertEqual(len(x), 2000)
        self.assertAlmostEqual(cdf[-1], 1.0)

    def test_cdf_array_input(self):
        data = np.array(list(range(2000)))
        x, cdf = stats.cdf(data)
        self.assertEqual(len(x), 2000)
        self.assertAlmostEqual(cdf[-1], 1.0)

    def test_cdf_all_zeros(self):
        data = np.zeros(200)
        x, cdf = stats.cdf(data)
        exp_x = [0]
        exp_cdf = [1.0]
        self.assertEqual(len(x), len(exp_x))
        self.assertEqual(len(cdf), len(exp_cdf))
        for i in range(len(exp_x)):
            self.assertAlmostEqual(x[i], exp_x[i])
            self.assertAlmostEqual(cdf[i], exp_cdf[i])

