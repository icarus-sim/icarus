"""Functions for modelling and evaluating the performance of cache
replacement policies.
"""
from __future__ import division

import math

from icarus.tools import DiscreteDist, TruncatedZipfDist

import numpy as np

from scipy.optimize import fsolve
import networkx as nx

from icarus.util import path_links
from icarus.tools import TruncatedZipfDist, DiscreteDist


__all__ = [
       'fagin_characteristic_time',
       'fagin_per_content_cache_hit_ratio',
       'fagin_cache_hit_ratio',
       'che_characteristic_time',
       'che_per_content_cache_hit_ratio',
       'che_cache_hit_ratio',
       'che_characteristic_time_simplified',
       'che_per_content_cache_hit_ratio_simplified',
       'che_cache_hit_ratio_simplified',
       'che_characteristic_time_generalized',
       'che_per_content_cache_hit_ratio_generalized',
       'che_cache_hit_ratio_generalized',
       'laoutaris_characteristic_time',
       'laoutaris_per_content_cache_hit_ratio',
       'laoutaris_cache_hit_ratio',
       'optimal_cache_hit_ratio',
       'numeric_per_content_cache_hit_ratio',
       'numeric_cache_hit_ratio',
       'numeric_cache_hit_ratio_2_layers',
       'trace_driven_cache_hit_ratio',
       'hashrouting_model',
       'hashrouting_model_ring',
       'hashrouting_model_mesh',
          ]


def fagin_characteristic_time(pdf, cache_size):
    """Return the characteristic time of an LRU cache under a given IRM
    workload, as defined by Fagin.

    Parameters
    ----------
    pdf : array-like
        The probability density function of an item being requested
    cache_size : int
        The size of the cache (in number of items)

    Returns
    -------
    r : float
        The characteristic time.
    """
    pdf = np.asarray(pdf)
    def func_r(r):
        return np.sum((1 - pdf)**r) - len(pdf) + cache_size
    return fsolve(func_r, x0=cache_size)[0]


def fagin_per_content_cache_hit_ratio(pdf, cache_size, target=None):
    """Estimate the cache hit ratio of an item or of all items using the Fagin's
    approximation. This version uses a single characteristic time for all
    contents.

    Parameters
    ----------
    pdf : array-like
        The probability density function of an item being requested
    cache_size : int
        The size of the cache (in number of items)
    target : int, optional
        The item index for which cache hit ratio is requested. If not
        specified, the function calculates the cache hit ratio of all the items
        in the population.

    Returns
    -------
    cache_hit_ratio : array of float or float
        If target is None, returns an array with the cache hit ratios of all
        items in the population. If a target is specified, then it returns
        the cache hit ratio of only the specified item.
    """
    items = range(len(pdf)) if target is None else [target]
    r = fagin_characteristic_time(pdf, cache_size)
    hit_ratio = [1 - (1 - pdf[i])**r for i in items]
    return hit_ratio if target is None else hit_ratio[0]


def fagin_cache_hit_ratio(pdf, cache_size):
    """Estimate the overall cache hit ratio of an LRU cache under generic IRM
    demand using the Fagin's approximation. This version uses a single
    characteristic time for all contents.

    Parameters
    ----------
    pdf : array-like
        The probability density function of an item being requested
    cache_size : int
        The size of the cache (in number of items)

    Returns
    -------
    cache_hit_ratio : float
        The overall cache hit ratio
    """
    ch = fagin_per_content_cache_hit_ratio(pdf, cache_size)
    return sum(pdf[i] * ch[i] for i in range(len(pdf)))


def che_characteristic_time(pdf, cache_size, target=None):
    """Return the characteristic time of an item or of all items, as defined by
    Che et al.

    Parameters
    ----------
    pdf : array-like
        The probability density function of an item being requested
    cache_size : int
        The size of the cache (in number of items)
    target : int, optional
        The item index [1,N] for which characteristic time is requested. If not
        specified, the function calculates the characteristic time of all the
        items in the population.

    Returns
    -------
    r : array of float or float
        If target is None, returns an array with the characteristic times of
        all items in the population. If a target is specified, then it returns
        the characteristic time of only the specified item.
    """
    def func_r(r, i):
        return sum(math.exp(-pdf[j] * r) for j in range(len(pdf)) if j != i) \
               - len(pdf) + 1 + cache_size
    items = range(len(pdf)) if target is None else [target - 1]
    r = [fsolve(func_r, x0=cache_size, args=(i)) for i in items]
    return r if target is None else r[0]


