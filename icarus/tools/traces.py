"""Functions for importing and analyzing traffic traces  
"""
from __future__ import division

import math
import collections

import numpy as np
from scipy.optimize import minimize_scalar
from scipy.stats import chisquare

from icarus.tools import TruncatedZipfDist


__all__ = [
       'frequencies',
       'zipf_fit',
       'parse_squid',
       'parse_wikibench'
           ]


def frequencies(data):
    """Extract frequencies from traces. Returns array of sorted frequencies
    
    Parameters
    ----------
    data : array-like
        An array of generic data (i.e. URLs of web pages)
    
    Returns
    -------
    frequencies : array of int
        The frequencies of the data sorted in descending order
        
    Notes
    -----
    This function does not return the mapping between data elements and their
    frequencies, it only returns frequencies.
    This function can be used to get frequencies to pass to the *zipf_fit*
    function given a set of data, e.g. content request traces.
    """
    return np.asarray(sorted(collections.Counter(data).values(), reverse=True))


def zipf_fit(obs_freqs):
    """Returns the value of the Zipf's distribution alpha parameter that best
    fits the data provided and the p-value of the fit test.
    
    Parameters
    ----------
    obs_freqs : array
        The array of observed frequencies
    
    Returns
    -------
    alpha : float
        The alpha parameter of the best Zipf fit
    p : float
        The p-value of the test
    
    Notes
    -----
    This function uses the method described in
    http://stats.stackexchange.com/questions/6780/how-to-calculate-zipfs-law-coefficient-from-a-set-of-top-frequencies
    """
    obs_freqs = np.asarray(obs_freqs)
    n = len(obs_freqs)
    def log_likelihood(alpha):
        return np.sum(obs_freqs * (alpha * np.log(np.arange(1.0, n+1)) + \
                       math.log(sum(1.0/np.arange(1.0, n+1)**alpha))))
    # Find optimal alpha
    alpha = minimize_scalar(log_likelihood)['x']
    # Calculate goodness of fit
    if alpha <= 0:
        # Silently report a zero probability of a fit
        return alpha, 0
    exp_freqs = np.sum(obs_freqs) * TruncatedZipfDist(alpha, n).pdf
    p = chisquare(obs_freqs, exp_freqs)[1]
    return alpha, p
    

def parse_wikibench(path):
    """Parses traces from the Wikibench dataset
    
    Parameters
    ----------
    path : str
        The path to the trace file to parse
    
    Returns
    -------
    trace : iterator of dict
        An iterator whereby each element is dictionary expressing all
        attributes of an entry of the trace
    """
    with open(path) as f:
        for line in f:
            entry = line.split(" ")
            yield dict(counter=int(entry[0]), timestamp=entry[1],
                           url=entry[2])
    raise StopIteration()


def parse_squid(path):
    """Parses traces from a Squid log file.
    
    Squid is one of the most common open-source Web proxies. Traces from the
    IRCache dataset are in this format.
    
    Parameters
    ----------
    path : str
        The path to the trace file to parse
    
    Returns
    -------
    trace : iterator of dict
        An iterator whereby each element is dictionary expressing all
        attributes of an entry of the trace
    
    Notes
    -----
    Documentation describing the Squid log format is available here:
    http://wiki.squid-cache.org/Features/LogFormat
    """
    with open(path) as f:
        for line in f:
            entry = line.split(" ")
            time = entry[0]
            duration = int(entry[1])
            client_addr = entry[2]
            log_tag, http_code = entry[3].split("/")
            http_code = int(http_code)
            bytes_len = int(entry[4])
            req_method = entry[5]
            url = entry[6]
            client_ident = entry[7] if entry[7] != '-' else None
            hierarchy_data, hostname = entry[8].split("/")
            content_type = entry[9] if entry[9] != '-' else None
            yield dict(time=time,
                       duration=duration,
                       client_addr=client_addr,
                       log_tag=log_tag,
                       http_code=http_code,
                       bytes_len=bytes_len,
                       req_method=req_method, url=url,
                       client_ident=client_ident,
                       hierarchy_data=hierarchy_data,
                       hostname=hostname,
                       content_type=content_type)
    raise StopIteration()
