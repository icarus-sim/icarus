#!/usr/bin/env python
"""Plot results read from a result set
"""
from __future__ import division
import os
import argparse
import logging

import matplotlib.pyplot as plt

from icarus.util import Settings, config_logging
from icarus.results import plot_lines, plot_bar_chart
from icarus.registry import RESULTS_READER


# Logger object
logger = logging.getLogger('plot')

# These lines prevent insertion of Type 3 fonts in figures
# Publishers don't want them
plt.rcParams['ps.useafm'] = True
plt.rcParams['pdf.use14corefonts'] = True

# If True text is interpreted as LaTeX, e.g. underscore are interpreted as
# subscript. If False, text is interpreted literally
plt.rcParams['text.usetex'] = False

# Aspect ratio of the output figures
plt.rcParams['figure.figsize'] = 8, 5

# Size of font in legends
LEGEND_SIZE = 14

# Line width in pixels
LINE_WIDTH = 1.5

# Plot
PLOT_EMPTY_GRAPHS = True

# This dict maps strategy names to the style of the line to be used in the plots
# Off-path strategies: solid lines
# On-path strategies: dashed lines
# No-cache: dotted line
STRATEGY_STYLE = {
         'HR_SYMM':         'b-o',
         'HR_ASYMM':        'g-D',
         'HR_MULTICAST':    'm-^',
         'HR_HYBRID_AM':    'c-s',
         'HR_HYBRID_SM':    'r-v',
         'LCE':             'b--p',
         'LCD':             'g-->',
         'CL4M':            'g-->',
         'PROB_CACHE':      'c--<',
         'RAND_CHOICE':     'r--<',
         'RAND_BERNOULLI':  'g--*',
         'NO_CACHE':        'k:o',
         'OPTIMAL':         'k-o'
                }

# This dict maps name of strategies to names to be displayed in the legend
STRATEGY_LEGEND = {
         'LCE':             'LCE',
         'LCD':             'LCD',
         'HR_SYMM':         'HR Symm',
         'HR_ASYMM':        'HR Asymm',
         'HR_MULTICAST':    'HR Multicast',
         'HR_HYBRID_AM':    'HR Hybrid AM',
         'HR_HYBRID_SM':    'HR Hybrid SM',
         'CL4M':            'CL4M',
         'PROB_CACHE':      'ProbCache',
         'RAND_CHOICE':     'Random (choice)',
         'RAND_BERNOULLI':  'Random (Bernoulli)',
         'NO_CACHE':        'No caching',
         'OPTIMAL':         'Optimal'
                    }

# Color and hatch styles for bar charts of cache hit ratio and link load vs topology
STRATEGY_BAR_COLOR = {
    'LCE':          'k',
    'LCD':          '0.4',
    'NO_CACHE':     '0.5',
    'HR_ASYMM':     '0.6',
    'HR_SYMM':      '0.7'
    }

STRATEGY_BAR_HATCH = {
    'LCE':          None,
    'LCD':          '//',
    'NO_CACHE':     'x',
    'HR_ASYMM':     '+',
    'HR_SYMM':      '\\'
    }


def plot_cache_hits_vs_alpha(resultset, topology, cache_size, alpha_range, strategies, plotdir):
    if 'NO_CACHE' in strategies:
        strategies.remove('NO_CACHE')
    desc = {}
    desc['title'] = 'Cache hit ratio: T=%s C=%s' % (topology, cache_size)
    desc['ylabel'] = 'Cache hit ratio'
    desc['xlabel'] = u'Content distribution \u03b1'
    desc['xparam'] = ('workload', 'alpha')
    desc['xvals'] = alpha_range
    desc['filter'] = {'topology': {'name': topology},
                      'cache_placement': {'network_cache': cache_size}}
    desc['ymetrics'] = [('CACHE_HIT_RATIO', 'MEAN')] * len(strategies)
    desc['ycondnames'] = [('strategy', 'name')] * len(strategies)
    desc['ycondvals'] = strategies
    desc['errorbar'] = True
    desc['legend_loc'] = 'upper left'
    desc['line_style'] = STRATEGY_STYLE
    desc['legend'] = STRATEGY_LEGEND
    desc['plotempty'] = PLOT_EMPTY_GRAPHS
    plot_lines(resultset, desc, 'CACHE_HIT_RATIO_T=%s@C=%s.pdf'
               % (topology, cache_size), plotdir)