def che_per_content_cache_hit_ratio(pdf, cache_size, target=None):
    """Estimate the cache hit ratio of an item or of all items using the Che's
    approximation.

    Parameters
    ----------
    pdf : array-like
        The probability density function of an item being requested
    cache_size : int
        The size of the cache (in number of items)
    target : int, optional
        The item index for which cache hit ratio is requested. If not
        specified, the function calculates the cache hit ratio of all the items
        in the population.

    Returns
    -------
    cache_hit_ratio : array of float or float
        If target is None, returns an array with the cache hit ratios of all
        items in the population. If a target is specified, then it returns
        the cache hit ratio of only the specified item.
    """
    items = range(len(pdf)) if target is None else [target]
    r = che_characteristic_time(pdf, cache_size)
    hit_ratio = [1 - math.exp(-pdf[i] * r[i]) for i in items]
    return hit_ratio if target is None else hit_ratio[0]


def che_cache_hit_ratio(pdf, cache_size):
    """Estimate the overall cache hit ratio of an LRU cache under generic IRM
    demand using the Che's approximation.

    Parameters
    ----------
    pdf : array-like
        The probability density function of an item being requested
    cache_size : int
        The size of the cache (in number of items)

    Returns
    -------
    cache_hit_ratio : float
        The overall cache hit ratio
    """
    ch = che_per_content_cache_hit_ratio(pdf, cache_size)
    return sum(pdf[i] * ch[i] for i in range(len(pdf)))


def che_characteristic_time_simplified(pdf, cache_size):
    """Return the characteristic time of an LRU cache under a given IRM
    workload, as defined by Che et al.
    This function computes one single characteristic time for all contents.
    This further approximation is normally accurate for workloads with
    reduced skewness in their popularity distribution.

    Parameters
    ----------
    pdf : array-like
        The probability density function of an item being requested
    cache_size : int
        The size of the cache (in number of items)

    Returns
    -------
    r : float
        The characteristic time.
    """
    pdf = np.asarray(pdf)
    def func_r(r):
        return np.sum(np.exp(-pdf * r)) - len(pdf) + cache_size
    return fsolve(func_r, x0=cache_size)[0]


def che_per_content_cache_hit_ratio_simplified(pdf, cache_size, target=None):
    """Estimate the cache hit ratio of an item or of all items using the Che's
    approximation. This version uses a single characteristic time for all
    contents.

    Parameters
    ----------
    pdf : array-like
        The probability density function of an item being requested
    cache_size : int
        The size of the cache (in number of items)
    target : int, optional
        The item index for which cache hit ratio is requested. If not
        specified, the function calculates the cache hit ratio of all the items
        in the population.

    Returns
    -------
    cache_hit_ratio : array of float or float
        If target is None, returns an array with the cache hit ratios of all
        items in the population. If a target is specified, then it returns
        the cache hit ratio of only the specified item.
    """
    items = range(len(pdf)) if target is None else [target]
    r = che_characteristic_time_simplified(pdf, cache_size)
    hit_ratio = [1 - math.exp(-pdf[i] * r) for i in items]
    return hit_ratio if target is None else hit_ratio[0]


def che_cache_hit_ratio_simplified(pdf, cache_size):
    """Estimate the overall cache hit ratio of an LRU cache under generic IRM
    demand using the Che's approximation. This version uses a single
    characteristic time for all contents.

    Parameters
    ----------
    pdf : array-like
        The probability density function of an item being requested
    cache_size : int
        The size of the cache (in number of items)

    Returns
    -------
    cache_hit_ratio : float
        The overall cache hit ratio
    """
    ch = che_per_content_cache_hit_ratio_simplified(pdf, cache_size)
    return sum(pdf[i] * ch[i] for i in range(len(pdf)))


