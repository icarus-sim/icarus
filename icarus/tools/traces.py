"""Functions for importing and analyzing traffic traces"""
from __future__ import division

import collections
import math
import time
import types

import dateutil

from icarus.tools import TruncatedZipfDist

import numpy as np

from scipy.stats import chisquare


__all__ = [
       'frequencies',
       'one_timers',
       'trace_stats',
       'zipf_fit',
       'parse_url_list',
       'parse_wikibench',
       'parse_squid',
       'parse_youtube_umass',
       'parse_common_log_format'
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


def one_timers(data):
    """Return fraction of contents requested only once (i.e., one-timers)

    Parameters
    ----------
    data : array-like
        An array of generic data (i.e. URLs of web pages)

    Returns
    -------
    one_timers : float
        Fraction of content objects requested only once.
    """
    n_items = 0
    n_onetimers = 0
    counter = collections.Counter(data)
    for i in counter.itervalues():
        n_items += 1
        if i == 1:
            n_onetimers += 1
    return n_onetimers / n_items


def trace_stats(data):
    """Print full stats of a trace

    Parameters
    ----------
    data : array-like
        An array of generic data (i.e. URLs of web pages)

    Return
    ------
    stats : dict
        Metrics of the trace
    """
    if isinstance(data, types.GeneratorType):
        data = collections.deque(data)
    freqs = frequencies(data)
    alpha, p = zipf_fit(freqs)
    n_reqs = len(data)
    n_contents = len(freqs)
    n_onetimers = len(freqs[freqs == 1])
    return dict(n_contents=n_contents,
                n_reqs=n_reqs,
                n_onetimers=n_onetimers,
                alpha=alpha,
                p=p,
                onetimers_contents_ratio=n_onetimers / n_contents,
                onetimers_reqs_ratio=n_onetimers / n_reqs,
                mean_reqs_per_content=n_reqs / n_contents
                )


def zipf_fit(obs_freqs, need_sorting=False):
    """Returns the value of the Zipf's distribution alpha parameter that best
    fits the data provided and the p-value of the fit test.

    Parameters
    ----------
    obs_freqs : array
        The array of observed frequencies sorted in descending order
    need_sorting : bool, optional
        If True, indicates that obs_freqs is not sorted and this function will
        sort it. If False, assume that the array is already sorted

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
    try:
        from scipy.optimize import minimize_scalar
    except ImportError:
        raise ImportError("Cannot import scipy.optimize minimize_scalar. "
                          "You either don't have scipy install or you have a "
                          "version too old (required 0.12 onwards)")
    obs_freqs = np.asarray(obs_freqs)
    if need_sorting:
        # Sort in descending order
        obs_freqs = -np.sort(-obs_freqs)
    n = len(obs_freqs)

    def log_likelihood(alpha):
        return np.sum(obs_freqs * (alpha * np.log(np.arange(1.0, n + 1)) +
                      math.log(sum(1.0 / np.arange(1.0, n + 1) ** alpha))))

    # Find optimal alpha
    alpha = minimize_scalar(log_likelihood)['x']
    # Calculate goodness of fit
    if alpha <= 0:
        # Silently report a zero probability of a fit
        return alpha, 0
    exp_freqs = np.sum(obs_freqs) * TruncatedZipfDist(alpha, n).pdf
    p = chisquare(obs_freqs, exp_freqs)[1]
    return alpha, p


def parse_url_list(path):
    """Parse traces from a text file where each line contains a URL requested
    without timestamp or counters

    Parameters
    ----------
    path : str
        The path to the trace file to parse

    Returns
    -------
    trace : iterator of strings
        An iterator whereby each element is dictionary expressing all
        attributes of an entry of the trace
    """
    with open(path) as f:
        for line in f:
            yield line
    return


def parse_wikibench(path):
    """Parses traces from the Wikibench dataset

    Parameters
    ----------
    path : str
        The path to the trace file to parse

    Returns
    -------
    trace : iterator of dicts
        An iterator whereby each element is dictionary expressing all
        attributes of an entry of the trace
    """
    with open(path) as f:
        for line in f:
            entry = line.split(" ")
            yield dict(
                counter=int(entry[0]),
                timestamp=entry[1],
                url=entry[2]
                      )
    return


def parse_squid(path):
    """Parses traces from a Squid log file.
    Parse a Squid log file.

    Squid is an HTTP reverse proxy. Its logs contains traces of all HTTP
    requests served and can be used for trace-driven simulations based on
    realistic HTTP workloads.
    Traces from the IRCache dataset are in this format.

    Parameters
    ----------
    path : str
        The path to the trace file to parse

    Returns
    -------
    trace : iterator of dicts
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
            timestamp = entry[0]
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
            yield dict(
                time=timestamp,
                duration=duration,
                client_addr=client_addr,
                log_tag=log_tag,
                http_code=http_code,
                bytes_len=bytes_len,
                req_method=req_method, url=url,
                client_ident=client_ident,
                hierarchy_data=hierarchy_data,
                hostname=hostname,
                content_type=content_type
                      )
    return


def parse_youtube_umass(path):
    """Parse YouTube collected at UMass campus network [1]_.

    These data were collected at UMass campus network over a a measurement
    period between June 2007 and March 2008.

    This function parses the request traces, named youtube.parsed.X.Y.dat.
    Each entry of the trace provides the following information elements:
     * Timestamp
     * YouTube server IP (anonymized)
     * Client IP (anonymized)
     * Request
     * Video ID
     * Content server IP

    Traces are available at http://traces.cs.umass.edu/index.php/Network/Network

    Parameters
    ----------
    path : str
        The path to the trace file to parse

    Returns
    -------
    trace : iterator of dicts
        An iterator whereby each element is dictionary expressing all
        attributes of an entry of the trace

    References
    ----------
    ..[1] Michael Zink, Kyoungwon Suh, Yu Gu and Jim Kurose,
          Watch Global Cache Local: YouTube Network Traces at a Campus Network -
          Measurements and Implications, in Proc. of IEEE MMCN'08
    """
    with open(path) as f:
        for line in f:
            entry = line.split(" ")
            timestamp = entry[0]
            youtube_server_addr = int(entry[1])
            client_addr = entry[2]
            request = entry[3]
            video_id = entry[4]
            content_server_addr = entry[5]
            yield dict(
                time=timestamp,
                youtube_server_addr=youtube_server_addr,
                client_addr=client_addr,
                request=request,
                video_id=video_id,
                content_server_addr=content_server_addr,
                      )
    return


def parse_common_log_format(path):
    """Parse files saved in the Common Log Format (CLF)

    Parameters
    ----------
    path : str
        The path to the Common Log Format file to parse

    Returns
    -------
    events : iterator
        iterator over the events parsed from the file

    Notes
    -----
    Common Log Format specifications:
    http://www.w3.org/Daemon/User/Config/Logging.html#common-logfile-format

    """
    with open(path) as f:
        for line in f:
            entry = line.split(" ")
            client_addr = entry[0]
            user_ident = entry[1]
            auth_user = entry[2]
            date = entry[3][1:-1]
            request = entry[4]
            status = int(entry[5])
            n_bytes = int(entry[6])
            # Convert timestamp into float
            t = time.mktime(dateutil.parser.parse(date.replace(":", " ", 0)).timetuple())
            event = dict(
                client_addr=client_addr,
                user_ident=user_ident,
                auth_user=auth_user,
                request=request,
                status=status,
                bytes=n_bytes
                        )
            yield t, event
    return