def plot_cache_hits_vs_cache_size(resultset, topology, alpha, cache_size_range, strategies, plotdir):
    desc = {}
    if 'NO_CACHE' in strategies:
        strategies.remove('NO_CACHE')
    desc['title'] = 'Cache hit ratio: T=%s A=%s' % (topology, alpha)
    desc['xlabel'] = u'Cache to population ratio'
    desc['ylabel'] = 'Cache hit ratio'
    desc['xscale'] = 'log'
    desc['xparam'] = ('cache_placement', 'network_cache')
    desc['xvals'] = cache_size_range
    desc['filter'] = {'topology': {'name': topology},
                      'workload': {'name': 'STATIONARY', 'alpha': alpha}}
    desc['ymetrics'] = [('CACHE_HIT_RATIO', 'MEAN')] * len(strategies)
    desc['ycondnames'] = [('strategy', 'name')] * len(strategies)
    desc['ycondvals'] = strategies
    desc['errorbar'] = True
    desc['legend_loc'] = 'upper left'
    desc['line_style'] = STRATEGY_STYLE
    desc['legend'] = STRATEGY_LEGEND
    desc['plotempty'] = PLOT_EMPTY_GRAPHS
    plot_lines(resultset, desc, 'CACHE_HIT_RATIO_T=%s@A=%s.pdf'
               % (topology, alpha), plotdir)


def plot_link_load_vs_alpha(resultset, topology, cache_size, alpha_range, strategies, plotdir):
    desc = {}
    desc['title'] = 'Internal link load: T=%s C=%s' % (topology, cache_size)
    desc['xlabel'] = u'Content distribution \u03b1'
    desc['ylabel'] = 'Internal link load'
    desc['xparam'] = ('workload', 'alpha')
    desc['xvals'] = alpha_range
    desc['filter'] = {'topology': {'name': topology},
                      'cache_placement': {'network_cache': cache_size}}
    desc['ymetrics'] = [('LINK_LOAD', 'MEAN_INTERNAL')] * len(strategies)
    desc['ycondnames'] = [('strategy', 'name')] * len(strategies)
    desc['ycondvals'] = strategies
    desc['errorbar'] = True
    desc['legend_loc'] = 'upper right'
    desc['line_style'] = STRATEGY_STYLE
    desc['legend'] = STRATEGY_LEGEND
    desc['plotempty'] = PLOT_EMPTY_GRAPHS
    plot_lines(resultset, desc, 'LINK_LOAD_INTERNAL_T=%s@C=%s.pdf'
               % (topology, cache_size), plotdir)


def plot_link_load_vs_cache_size(resultset, topology, alpha, cache_size_range, strategies, plotdir):
    desc = {}
    desc['title'] = 'Internal link load: T=%s A=%s' % (topology, alpha)
    desc['xlabel'] = 'Cache to population ratio'
    desc['ylabel'] = 'Internal link load'
    desc['xscale'] = 'log'
    desc['xparam'] = ('cache_placement', 'network_cache')
    desc['xvals'] = cache_size_range
    desc['filter'] = {'topology': {'name': topology},
                      'workload': {'name': 'stationary', 'alpha': alpha}}
    desc['ymetrics'] = [('LINK_LOAD', 'MEAN_INTERNAL')] * len(strategies)
    desc['ycondnames'] = [('strategy', 'name')] * len(strategies)
    desc['ycondvals'] = strategies
    desc['errorbar'] = True
    desc['legend_loc'] = 'upper right'
    desc['line_style'] = STRATEGY_STYLE
    desc['legend'] = STRATEGY_LEGEND
    desc['plotempty'] = PLOT_EMPTY_GRAPHS
    plot_lines(resultset, desc, 'LINK_LOAD_INTERNAL_T=%s@A=%s.pdf'
               % (topology, alpha), plotdir)