def che_p_in_func(pdf, policy, **policy_args):
    """Return function to compute cache hit ratio of a policy given probability
    of a content being requested and characteristic time

    Parameters
    ----------
    pdf : array-like
        The probability density function of an item being requested
    policy : str
        The cache replacement policy ('LRU', 'q-LRU', 'FIFO', 'RANDOM')
    """
    if policy == 'LRU':
        p_in = lambda p, t: 1 - np.exp(-p * t)
    elif policy == 'q-LRU':
        if 'q' not in policy_args:
            raise ValueError('q parameter not specified')
        q = policy_args['q']
        p_in = lambda p, t: q * (1 - np.exp(-p * t)) / (np.exp(-p * t) + q * (1 - np.exp(-p * t)))
    elif policy in ('FIFO', 'RANDOM'):
        p_in = lambda p, t: p * t / (1 + p * t)
    else:
        raise ValueError('policy {} not recognized'.format(policy))
    return p_in


def che_characteristic_time_generalized(pdf, cache_size, policy, **policy_args):
    """Return the characteristic time of a cache under a given IRM demand
    according to the the extension of Che's approximation proposed by Martina
    et al.
    This function computes one single characteristic time for all content items.

    Parameters
    ----------
    pdf : array-like
        The probability density function of an item being requested
    cache_size : int
        The size of the cache (in number of items)
    policy : str
        The cache replacement policy ('LRU', 'q-LRU', 'FIFO', 'RANDOM')

    Returns
    -------
    r : float
        The characteristic time.

    Rereferences
    ------------
    V. Martina, M. Garetto, and E. Leonardi, "A unified approach to the
    performance analysis of caching systems," in Proceedings of the 2014
    IEEE Conference on Computer Communications (INFOCOM'14), April 2014
    """
    p_in = che_p_in_func(pdf, policy, **policy_args)

    def func_t(t):
        return np.sum(p_in(pdf, t)) - cache_size

    return fsolve(func_t, x0=cache_size)[0]


def che_per_content_cache_hit_ratio_generalized(pdf, cache_size, policy,
                                                **policy_args):
    """Estimate the cache hit ratio of an item or of all items in a cache
    subject to IRM demand according to the extension of Che's approximation
    proposed by Martina et al.

    Parameters
    ----------
    pdf : array-like
        The probability density function of an item being requested
    cache_size : int
        The size of the cache (in number of items)
    policy : str, optional
        The cache replacement policy ('LRU', 'q-LRU', 'FIFO', 'RANDOM')

    Returns
    -------
    cache_hit_ratio : array of float or float
        If target is None, returns an array with the cache hit ratios of all
        items in the population. If a target is specified, then it returns
        the cache hit ratio of only the specified item.

    Rereferences
    ------------
    V. Martina, M. Garetto, and E. Leonardi, "A unified approach to the
    performance analysis of caching systems," in Proceedings of the 2014
    IEEE Conference on Computer Communications (INFOCOM'14), April 2014
    """
    p_in = che_p_in_func(pdf, policy, **policy_args)
    t = che_characteristic_time_generalized(pdf, cache_size, policy, **policy_args)
    return p_in(pdf, t)


def che_cache_hit_ratio_generalized(pdf, cache_size, policy='LRU', **policy_args):
    """Estimate the overall cache hit ratio of a cache subject to IRM demand
    according to the extension of Che's approximation proposed by Martina et al.

    Parameters
    ----------
    pdf : array-like
        The probability density function of an item being requested
    cache_size : int
        The size of the cache (in number of items)
    policy : str, optional
        The cache replacement policy ('LRU', 'q-LRU', 'FIFO', 'RANDOM')

    Returns
    -------
    cache_hit_ratio : float
        The overall cache hit ratio

    Rereferences
    ------------
    V. Martina, M. Garetto, and E. Leonardi, "A unified approach to the
    performance analysis of caching systems," in Proceedings of the 2014
    IEEE Conference on Computer Communications (INFOCOM'14), April 2014
    """
    ch = che_per_content_cache_hit_ratio_generalized(pdf, cache_size, policy, **policy_args)
    return sum(pdf[i] * ch[i] for i in range(len(pdf)))


