"""Provides statistical utilities functions used by the simulator
"""
from __future__ import division

import math
import random
import collections

import numpy as np
import scipy.stats as ss


__all__ = [
       'DiscreteDist',
       'TruncatedZipfDist',
       'means_confidence_interval',
       'proportions_confidence_interval',
       'cdf',
       'pdf',
           ]


class DiscreteDist(object):
    """Implements a discrete distribution with finite population.

    The support must be a finite discrete set of contiguous integers
    {1, ..., N}. This definition of discrete distribution.
    """

    def __init__(self, pdf, seed=None):
        """
        Constructor

        Parameters
        ----------
        pdf : array-like
            The probability density function
        seed : any hashable type (optional)
            The seed to be used for random number generation
        """
        if np.abs(sum(pdf) - 1.0) > 0.001:
            raise ValueError('The sum of pdf values must be equal to 1')
        random.seed(seed)
        self._pdf = np.asarray(pdf)
        self._cdf = np.cumsum(self._pdf)
        # set last element of the CDF to 1.0 to avoid rounding errors
        self._cdf[-1] = 1.0

    def __len__(self):
        """Return the cardinality of the support

        Returns
        -------
        len : int
            The cardinality of the support
        """
        return len(self._pdf)

    @property
    def pdf(self):
        """
        Return the Probability Density Function (PDF)

        Returns
        -------
        pdf : Numpy array
            Array representing the probability density function of the
            distribution
        """
        return self._pdf

    @property
    def cdf(self):
        """
        Return the Cumulative Density Function (CDF)

        Returns
        -------
        cdf : Numpy array
            Array representing cdf
        """
        return self._cdf

    def rv(self):
        """Get rand value from the distribution
        """
        rv = random.random()
        # This operation performs binary search over the CDF to return the
        # random value. Worst case time complexity is O(log2(n))
        return int(np.searchsorted(self._cdf, rv) + 1)


class TruncatedZipfDist(DiscreteDist):
    """Implements a truncated Zipf distribution, i.e. a Zipf distribution with
    a finite population, which can hence take values of alpha > 0.
    """

    def __init__(self, alpha=1.0, n=1000, seed=None):
        """Constructor

        Parameters
        ----------
        alpha : float
            The value of the alpha parameter (it must be positive)
        n : int
            The size of population
        seed : any hashable type, optional
            The seed to be used for random number generation
        """
        # Validate parameters
        if alpha <= 0:
            raise ValueError('alpha must be positive')
        if n < 0:
            raise ValueError('n must be positive')
        # This is the PDF i. e. the array that  contains the probability that
        # content i + 1 is picked
        pdf = np.arange(1.0, n + 1.0) ** -alpha
        pdf /= np.sum(pdf)
        self._alpha = alpha
        super(TruncatedZipfDist, self).__init__(pdf, seed)

    @property
    def alpha(self):
        return self._alpha


def means_confidence_interval(data, confidence=0.95):
    """Computes the confidence interval for a given set of means.

    Parameters
    ----------
    data : array-like
        The set of samples whose confidence interval is calculated
    confidence : float, optional
        The confidence level. It must be a value in the interval (0, 1)

    Returns
    -------
    mean : float
        The mean of the sample
    err : float
        The standard error of the sample

    References
    ----------
    [1] N. Matloff, From Algorithms to Z-Scores: Probabilistic and Statistical
        Modeling in Computer Science.
        Available: http://heather.cs.ucdavis.edu/probstatbook
    """
    if confidence <= 0 or confidence >= 1:
        raise ValueError('The confidence parameter must be greater than 0 and '
                         'smaller than 1')
    n = len(data)
    w = np.mean(data)
    s = np.std(data)
    err = ss.norm.interval(confidence)[1]
    return w, err * s / math.sqrt(n)


def proportions_confidence_interval(data, confidence):
    """Computes the confidence interval of a proportion.

    Parameters
    ----------
    data : array-like of bool
        The sample of data whose proportion of True values needs to be
        estimated
    confidence : float, optional
        The confidence level. It must be a value in the interval (0, 1)

    References
    ----------
    [1] N. Matloff, From Algorithms to Z-Scores: Probabilistic and Statistical
        Modeling in Computer Science.
        Available: http://heather.cs.ucdavis.edu/probstatbook
    """
    if confidence <= 0 or confidence >= 1:
        raise ValueError('The confidence parameter must be greater than 0 and '
                         'smaller than 1')
    n = float(len(data))
    m = len((i for i in data if i is True))
    p = m / n
    err = ss.norm.interval(confidence)[1]
    return p, err * math.sqrt(p * (1 - p) / n)


def cdf(data):
    """Return the empirical CDF of a set of 1D data

    Parameters
    ----------
    data : array-like
        Array of data

    Returns
    -------
    x : array
        All occurrences of data sorted
    cdf : array
        The CDF of data.
        More specifically cdf[i] is the probability that x < x[i]
    """
    if len(data) < 1:
        raise TypeError("data must have at least one element")
    freq_dict = collections.Counter(data)
    sorted_unique_data = np.sort(list(freq_dict.keys()))
    freqs = np.zeros(len(sorted_unique_data))
    for i in range(len(freqs)):
        freqs[i] = freq_dict[sorted_unique_data[i]]
#    freqs = np.array([freq_dict[sorted_unique_data[i]]
#                       for i in range(len(sorted_unique_data))])
    cdf = np.array(np.cumsum(freqs))
    norm = cdf[-1]
    cdf = cdf / norm  # normalize
    cdf[-1] = 1.0  # Prevent rounding errors
    return sorted_unique_data, cdf


def pdf(data, n_bins):
    """Return the empirical PDF of a set of 1D data

    Parameters
    ----------
    data : array-like
        Array of data
    n_bins : int
        The number of bins

    Returns
    x : array
        The center point of all bins
    pdf : array
        The PDF of data.
    """
    # Validate input parameters
    if len(data) < 1:
        raise TypeError("data must have at least one element")
    if not isinstance(n_bins, int):
        raise TypeError("intervals parameter must be an integer")
    if n_bins < 1:
        raise TypeError("Intervals must be >= 1")
    # Sort data and divide it in sections
    data = np.sort(data)
    data_min = data[0]
    data_max = data[-1]
    boundaries = np.linspace(data_min, data_max, n_bins + 1)
    x = boundaries[:-1] + ((boundaries[1] - boundaries[0]) / 2.0)
    # Count number of samples in each section
    pdf = np.zeros(n_bins)
    section = 0
    for entry in data:
        if entry <= boundaries[section + 1]:
            pdf[section] += 1
        else:
            section += 1
            while entry > boundaries[section + 1]:
                section += 1
            pdf[section] += 1
    # Normalize pdf
    pdf = (pdf * n_bins) / (np.sum(pdf) * (data_max - data_min))
    return x, pdf