def plot_latency_vs_alpha(resultset, topology, cache_size, alpha_range, strategies, plotdir):
    desc = {}
    desc['title'] = 'Latency: T=%s C=%s' % (topology, cache_size)
    desc['xlabel'] = u'Content distribution \u03b1'
    desc['ylabel'] = 'Latency (ms)'
    desc['xparam'] = ('workload', 'alpha')
    desc['xvals'] = alpha_range
    desc['filter'] = {'topology': {'name': topology},
                      'cache_placement': {'network_cache': cache_size}}
    desc['ymetrics'] = [('LATENCY', 'MEAN')] * len(strategies)
    desc['ycondnames'] = [('strategy', 'name')] * len(strategies)
    desc['ycondvals'] = strategies
    desc['errorbar'] = True
    desc['legend_loc'] = 'upper right'
    desc['line_style'] = STRATEGY_STYLE
    desc['legend'] = STRATEGY_LEGEND
    desc['plotempty'] = PLOT_EMPTY_GRAPHS
    plot_lines(resultset, desc, 'LATENCY_T=%s@C=%s.pdf'
               % (topology, cache_size), plotdir)


def plot_latency_vs_cache_size(resultset, topology, alpha, cache_size_range, strategies, plotdir):
    desc = {}
    desc['title'] = 'Latency: T=%s A=%s' % (topology, alpha)
    desc['xlabel'] = 'Cache to population ratio'
    desc['ylabel'] = 'Latency'
    desc['xscale'] = 'log'
    desc['xparam'] = ('cache_placement', 'network_cache')
    desc['xvals'] = cache_size_range
    desc['filter'] = {'topology': {'name': topology},
                      'workload': {'name': 'STATIONARY', 'alpha': alpha}}
    desc['ymetrics'] = [('LATENCY', 'MEAN')] * len(strategies)
    desc['ycondnames'] = [('strategy', 'name')] * len(strategies)
    desc['ycondvals'] = strategies
    desc['metric'] = ('LATENCY', 'MEAN')
    desc['errorbar'] = True
    desc['legend_loc'] = 'upper right'
    desc['line_style'] = STRATEGY_STYLE
    desc['legend'] = STRATEGY_LEGEND
    desc['plotempty'] = PLOT_EMPTY_GRAPHS
    plot_lines(resultset, desc, 'LATENCY_T=%s@A=%s.pdf'
               % (topology, alpha), plotdir)


def plot_cache_hits_vs_topology(resultset, alpha, cache_size, topology_range, strategies, plotdir):
    """
    Plot bar graphs of cache hit ratio for specific values of alpha and cache
    size for various topologies.

    The objective here is to show that our algorithms works well on all
    topologies considered
    """
    if 'NO_CACHE' in strategies:
        strategies.remove('NO_CACHE')
    desc = {}
    desc['title'] = 'Cache hit ratio: A=%s C=%s' % (alpha, cache_size)
    desc['ylabel'] = 'Cache hit ratio'
    desc['xparam'] = ('topology', 'name')
    desc['xvals'] = topology_range
    desc['filter'] = {'cache_placement': {'network_cache': cache_size},
                      'workload': {'name': 'STATIONARY', 'alpha': alpha}}
    desc['ymetrics'] = [('CACHE_HIT_RATIO', 'MEAN')] * len(strategies)
    desc['ycondnames'] = [('strategy', 'name')] * len(strategies)
    desc['ycondvals'] = strategies
    desc['errorbar'] = True
    desc['legend_loc'] = 'lower right'
    desc['bar_color'] = STRATEGY_BAR_COLOR
    desc['bar_hatch'] = STRATEGY_BAR_HATCH
    desc['legend'] = STRATEGY_LEGEND
    desc['plotempty'] = PLOT_EMPTY_GRAPHS
    plot_bar_chart(resultset, desc, 'CACHE_HIT_RATIO_A=%s_C=%s.pdf'
                   % (alpha, cache_size), plotdir)