def laoutaris_characteristic_time(alpha, population, cache_size, order=3):
    """Estimates the Che's characteristic time of an LRU cache under general
    power-law demand using the Laoutaris approximation.

    Parameters
    ----------
    alpha : float
        The coefficient of the demand power-law
    population : int
        The content population
    cache_size : int
        The cache size
    order : int, optional
        The order of the Taylor expansion. Supports only 2 and 3

    Returns
    -------
    cache_hit_ratio : float
        The cache hit ratio

    References
    ----------
    http://arxiv.org/pdf/0705.1970.pdf
    """
    def H(N, alpha):
        return sum(1.0 / l ** alpha for l in range(1, N + 1))

    def cubrt(x):
        """Compute cubic root of a number

        Parameters
        ----------
        x : float
            Number whose cubic root is to be calculated

        Returns
        -------
        cubrt : float
            The cubic root
        """
        exp = 1.0 / 3
        return x ** exp if x >= 0 else -(-x) ** exp

    def solve_3rd_order_equation(a, b, c, d):
        """Calculate the real solutions of the 3rd order equations
        a*x**3 + b*x**2 + c*x + d = 0

        Parameters
        ----------
        a : float
            Coefficent of 3rd degree monomial
        b : float
            Coefficent of 2nd degree monomial
        c : float
            Coefficent of 1st degree monomial
        d : float
            Constant

        Returns
        -------
        roots : tuple
            Tuple of real solutions.
            The tuple may comprise either 1 or 3 values

        Notes
        -----
        The method used to calculate roots is described in this paper:
        http://www.nickalls.org/dick/papers/maths/cubic1993.pdf
        """
        # Compute parameters
        x_N = -b / (3 * a)
        y_N = a * x_N ** 3 + b * x_N ** 2 + c * x_N + d
        delta_2 = (b ** 2 - 3 * a * c) / (9 * a ** 2)
        h_2 = 4 * (a ** 2) * (delta_2 ** 3)
        # Calculate discriminator and find roots
        discr = y_N ** 2 - h_2
        if discr > 0:
            r_x = (x_N + cubrt(0.5 / a * (-y_N + math.sqrt(discr))) +
                   cubrt(0.5 / a * (-y_N - math.sqrt(discr))),)
        elif discr == 0:
            delta = math.sqrt(delta_2)
            r1 = r2 = x_N + delta
            r3 = x_N - 2 * delta
            r_x = (r1, r2, r3)
        else:  # discr < 0
            h = math.sqrt(h_2)
            delta = math.sqrt(delta_2)
            Theta = np.arccos(-y_N / h) / 3.0
            r1 = x_N + 2 * delta * np.cos(Theta)
            r2 = x_N + 2 * delta * np.cos(2 * np.pi / 3 - Theta)
            r3 = x_N + 2 * delta * np.cos(2 * np.pi / 3 + Theta)
            r_x = (r1, r2, r3)
        return r_x
    # Get parameters
    C = cache_size
    N = population
    # Calculate harmonics
    H_N_a = H(N, alpha)
    H_N_2a = H(N, 2 * alpha)
    H_N_3a = H(N, 3 * alpha)
    H_N_4a = H(N, 4 * alpha)
    Lambda = 1.0 / H_N_a
    # Find values of r
    if order == 2:
        alpha_2 = (0.5 * Lambda ** 2 * H_N_2a) - \
                  (0.5 * Lambda ** 3 * C * H_N_3a) + \
                  (0.25 * Lambda ** 4 * C ** 2 * H_N_4a)
        alpha_1 = -(Lambda * H_N_a) + \
                   (0.5 * Lambda ** 3 * C ** 2 * H_N_3a) - \
                   (0.5 * Lambda ** 4 * C ** 3 * H_N_4a)
        alpha_0 = C + (0.25 * Lambda ** 4 * C ** 4 * H_N_4a)
        # Calculate discriminant to verify if there are real solutions
        discr = alpha_1 ** 2 - 4 * alpha_2 * alpha_0
        if discr < 0:
            raise ValueError('Could not find real values for the '
                             'characteristic time. Try using a 3rd order '
                             'expansion')
        # Calculate roots of the 2nd order equation
        r1 = (-alpha_1 + math.sqrt(discr)) / (2 * alpha_2)
        r2 = (-alpha_1 - math.sqrt(discr)) / (2 * alpha_2)
        r_x = (r1, r2)
    elif order == 3:
        # Additional parameters
        H_N_5a = H(N, 5 * alpha)
        H_N_6a = H(N, 6 * alpha)
        # Calculate coefficients of the 3rd order equation
        alpha_3 = -(Lambda ** 3 / 6 * H_N_3a) + (Lambda ** 4 * C / 6 * H_N_4a) - \
                   (Lambda ** 5 * C ** 2 / 12 * H_N_5a) + (Lambda ** 6 * C ** 3 / 36 * H_N_6a)
        alpha_2 = (Lambda ** 2 / 2 * H_N_2a) - (Lambda ** 4 * C ** 2 / 4 * H_N_4a) + \
                  (Lambda ** 5 * C ** 3 / 6 * H_N_5a) - (Lambda ** 6 * C ** 4 / 12 * H_N_6a)
        alpha_1 = -Lambda * H_N_a + (Lambda ** 4 * C ** 3 / 6 * H_N_4a) - \
                                    (Lambda ** 5 * C ** 4 / 12 * H_N_5a) + \
                                    (Lambda ** 6 * C ** 5 / 12 * H_N_6a)
        alpha_0 = C - (Lambda ** 4 * C ** 4 / 12 * H_N_4a) - \
                      (Lambda ** 6 * C ** 6 / 36 * H_N_6a)
        # Solve 3rd order equation
        r_x = solve_3rd_order_equation(alpha_3, alpha_2, alpha_1, alpha_0)
    else:
        raise ValueError('Only 2nd and 3rd order solutions are supported')
    # Find actual value of characteristic time (r) if exists
    # We select the minimum positive r greater than C
    r_c = [x for x in r_x if x > C]
    if r_c:
        return min(r_c)
    else:
        raise ValueError('Cannot compute cache hit ratio using this method. '
                         'Could not find positive values of characteristic time'
                         ' greater than the cache size.')


