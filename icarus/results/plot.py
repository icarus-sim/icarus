#!/usr/bin/env python
"""Plot results read from a resultset
"""
from __future__ import division
import os
import argparse
import collections
import logging

import numpy as np
import matplotlib.pyplot as plt

from icarus.util import Settings, config_logging
from icarus.tools import means_confidence_interval
from icarus.registry import results_reader_register


# Logger object
logger = logging.getLogger('plot')

# These lines prevent insertion of Type 3 fonts in figures
# Publishers don't want them
plt.rcParams['ps.useafm'] = True
plt.rcParams['pdf.use14corefonts'] = True
plt.rcParams['text.usetex'] = True

# Aspect ratio of the output figures
plt.rcParams['figure.figsize'] = 8, 4.5

# Size of font in legends
LEGEND_SIZE = 11

# Plot
PLOT_EMPTY_GRAPHS = False

# Catalogue of possible bw shades (for bar charts)
BW_COLOR_CATALOGUE = ['k', '0.2', '0.3', '0.4', '0.5', '0.6', '0.7', '0.8', '0.9']

# Catalogue of possible hatch styles (for bar charts)
HATCH_CATALOGUE = [None, '/', '\\', '\\\\', '//', '+', 'x', '*', 'o', '.',  '|', '-',  'O']

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
    desc = {}
    desc['title'] = 'Cache hit ratio: T=%s C=%s' % (topology, cache_size)
    desc['ylabel'] = 'Cache hit ratio'
    desc['xlabel'] = u'Content distribution \u03b1'
    desc['yparam'] = 'strategy_name'
    desc['yvals'] = strategies
    desc['xparam'] = 'alpha'
    desc['xvals'] = alpha_range
    desc['filter'] = dict(topology_name=topology, network_cache=cache_size)
    desc['metric'] = ('CACHE_HIT_RATIO', 'MEAN')
    desc['errorbar'] = True
    desc['legend_loc'] = 'upper left'
    desc['line_style'] = STRATEGY_STYLE
    desc['legend'] = STRATEGY_LEGEND
    desc['plotempty'] = PLOT_EMPTY_GRAPHS
    if 'NO_CACHE' in desc['yvals']:
        desc['yvals'].remove('NO_CACHE')
    plot_lines(resultset, desc, 'CACHE_HIT_RATIO_T=%s@C=%s.pdf'
               % (topology, cache_size), plotdir)


def plot_cache_hits_vs_cache_size(resultset, topology, alpha, cache_size_range, strategies, plotdir):
    desc = {}
    desc['title'] = 'Cache hit ratio: T=%s A=%s' % (topology, alpha)
    desc['xlabel'] = u'Cache to population ratio'
    desc['ylabel'] = 'Cache hit ratio'
    desc['xscale'] = 'log'
    desc['yparam'] = 'strategy_name'
    desc['yvals'] = strategies
    desc['xparam'] = 'network_cache'
    desc['xvals'] = cache_size_range
    desc['filter'] = dict(topology_name=topology, alpha=alpha)
    desc['metric'] = ('CACHE_HIT_RATIO', 'MEAN')
    desc['errorbar'] = True
    desc['legend_loc'] = 'upper left'
    desc['line_style'] = STRATEGY_STYLE
    desc['legend'] = STRATEGY_LEGEND
    desc['plotempty'] = PLOT_EMPTY_GRAPHS
    if 'NO_CACHE' in desc['yvals']:
        desc['yvals'].remove('NO_CACHE')
    plot_lines(resultset, desc,'CACHE_HIT_RATIO_T=%s@A=%s.pdf'
               % (topology, alpha), plotdir)
    

