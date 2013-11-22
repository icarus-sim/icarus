#!/usr/bin/env python
"""Plots results read from a resultset
"""
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

# This dict maps name of strategies to the style of the line to be used in the plots
# Off-path strategies: solid lines
# On-path strategies: dashed lines
# No-cache: dotted line
style_dict = {
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
legend_name = {
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
color_bar_graphs = {
    'LCE':          'k',
    'LCD':          '0.4',
    'NO_CACHE':     '0.5',
    'HR_ASYMM':     '0.6',
    'HR_SYMM':      '0.7'
    }

hatch_bar_graphs = {
    'LCE':          None,
    'LCD':          '//',
    'NO_CACHE':     'x',
    'HR_ASYMM':     '+',
    'HR_SYMM':      '\\'
    }


def main(config_file, results, output_dir):
    """Run the plot script
    """
    settings = Settings()
    settings.read_from(config_file)
    config_logging(settings.LOG_LEVEL)
    resultset = results_reader_register[settings.RESULTS_FORMAT](results)
    
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    
    topologies = settings.TOPOLOGIES
    cache_sizes = settings.NETWORK_CACHE
    alphas = settings.ALPHA
    strategies = settings.STRATEGIES
    
    for topology in topologies:
        for cache_size in cache_sizes:
            logger.info('Plotting cache hit ratio for topology %s and cache size %s vs alpha' % (topology, str(cache_size)))
            plot_cache_hits_vs_alpha(resultset, topology, cache_size, alphas, strategies, output_dir)
            logger.info('Plotting link load for topology %s vs cache size %s' % (topology, str(cache_size)))
            plot_link_load_vs_alpha(resultset, topology, cache_size, alphas, strategies, output_dir)

    for topology in topologies:
        for alpha in alphas:
            logger.info('Plotting cache hit ratio for topology %s and alpha %s vs cache size' % (topology, str(alpha)))
            plot_cache_hits_vs_cache_size(resultset, topology, alpha, cache_sizes, strategies, output_dir)
            logger.info('Plotting link load for topology %s and alpha %s vs cache size' % (topology, str(alpha)))
            plot_link_load_vs_cache_size(resultset, topology, alpha, cache_sizes, strategies, output_dir)

    for cache_size in cache_sizes:
        for alpha in alphas:
            logger.info('Plotting cache hit ratio for cache size %s vs alpha %s against topologies' % (str(cache_size), str(alpha)))
            plot_cache_hits_vs_topology(resultset, alpha, cache_size, topologies, strategies, output_dir)
            logger.info('Plotting link load for cache size %s vs alpha %s against topologies' % (str(cache_size), str(alpha)))
            plot_link_load_vs_topology(resultset, alpha, cache_size, topologies, strategies, output_dir)
    logger.info('Exit. Plots were saved in directory %s' % os.path.abspath(output_dir))
            
            
def plot_cache_hits_vs_alpha(resultset, topology, cache_size, alpha_range, strategies, output_dir):
    plt.figure()
    plt.title('Cache hit ratio: T=%s C=%s' % (topology, cache_size))
    plt.ylabel('Cache hit ratio')
    plt.xlabel(u'Content distribution \u03b1')
    for strategy in strategies:
        means = np.zeros(len(alpha_range))
        err = np.zeros(len(alpha_range))
        for i in range(len(alpha_range)):
            condition = {'alpha': alpha_range[i], 'network_cache': cache_size, 'strategy': strategy, 'topology_id': topology}
            data = [x[1]['CACHE_HIT_RATIO']['MEAN'] for x in resultset.filter(condition)]
            means[i], err[i] = means_confidence_interval(data, confidence=0.95)
        plt.errorbar(alpha_range, means, err, fmt=style_dict[strategy])
    plt.xlim(min(alpha_range), max(alpha_range))
    plt.legend([legend_name[s] for s in strategies], prop={'size': LEGEND_SIZE}, loc='upper left')
    plt.savefig(os.path.join(output_dir, 'CACHE_HIT_T=%s@C=%s.pdf' % (topology, cache_size)), bbox_inches='tight')
    

def plot_cache_hits_vs_cache_size(resultset, topology, alpha, cache_size_range, strategies, output_dir):
    plt.figure()
    plt.title('Cache hit ratio: T=%s A=%s' % (topology, alpha))
    plt.ylabel('Cache hit ratio')
    plt.xlabel(u'Cache to population ratio')
    for strategy in strategies:
        means = np.zeros(len(cache_size_range))
        err = np.zeros(len(cache_size_range))
        for i in range(len(cache_size_range)):
            condition = {'network_cache': cache_size_range[i], 'alpha': alpha, 'strategy': strategy, 'topology_id': topology}
            data = [x[1]['CACHE_HIT_RATIO']['MEAN'] for x in resultset.filter(condition)]
            means[i], err[i] = means_confidence_interval(data, confidence=0.95)
        plt.errorbar(cache_size_range, means, err, fmt=style_dict[strategy])
    plt.xlim(min(cache_size_range), max(cache_size_range))
    plt.legend([legend_name[s] for s in strategies], prop={'size': LEGEND_SIZE}, loc='upper left')
    plt.savefig(os.path.join(output_dir, 'CACHE_HIT_T=%s@A=%s.pdf' % (topology, alpha)), bbox_inches='tight')


def plot_link_load_vs_alpha(resultset, topology, cache_size, alpha_range, strategies, output_dir):
    plt.figure()
    plt.title('Internal link load: T=%s C=%s' % (topology, cache_size))
    plt.ylabel('Internal link load')
    plt.xlabel(u'Content distribution \u03b1')
    for strategy in strategies:
        means = np.zeros(len(alpha_range))
        err = np.zeros(len(alpha_range))
        for i in range(len(alpha_range)):
            condition = {'alpha': alpha_range[i], 'network_cache': cache_size, 'strategy': strategy, 'topology_id': topology}
            data = [x[1]['LINK_LOAD']['MEAN_INTERNAL'] for x in resultset.filter(condition)]
            means[i], err[i] = means_confidence_interval(data, confidence=0.95)
        plt.errorbar(alpha_range, means, err, fmt=style_dict[strategy])
    plt.xlim(min(alpha_range), max(alpha_range))
    plt.legend([legend_name[s] for s in strategies], prop={'size': LEGEND_SIZE}, loc='upper left')
    plt.savefig(os.path.join(output_dir, 'LINK_LOAD_INTERNAL_T=%s@C=%s.pdf' % (topology, cache_size)), bbox_inches='tight')


def plot_link_load_vs_cache_size(resultset, topology, alpha, cache_size_range, strategies, output_dir):
    plt.figure()
    plt.title('Internal link load: T=%s A=%s' % (topology, alpha))
    plt.ylabel('Internal link load')
    plt.xlabel(u'Cache to population ratio')
    for strategy in strategies:
        means = np.zeros(len(cache_size_range))
        err = np.zeros(len(cache_size_range))
        for i in range(len(cache_size_range)):
            condition = {'network_cache': cache_size_range[i], 'alpha': alpha, 'strategy': strategy, 'topology_id': topology}
            data = [x[1]['LINK_LOAD']['MEAN_INTERNAL'] for x in resultset.filter(condition)]
            means[i], err[i] = means_confidence_interval(data, confidence=0.95)
        plt.errorbar(cache_size_range, means, err, fmt=style_dict[strategy])
    plt.xlim(min(cache_size_range), max(cache_size_range))
    plt.legend([legend_name[s] for s in strategies], prop={'size': LEGEND_SIZE}, loc='upper left')
    plt.savefig(os.path.join(output_dir, 'LINK_LOAD_INTERNAL_T=%s@A=%s.pdf' % (topology, alpha)), bbox_inches='tight')


def plot_cache_hits_vs_topology(resultset, alpha, cache_size, topology_range, strategies, output_dir):
    """
    Plot bar graphs of cache hit ratio for specific values of alpha and cache
    size for various topologies.
    
    The objective here is to show that our algorithms works well on all
    topologies considered
    """    
    plt.figure()
    plt.title('Cache hit ratio: A=%s C=%s' % (alpha, cache_size))
    plt.subplot(111)
    plt.grid(b=True, which='major', color='k', axis='y', linestyle='--')
    plt.ylabel('Cache hit ratio')
    width = 0.15        # the width of the bars
    left = 0.15         # offset left of first bar
    offset = 0
    elem = collections.defaultdict(int)     # bar objects (for legend)
    
    for strategy in strategies:
        for i in range(len(topology_range)):
            condition = {'topology_id': topology_range[i], 'alpha': alpha, 'strategy': strategy, 'network_cache': cache_size}
            data = [x[1]['CACHE_HIT_RATIO']['MEAN'] for x in resultset.filter(condition)]
            meanval, err = means_confidence_interval(data, confidence=0.95)    
            elem[strategy] = plt.bar(left + i + offset, meanval, width,
                                     color=color_bar_graphs[strategy],
                                     yerr=err,ecolor='k',
                                     hatch=hatch_bar_graphs[strategy],
                                     label=strategy)
        offset += width
    plt.xticks(left + np.arange(len(topology_range)) + 0.5*len(strategies)*width, topology_range)
    plt.legend([elem[x] for x in strategies], [legend_name[s] for s in strategies], prop={'size': LEGEND_SIZE}, loc='lower right')
    xmin, _ = plt.xlim()
    plt.xlim(xmin, left + len(topology_range) - 1 + len(strategies)*width + left)
    plt.savefig(os.path.join(output_dir, 'CACHE_HIT_RATIO_A=%s_C=%s.pdf' % (alpha, cache_size)), bbox_inches='tight')


def plot_link_load_vs_topology(resultset, alpha, cache_size, topology_range, strategies, output_dir):
    """
    Plot bar graphs of link load for specific values of alpha and cache
    size for various topologies.
    
    The objective here is to show that our algorithms works well on all
    topologies considered
    """
    plt.figure()
    plt.title('Internal link load: A=%s C=%s' % (alpha, cache_size))
    plt.subplot(111)
    plt.grid(b=True, which='major', color='k', axis='y', linestyle='--')
    plt.ylabel('Internal link load')
    width = 0.15        # the width of the bars
    left = 0.15         # offset left of first bar
    offset = 0
    elem = collections.defaultdict(int)     # bar objects (for legend)
    
    for strategy in strategies:
        for i in range(len(topology_range)):
            condition = {'topology_id': topology_range[i], 'alpha': alpha,
                         'strategy': strategy, 'network_cache': cache_size}
            data = [x[1]['LINK_LOAD']['MEAN_INTERNAL'] 
                    for x in resultset.filter(condition)]
            meanval, err = means_confidence_interval(data, confidence=0.95)    
            elem[strategy] = plt.bar(left + i + offset, meanval, width,
                                     color=color_bar_graphs[strategy],
                                     yerr=err, ecolor='k',
                                     hatch=hatch_bar_graphs[strategy],
                                     label=strategy)
        offset += width
    plt.xticks(left + np.arange(len(topology_range)) + 0.5*len(strategies)*width,topology_range)
    plt.legend([elem[x] for x in strategies], [legend_name[s] for s in strategies], prop={'size': LEGEND_SIZE}, loc='lower right')
    xmin, _ = plt.xlim()
    plt.xlim(xmin, left + len(topology_range) - 1 + len(strategies)*width + left)
    plt.savefig(os.path.join(output_dir, 'LINK_LOAD_INTERNAL_A=%s_C=%s.pdf' % (alpha, cache_size)), bbox_inches='tight')



if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument("-r", "--results", dest="results",
                        help='The results file',
                        required=False)
    parser.add_argument("-o", "--output", dest="output",
                        help='The output directory where plots will be saved',
                        required=False)
    parser.add_argument("config_file",
                        help="The simulation configuration file")
    args = parser.parse_args()
    main(args.config_file, args.results, args.output)