def laoutaris_per_content_cache_hit_ratio(alpha, population, cache_size,
                                          order=3, target=None):
    """Estimates the per-content cache hit ratio of an LRU cache under general
    power-law demand using the Laoutaris approximation.

    Parameters
    ----------
    alpha : float
        The coefficient of the demand power-law distribution
    population : int
        The content population
    cache_size : int
        The cache size
    order : int, optional
        The order of the Taylor expansion. Supports only 2 and 3
    target : int, optional
        The item index [1,N] for which cache hit ratio is requested. If not
        specified, the function calculates the cache hit ratio of all the items
        in the population.

    Returns
    -------
    cache_hit_ratio : array of float or float
        If target is None, returns an array with the cache hit ratios of all
        items in the population. If a target is specified, then it returns
        the cache hit ratio of only the specified item.

    References
    ----------
    http://arxiv.org/pdf/0705.1970.pdf
    """
    pdf = TruncatedZipfDist(alpha, population).pdf
    r = laoutaris_characteristic_time(alpha, population, cache_size, order)
    items = range(len(pdf)) if target is None else [target - 1]
    hit_ratio = [1 - math.exp(-pdf[i] * r) for i in items]
    return hit_ratio if target is None else hit_ratio[0]


def laoutaris_cache_hit_ratio(alpha, population, cache_size, order=3):
    """Estimate the cache hit ratio of an LRU cache under general power-law
    demand using the Laoutaris approximation.

    Parameters
    ----------
    alpha : float
        The coefficient of the demand power-law distribution
    population : int
        The content population
    cache_size : int
        The cache size
    order : int, optional
        The order of the Taylor expansion. Supports only 2 and 3

    Returns
    -------
    cache_hit_ratio : float
        The cache hit ratio

    References
    ----------
    http://arxiv.org/pdf/0705.1970.pdf
    """
    pdf = TruncatedZipfDist(alpha, population).pdf
    r = laoutaris_characteristic_time(alpha, population, cache_size, order)
    return np.sum(pdf * (1 - math.e ** -(r * pdf)))


