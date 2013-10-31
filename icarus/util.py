"""Utility functions"""
from random import random
from numpy import searchsorted, zeros, cumsum

class ZipfDistribution(object):
    """
    Truncated Zipf distribution (finite number of items) supporting alpha < 1
    """

    def __init__(self, alpha=1.0, N=1000):
        """
        Constructor
        """
        pdf = zeros(N) # array that will contain the probability that content i + 1 is picked
        norm_factor = 0
        for i in range(N):
            p_i = 1.0/((i+1)**alpha)
            pdf[i] = p_i
            norm_factor += p_i
        pdf /= norm_factor
        cdf = cumsum(pdf)
        cdf[N-1] = 1.0 # to avoid rounding errors
        self.pdf = pdf
        self.cdf = cdf

    def get_pdf(self):
        """
        Return PDF
        
        Return
        ------
        pdf : array
            Array representing pdf 
        """
        return self.pdf
    
    def get_cdf(self):
        """
        Return CDF
        
        Return
        ------
        cdf : array
            Array representing cdf 
        """
        return self.cdf
    
    def rand_val(self):
        """
        Get rand value from the distribution
        """
        rand_val = random()
        # This operation performs binary search over the CDF to return the
        # random value. Worst case time complexity is O(log2(n))
        return int(searchsorted(self.cdf, rand_val) + 1)