def plot_link_load_vs_topology(resultset, alpha, cache_size, topology_range, strategies, plotdir):
    """
    Plot bar graphs of link load for specific values of alpha and cache
    size for various topologies.

    The objective here is to show that our algorithms works well on all
    topologies considered
    """
    desc = {}
    desc['title'] = 'Internal link load: A=%s C=%s' % (alpha, cache_size)
    desc['ylabel'] = 'Internal link load'
    desc['xparam'] = ('topology', 'name')
    desc['xvals'] = topology_range
    desc['filter'] = {'cache_placement': {'network_cache': cache_size},
                      'workload': {'name': 'STATIONARY', 'alpha': alpha}}
    desc['ymetrics'] = [('LINK_LOAD', 'MEAN_INTERNAL')] * len(strategies)
    desc['ycondnames'] = [('strategy', 'name')] * len(strategies)
    desc['ycondvals'] = strategies
    desc['errorbar'] = True
    desc['legend_loc'] = 'lower right'
    desc['bar_color'] = STRATEGY_BAR_COLOR
    desc['bar_hatch'] = STRATEGY_BAR_HATCH
    desc['legend'] = STRATEGY_LEGEND
    desc['plotempty'] = PLOT_EMPTY_GRAPHS
    plot_bar_chart(resultset, desc, 'LINK_LOAD_INTERNAL_A=%s_C=%s.pdf'
                   % (alpha, cache_size), plotdir)


def run(config, results, plotdir):
    """Run the plot script

    Parameters
    ----------
    config : str
        The path of the configuration file
    results : str
        The file storing the experiment results
    plotdir : str
        The directory into which graphs will be saved
    """
    settings = Settings()
    settings.read_from(config)
    config_logging(settings.LOG_LEVEL)
    resultset = RESULTS_READER[settings.RESULTS_FORMAT](results)
    # Create dir if not existsing
    if not os.path.exists(plotdir):
        os.makedirs(plotdir)
    # Parse params from settings
    topologies = settings.TOPOLOGIES
    cache_sizes = settings.NETWORK_CACHE
    alphas = settings.ALPHA
    strategies = settings.STRATEGIES
    # Plot graphs
    for topology in topologies:
        for cache_size in cache_sizes:
            logger.info('Plotting cache hit ratio for topology %s and cache size %s vs alpha' % (topology, str(cache_size)))
            plot_cache_hits_vs_alpha(resultset, topology, cache_size, alphas, strategies, plotdir)
            logger.info('Plotting link load for topology %s vs cache size %s' % (topology, str(cache_size)))
            plot_link_load_vs_alpha(resultset, topology, cache_size, alphas, strategies, plotdir)
            logger.info('Plotting latency for topology %s vs cache size %s' % (topology, str(cache_size)))
            plot_latency_vs_alpha(resultset, topology, cache_size, alphas, strategies, plotdir)
    for topology in topologies:
        for alpha in alphas:
            logger.info('Plotting cache hit ratio for topology %s and alpha %s vs cache size' % (topology, str(alpha)))
            plot_cache_hits_vs_cache_size(resultset, topology, alpha, cache_sizes, strategies, plotdir)
            logger.info('Plotting link load for topology %s and alpha %s vs cache size' % (topology, str(alpha)))
            plot_link_load_vs_cache_size(resultset, topology, alpha, cache_sizes, strategies, plotdir)
            logger.info('Plotting latency for topology %s and alpha %s vs cache size' % (topology, str(alpha)))
            plot_latency_vs_cache_size(resultset, topology, alpha, cache_sizes, strategies, plotdir)
    for cache_size in cache_sizes:
        for alpha in alphas:
            logger.info('Plotting cache hit ratio for cache size %s vs alpha %s against topologies' % (str(cache_size), str(alpha)))
            plot_cache_hits_vs_topology(resultset, alpha, cache_size, topologies, strategies, plotdir)
            logger.info('Plotting link load for cache size %s vs alpha %s against topologies' % (str(cache_size), str(alpha)))
            plot_link_load_vs_topology(resultset, alpha, cache_size, topologies, strategies, plotdir)
    logger.info('Exit. Plots were saved in directory %s' % os.path.abspath(plotdir))


def main():
    parser = argparse.ArgumentParser(__doc__)
    parser.add_argument("-r", "--results", dest="results",
                        help='the results file',
                        required=True)
    parser.add_argument("-o", "--output", dest="output",
                        help='the output directory where plots will be saved',
                        required=True)
    parser.add_argument("config",
                        help="the configuration file")
    args = parser.parse_args()
    run(args.config, args.results, args.output)


if __name__ == '__main__':
    main()