def optimal_cache_hit_ratio(pdf, cache_size):
    """Return the value of the optimal cache hit ratio of a cache under IRM
    stationary demand with a given pdf.

    In practice this function returns the probability of a cache hit if cache
    is filled with the *cache_size* most popular times. This value also
    corresponds to the steady-state cache hit ratio of an LFU cache.

    Parameters
    ----------
    pdf : array-like
        The probability density function of an item being requested
    cache_size : int
        The size of the cache (in number of items)

    Returns
    -------
    cache_hit_ratio : float
        The optimal cache hit ratio
    """
    if cache_size >= len(pdf):
        return 1.0
    return sum(sorted(pdf, reverse=True)[:cache_size])


def numeric_per_content_cache_hit_ratio(pdf, cache, warmup=None, measure=None,
                                        seed=None, target=None):
    """Numerically compute the per-content cache hit ratio of a cache under IRM
    stationary demand with a given pdf.

    Parameters
    ----------
    pdf : array-like
        The probability density function of an item being requested
    cache : Cache
        The cache object (i.e. the instance of a class subclassing
        icarus.Cache)
    warmup : int, optional
        The number of warmup requests to generate. If not specified, it is set
        to 10 times the content population
    measure : int, optional
        The number of measured requests to generate. If not specified, it is
        set to 30 times the content population
    seed : int, optional
        The seed used to generate random numbers
    target : int, optional
        The item index [1, N] for which cache hit ratio is requested. If not
        specified, the function calculates the cache hit ratio of all the items
        in the population.

    Returns
    -------
    cache_hit_ratio : array of float or float
        If target is None, returns an array with the cache hit ratios of all
        items in the population. If a target is specified, then it returns
        the cache hit ratio of only the specified item.
    """
    if warmup is None:
        warmup = 10 * len(pdf)
    if measure is None:
        measure = 30 * len(pdf)
    z = DiscreteDist(pdf, seed)
    for _ in range(warmup):
        content = z.rv()
        if not cache.get(content):
            cache.put(content)
    cache_hits = np.zeros(len(pdf))
    requests = np.zeros(len(pdf))
    for _ in range(measure):
        content = z.rv()
        requests[content - 1] += 1
        if cache.get(content):
            cache_hits[content - 1] += 1
        else:
            cache.put(content)
    hit_ratio = np.where(requests > 0, cache_hits / requests, requests)
    return hit_ratio if target is None else hit_ratio[target - 1]


def numeric_cache_hit_ratio(pdf, cache, warmup=None, measure=None, seed=None):
    """Numerically compute the cache hit ratio of a cache under IRM
    stationary demand with a given pdf.

    Parameters
    ----------
    pdf : array-like
        The probability density function of an item being requested
    cache : Cache
        The cache object (i.e. the instance of a class subclassing
        icarus.Cache)
    warmup : int, optional
        The number of warmup requests to generate. If not specified, it is set
        to 10 times the content population
    measure : int, optional
        The number of measured requests to generate. If not specified, it is
        set to 30 times the content population
    seed : int, optional
        The seed used to generate random numbers

    Returns
    -------
    cache_hit_ratio : float
        The cache hit ratio
    """
    if warmup is None:
        warmup = 10 * len(pdf)
    if measure is None:
        measure = 30 * len(pdf)
    z = DiscreteDist(pdf, seed)
    for _ in range(warmup):
        content = z.rv()
        if not cache.get(content):
            cache.put(content)
    cache_hits = 0
    for _ in range(measure):
        content = z.rv()
        if cache.get(content):
            cache_hits += 1
        else:
            cache.put(content)
    return cache_hits / measure