def plot_link_load_vs_alpha(resultset, topology, cache_size, alpha_range, strategies, plotdir):
    desc = {}
    desc['title'] = 'Internal link load: T=%s C=%s' % (topology, cache_size)
    desc['xlabel'] = u'Content distribution \u03b1'
    desc['ylabel'] = 'Internal link load'
    desc['yparam'] = 'strategy_name'
    desc['yvals'] = strategies
    desc['xparam'] = 'alpha'
    desc['xvals'] = alpha_range
    desc['filter'] = dict(topology_name=topology, network_cache=cache_size)
    desc['metric'] = ('LINK_LOAD', 'MEAN_INTERNAL')
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
    desc['yparam'] = 'strategy_name'
    desc['yvals'] = strategies
    desc['xparam'] = 'network_cache'
    desc['xvals'] = cache_size_range
    desc['filter'] = dict(topology_name=topology, alpha=alpha)
    desc['metric'] = ('LINK_LOAD', 'MEAN_INTERNAL')
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
    desc['yparam'] = 'strategy_name'
    desc['yvals'] = strategies
    desc['xparam'] = 'alpha'
    desc['xvals'] = alpha_range
    desc['filter'] = dict(topology_name=topology, network_cache=cache_size)
    desc['metric'] = ('LATENCY', 'MEAN')
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
    desc['yparam'] = 'strategy_name'
    desc['yvals'] = strategies
    desc['xparam'] = 'network_cache'
    desc['xvals'] = cache_size_range
    desc['filter'] = dict(topology_name=topology, alpha=alpha)
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
    desc = {}
    desc['title'] = 'Cache hit ratio: A=%s C=%s' % (alpha, cache_size)
    desc['ylabel'] = 'Cache hit ratio'
    desc['yparam'] = 'strategy_name'
    desc['yvals'] = strategies
    desc['xparam'] = 'topology_name'
    desc['xvals'] = topology_range
    desc['filter'] = dict(alpha=alpha, network_cache=cache_size)
    desc['metric'] = ('CACHE_HIT_RATIO', 'MEAN')
    desc['errorbar'] = True
    desc['legend_loc'] = 'lower right'
    desc['bar_color'] = STRATEGY_BAR_COLOR
    desc['bar_hatch'] = STRATEGY_BAR_HATCH
    desc['legend'] = STRATEGY_LEGEND
    desc['plotempty'] = PLOT_EMPTY_GRAPHS
    if 'NO_CACHE' in desc['yvals']:
        desc['yvals'].remove('NO_CACHE')
    plot_bar_graph(resultset, desc, 'CACHE_HIT_RATIO_A=%s_C=%s.pdf'
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
    desc['yparam'] = 'strategy_name'
    desc['yvals'] = strategies
    desc['xparam'] = 'topology_name'
    desc['xvals'] = topology_range
    desc['filter'] = dict(alpha=alpha, network_cache=cache_size)
    desc['metric'] = ('LINK_LOAD', 'MEAN_INTERNAL')
    desc['errorbar'] = True
    desc['legend_loc'] = 'lower right'
    desc['bar_color'] = STRATEGY_BAR_COLOR
    desc['bar_hatch'] = STRATEGY_BAR_HATCH
    desc['legend'] = STRATEGY_LEGEND
    desc['plotempty'] = PLOT_EMPTY_GRAPHS
    plot_bar_graph(resultset, desc, 'LINK_LOAD_INTERNAL_A=%s_C=%s.pdf'
                   % (alpha, cache_size), plotdir)


    
def plot_lines(resultset, desc, filename, plotdir):
    """Plot a graph with characteristics described in the plot descriptor out
    of the data contained in the resultset and save the plot in given directory.
    
    Parameters
    ----------
    rs : ResultSet
        Result set
    desc : dict
        The plot descriptor (more info below)
    filename : str
        The name used to save the file. The file format is determined by the
        extension of the file. For example, if this filename is 'foo.pdf', the
        file will be saved in pdf format.
    plotdir : str
        The directory in which the plot will be saved.
    
    Notes
    -----
    The plot descriptor is a dictionary with a set of values that describe how
    to make the plot.
    
    The dictionary can contain the following keys:
     * title : str, optional.
           The title of the graph
     * xlabel : str, optional
         The x label
     * ylabel : str, optional
         The y label
     * errorbar : bool, optional
         If *True* error bars will be plotted. Default value is *True*
     * confidence : float, optional
         The confidence used to plot error bars. Default value is 0.95
     * metric : tuple
         A tuple of 2-values representing the metric to plot.
         The first value is the name of the collector which measured the metric
         and the second value is the metric name. Example values could
         ('CACHE_HIT_RATIO', 'MEAN'), ('LINK_LOAD', 'MEAN_INTERNAL') or 
         ('LATENCY', 'MEAN')
     * filter : dict
         A dictionary of values to filter in the resultset.
         Example: {'network_cache': 0.004, 'topology_name': 'GEANT'}
     * xparam : str
         The name of the x axis metric, e.g. 'alpha'
     * xvals : list
         Range of x values, e.g. [0.6, 0.7, 0.8, 0.9]
     * yparam : str
         The name of the y metric, e.g. 'strategy'
     * yvals : list
         List of lines plotted. For example. if yparam = 'strategy_name', then
         a valid yvals value could be ['HR_SYMM', 'HR_ASYMM']
     * xscale : str, optional
         The scale of x axis. Options allowed are 'linear' and 'log'. 
         Default value is 'linear'
     * yscale : str, optional
         The scale of y axis. Options allowed are 'linear' and 'log'.
         Default value is 'linear'
     * legend_loc : str
         Legend location, e.g. 'upper left'
     * line_style : dict, optional
         Dictionary mapping each value of yvals with a line style
     * legend : dict, optional
         Dictionary mapping each value of yvals with a legend label
     * plotempty : bool, optional
         If *True*, plot and save graph even if empty. Default is *True* 
    """
    plt.figure()
    if 'title' in desc:
        plt.title(desc['title'])
    if 'xlabel' in desc:
        plt.xlabel(desc['xlabel'])
    if 'ylabel' in desc:
        plt.ylabel(desc['ylabel'])
    if 'xscale' in desc:
        plt.xscale(desc['xscale'])
    if 'yscale' in desc:
        plt.yscale(desc['yscale'])
    xvals = sorted(desc['xvals'])
    plot_empty = desc['plotempty'] if 'plotempty' in desc else True
    empty = True
    for l in desc['yvals']:
        means = np.zeros(len(xvals))
        err = np.zeros(len(xvals))
        for i in range(len(xvals)):
            condition = dict(list(desc['filter'].items()) + \
                             [(desc['xparam'], xvals[i]),
                              (desc['yparam'], l)])
            data = [x[1][desc['metric'][0]][desc['metric'][1]]
                    for x in resultset.filter(condition)]
            confidence = desc['confidence'] if 'confidence' in desc else 0.95 
            means[i], err[i] = means_confidence_interval(data, confidence)
        yerr = None if 'errorbar' in desc and not desc['errorbar'] else err
        fmt = desc['line_style'][l] if 'line_style' in desc \
              and l in desc['line_style'] else '-'
        # This check is to prevent crashing when trying to plot arrays of nan
        # values with axes log scale
        if all(np.isnan(x) for x in xvals) or all(np.isnan(y) for y in means):
            plt.errorbar([], [], fmt=fmt)
        else:
            plt.errorbar(xvals, means, yerr=yerr, fmt=fmt)
            empty = False
    if empty and not plot_empty:
        return
    plt.xlim(min(xvals), max(xvals))
    legend = [desc['legend'][l] for l in desc['yvals']] if 'legend'in desc \
             else desc['yvals']
    plt.legend(legend, prop={'size': LEGEND_SIZE}, loc=desc['legend_loc'])
    plt.savefig(os.path.join(plotdir, filename), bbox_inches='tight')


def plot_bar_graph(resultset, desc, filename, plotdir):
    """Plot a bar chart with characteristics described in the plot descriptor
    out of the data contained in the resultset and save the plot in given
    directory.
    
    Parameters
    ----------
    rs : ResultSet
        Result set
    desc : dict
        The plot descriptor (more info below)
    filename : str
        The name used to save the file. The file format is determined by the
        extension of the file. For example, if this filename is 'foo.pdf', the
        file will be saved in pdf format.
    plotdir : str
        The directory in which the plot will be saved.
    
    Notes
    -----
    The plot descriptor is a dictionary with a set of values that describe how
    to make the plot.
    
    The dictionary can contain the following keys:
     * title : str, optional.
           The title of the graph
     * xlabel : str, optional
         The x label
     * ylabel : str, optional
         The y label
     * errorbar : bool, optional
         If *True* error bars will be plotted. Default value is *True*
     * confidence : float, optional
         The confidence used to plot error bars. Default value is 0.95
     * metric : tuple
         A tuple of 2-values representing the metric to plot.
         The first value is the name of the collector which measured the metric
         and the second value is the metric name. Example values could
         ('CACHE_HIT_RATIO', 'MEAN'), ('LINK_LOAD', 'MEAN_INTERNAL') or 
         ('LATENCY', 'MEAN')
     * filter : dict
         A dictionary of values to filter in the resultset.
         Example: {'network_cache': 0.004, 'topology_name': 'GEANT'}
     * xparam : str
         The name of the x axis metric, e.g. 'alpha'
     * xvals : list
         Range of x values, e.g. [0.6, 0.7, 0.8, 0.9]
     * yparam : str
         The name of the y metric, e.g. 'strategy'
     * yvals : list
         List of lines plotted. For example. if yparam = 'strategy_name', then
         a valid yvals value could be ['HR_SYMM', 'HR_ASYMM']
     * legend_loc : str
         Legend location, e.g. 'upper left'
     * bar_color : dict, optional
         Dictionary mapping each value of yvals with a bar color
     * bar_hatch : dict, optional
         Dictionary mapping each value of yvals with a bar hatch
     * legend : dict, optional
         Dictionary mapping each value of yvals with a legend label
     * plotempty : bool, optional
         If *True*, plot and save graph even if empty. Default is *True*
    """
    plt.figure()
    if 'title' in desc:
        plt.title(desc['title'])
    plt.subplot(111)
    plt.grid(b=True, which='major', color='k', axis='y', linestyle='--')
    if 'xlabel' in desc:
        plt.xlabel(desc['xlabel'])
    if 'ylabel' in desc:
        plt.ylabel(desc['ylabel'])
    plot_empty = desc['plotempty'] if 'plotempty' in desc else True
    empty = True
    # Spacing attributes
    GROUP_WIDTH = 0.4                           # width of a group of bars 
    WIDTH = GROUP_WIDTH/len(desc['yvals'])      # width of a single bar
    SEPARATION = WIDTH/2                        # space between adjacent groups
    BORDER = 0.6 * SEPARATION                   # left and right borders
        
    elem = collections.defaultdict(int)         # bar objects (for legend)
    # Select colors and hatches
    yvals = list(desc['yvals'])
    if 'bar_color' in desc and all(y in desc['bar_color'] for y in yvals):
        color = desc['bar_color']
    elif len(yvals) <= len(BW_COLOR_CATALOGUE):
        color = dict((y, BW_COLOR_CATALOGUE[yvals.index(y)]) for y in yvals)
    else:
        color = collections.defaultdict(lambda: None)
    if 'bar_hatch' in desc and all(y in desc['bar_hatch'] for y in yvals):
        hatch = desc['bar_hatch']
    elif len(yvals) <= len(BW_COLOR_CATALOGUE):
        hatch = dict((y, HATCH_CATALOGUE[yvals.index(y)]) for y in yvals)
    else:
        hatch = collections.defaultdict(lambda: None)
    # Plot bars
    left = BORDER       # left-most point of the bar about to draw
    for i in range(len(desc['xvals'])):
        for l in desc['yvals']:
            condition = dict(list(desc['filter'].items()) + \
                             [(desc['xparam'], desc['xvals'][i]),
                              (desc['yparam'], l)])
            data = [x[1][desc['metric'][0]][desc['metric'][1]]
                    for x in resultset.filter(condition)]
            confidence = desc['confidence'] if 'confidence' in desc else 0.95 
            meanval, err = means_confidence_interval(data, confidence)
            yerr = None if 'errorbar' in desc and not desc['errorbar'] else err
            if not np.isnan(meanval):
                empty = False
            elem[l] = plt.bar(left, meanval, WIDTH, color=color[l], 
                              yerr=yerr, ecolor='k', hatch=hatch[l], label=l)
            left += WIDTH
        left += SEPARATION
    if empty and not plot_empty:
        return
    plt.xticks(BORDER + 0.5*(len(desc['yvals'])*WIDTH) + 
               (SEPARATION + len(desc['yvals'])*WIDTH)*np.arange(len(desc['xvals'])),
               desc['xvals'])
    legend = [desc['legend'][l] for l in desc['yvals']] if 'legend'in desc \
             else desc['yvals']
    plt.legend([elem[x] for x in desc['yvals']], legend,
               prop={'size': LEGEND_SIZE}, loc=desc['legend_loc'])
    xmin, _ = plt.xlim()
    plt.xlim(xmin, left - SEPARATION + BORDER)
    plt.savefig(os.path.join(plotdir, filename), bbox_inches='tight')


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
    resultset = results_reader_register[settings.RESULTS_FORMAT](results)
    # Create dir if not existsing
    if not os.path.exists(plotdir):
        os.makedirs(plotdir)
    # Parse params from settings
    topologies = settings.TOPOLOGIES
    cache_sizes = settings.NETWORK_CACHE
    alphas = settings.ALPHA
    strategies = settings.STRATEGIES
    #Plot graphs
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