def numeric_cache_hit_ratio_2_layers(pdf, l1_cache, l2_cache,
                                     warmup=None, measure=None, seed=None):
    """Numerically compute the cache hit ratio of a two-layer cache under IRM
    stationary demand with a given pdf.

    Differently from the numeric_cache_hit_ratio function, this function
    allows users to compute the hits at layer 1, layer 2 and overall.

    Parameters
    ----------
    pdf : array-like
        The probability density function of an item being requested
    cache : Cache
        The cache object (i.e. the instance of a class subclassing
        icarus.Cache)
    warmup : int, optional
        The number of warmup requests to generate. If not specified, it is set
        to 10 times the content population
    measure : int, optional
        The number of measured requests to generate. If not specified, it is
        set to 30 times the content population
    seed : int, optional
        The seed used to generate random numbers

    Returns
    -------
    cache_hit_ratio : dict
        Dictionary with keys "l1_hits", "l2_hits" and "total_hits"
    """
    if warmup is None:
        warmup = 10 * len(pdf)
    if measure is None:
        measure = 30 * len(pdf)
    z = DiscreteDist(pdf, seed)
    for _ in range(warmup):
        content = z.rv()
        if not l1_cache.get(content):
            if not l2_cache.get(content):
                l2_cache.put(content)
            l1_cache.put(content)
    l1_hits = 0
    l1_misses = 0
    l2_hits = 0
    for _ in range(measure):
        content = z.rv()
        if l1_cache.get(content):
            l1_hits += 1
        else:
            l1_misses += 1
            if l2_cache.get(content):
                l2_hits += 1
            else:
                l2_cache.put(content)
            l1_cache.put(content)
    return {
        'l1_hits': l1_hits / measure,
        'l2_hits': l2_hits / measure,
        'total_hits': (l1_hits + l2_hits) / measure
           }


def trace_driven_cache_hit_ratio(workload, cache, warmup_ratio=0.25):
    """Compute cache hit ratio of a cache under an arbitrary trace-driven
    workload.

    Parameters
    ----------
    workload : list or array
        List of URLs or content identifiers extracted from a trace. This list
        only needs to contains content identifiers and not timestamps
    cache : Cache
        Instance of a cache object
    warmup_ratio : float, optional
        Ratio of requests of the workload used to warm up the cache (i.e. whose
        cache hit/miss results are discarded)

    Returns
    -------
    cache_hit_ratio : float
        The cache hit ratio
    """
    if warmup_ratio < 0 or warmup_ratio > 1:
        raise ValueError("warmup_ratio must be comprised between 0 and 1")
    n = len(workload)
    cache_hits = 0
    n_warmup = int(warmup_ratio * n)
    n_req = 0
    for content in workload:
        if cache.get(content):
            if n_req >= n_warmup:
                cache_hits += 1
        else:
            cache.put(content)
        n_req += 1
    return cache_hits / (n - n_warmup)


def hashrouting_model(topology, routing, hit_ratio, source_content_ratio,
                      req_rates, paths=None):
    """Compute overall latency of hashrouting over an arbitrary topology

    Parameters
    ----------
    topology : Topology
        The topology
    routing : str ('SYMM | 'MULTICAST')
        Content routing strategy
    hit_ratio : float
        Average cache hit ratio of the system of hash-routed caches
    source_content_ratio : dict
        Ratio of contents that each source serve
    req_rates : dict
        Rate of requests for each requester
    paths : dict of dicts, optional
        Network paths

    Returns
    -------
    latency : float
        The average content retrieval latency

    References
    ----------
    .. [1] L. Saino, I. Psaras and G. Pavlou, Framework and Algorithms for
           Operator-managed Content Caching, in IEEE Transactions on
           Network and Service Management (TNSM), Volume 17, Issue 1, March 2020
           https://doi.org/10.1109/TNSM.2019.2956525
    .. [2] L. Saino, On the Design of Efficient Caching Systems, Ph.D. thesis
           University College London, Dec. 2015. Available:
           http://discovery.ucl.ac.uk/1473436/
    """
    if routing not in ('SYMM', 'MULTICAST'):
        raise ValueError("Routing {} not supported".format(routing))
    if math.fabs(sum(source_content_ratio.values()) - 1) > 0.0001:
        raise ValueError("The sum of source_content_ratio values must be 1")
    if paths is None:
        paths = dict(nx.all_pairs_dijkstra_path(topology))
    latencies = {}
    for u in paths:
        latencies[u] = {}
        for v in paths[u]:
            links = path_links(paths[u][v])
            latencies[u][v] = sum(topology.edges[i, j]['delay'] for i, j in links)
    # Get all caching nodes
    caches = topology.cache_nodes()
    overall_req_rate = sum(req_rates.values())

    req_ratios = {k: v / overall_req_rate for k, v in req_rates.items()}
    # Calculate overall latency

    # This is the latency component between receivers and caches
    if routing == 'SYMM':
        latency = (1 / len(caches)) * \
                  sum(rate * (latencies[recv][cache] + latencies[cache][recv])
                      for recv, rate in req_ratios.items() for cache in caches)
        # This is the latency component between caches and sources
        latency += ((1 - hit_ratio) / len(caches)) * \
                   sum(ratio * (latencies[cache][source] + latencies[source][cache])
                       for cache in caches
                       for source, ratio in source_content_ratio.items())
    elif routing == 'MULTICAST':
        # Latency leg receiver-cache
        latency = (1 / len(caches)) * \
          sum(rate * (latencies[recv][cache])
              for recv, rate in req_ratios.items() for cache in caches)
        # Latency leg cache-receiver (hit case)
        latency += (hit_ratio / len(caches)) * \
          sum(rate * (latencies[cache][recv])
              for recv, rate in req_ratios.items() for cache in caches)
        # Latency leg caches-sources (miss case)
        latency += ((1 - hit_ratio) / len(caches)) * \
                    sum(ratio * (latencies[cache][source])
                        for cache in caches
                        for source, ratio in source_content_ratio.items())
        # Latency leg sources-receivers (miss case)
        latency += (1 - hit_ratio) * \
                    sum(source_ratio * req_ratio * (latencies[source][receiver])
                        for receiver, req_ratio in req_ratios.items()
                        for source, source_ratio in source_content_ratio.items())
    else:
        # Should never reach this block anyway
        raise ValueError("Routing {} not supported".format(routing))
    return latency


def hashrouting_model_mesh(n, m, h, delay_int, delay_ext):
    """Compute latency of hashrouting over a mesh topology

    Parameters
    ----------
    n : int
        The number of nodes in the mesh
    m : int
        The number of nodes directly connected with an origin
    h : float
        The cumulative cache hit ratio of the network
    delay_int : float
        The latency on an internal link
    delay_ext : float
        The latency on an external link

    Returns
    -------
    latency : float
        The average content retrieval latency

    References
    ----------
    .. [1] L. Saino, I. Psaras and G. Pavlou, Framework and Algorithms for
           Operator-managed Content Caching, in IEEE Transactions on
           Network and Service Management (TNSM), Volume 17, Issue 1, March 2020
           https://doi.org/10.1109/TNSM.2019.2956525
    .. [2] L. Saino, On the Design of Efficient Caching Systems, Ph.D. thesis
           University College London, Dec. 2015. Available:
           http://discovery.ucl.ac.uk/1473436/
    """
    if m > n:
        raise ValueError("m must be no greater than n")
    if h < 0 or h > 1:
        raise ValueError("h must be comprised between 0 and 1")
    return 2*(((n-1)/n)*delay_int + (1-h)*(((n-m)/n)*delay_int + delay_ext))


def hashrouting_model_ring(n, h, delay_int, delay_ext):
    """Compute latency of hashrouting over a mesh topology

    Parameters
    ----------
    n : int
        The number of nodes in the mesh
    h : float
        The cumulative cache hit ratio of the network
    delay_int : float
        The latency on an internal link
    delay_ext : float
        The latency on an external link

    Returns
    -------
    latency : float
        The average content retrieval latency

    References
    ----------
    .. [1] L. Saino, I. Psaras and G. Pavlou, Framework and Algorithms for
           Operator-managed Content Caching, in IEEE Transactions on
           Network and Service Management (TNSM), Volume 17, Issue 1, March 2020
           https://doi.org/10.1109/TNSM.2019.2956525
    .. [2] L. Saino, On the Design of Efficient Caching Systems, Ph.D. thesis
           University College London, Dec. 2015. Available:
           http://discovery.ucl.ac.uk/1473436/
    """
    if h < 0 or h > 1:
        raise ValueError("h must be comprised between 0 and 1")
    avg_hop = (n**2 - 1)/(4*n) if n % 2 == 1 else n/4
    return 2*(avg_hop*delay_int + (1-h)*(avg_hop*delay_int + delay_ext))
