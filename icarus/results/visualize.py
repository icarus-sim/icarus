"""Functions for visualizing results on graphs of topologies"""
from __future__ import division
import os

import numpy as np
import matplotlib as mpl
import matplotlib.pyplot as plt
import networkx as nx


__all__ = [
       'draw_stack_deployment',
       'draw_network_load',
          ]


# Colormap for node stacks
COLORMAP = {'source':    'blue',
            'receiver':  'green',
            'router':    'white',
            'cache':     'red',
            }


def stack_map(topology):
    """Return dict mapping node ID to stack type

    Parameters
    ----------
    topology : Topology
        The topology

    Returns
    -------
    stack_map : dict
        Dict mapping node to stack. Options are:
        source | receiver | router | cache
    """
    stack = {}
    for v, (name, props) in topology.stacks().items():
        if name == 'router':
            cache = False
            if 'cache_size' in props and props['cache_size'] > 0:
                cache = True
            elif cache:
                name = 'cache'
            else:
                name = 'router'
        stack[v] = name
    return stack


def draw_stack_deployment(topology, filename, plotdir):
    """Draw a topology with different node colors according to stack

    Parameters
    ----------
    topology : Topology
        The topology to draw
    plotdir : string
        The directory onto which draw plots
    filename : string
        The name of the image file to save
    """
    stack = stack_map(topology)
    node_color = [COLORMAP[stack[v]] for v in topology.nodes_iter()]
    plt.figure()
    nx.draw_graphviz(topology, node_color=node_color, with_labels=False)
    plt.savefig(os.path.join(plotdir, filename), bbox_inches='tight')


def draw_network_load(topology, result, filename, plotdir):
    """Draw topology with node colors according to stack and node size and link
    color according to server/cache hits and link loads.

    Nodes are colored according to COLORMAP. Edge are colored on a blue-red
    scale where blue means min link load and red means max link load.
    Sources and caches have variable size proportional to their hit ratios.

    Parameters
    ----------
    topology : Topology
        The topology to draw
    result : Tree
        The tree representing the specific experiment result from which metric
        are read
    plotdir : string
        The directory onto which draw plots
    filename : string
        The name of the image file to save
    """
    stack = stack_map(topology)
    node_color = [COLORMAP[stack[v]] for v in topology.nodes_iter()]
    node_min = 50
    node_max = 600
    hits = result['CACHE_HIT_RATIO']['PER_NODE_CACHE_HIT_RATIO'].copy()
    hits.update(result['CACHE_HIT_RATIO']['PER_NODE_SERVER_HIT_RATIO'])
    hits = np.array([hits[v] if v in hits else 0 for v in topology.nodes_iter()])
    min_hits = np.min(hits)
    max_hits = np.max(hits)
    hits = node_min + (node_max - node_min) * (hits - min_hits) / (max_hits - min_hits)
    link_load = result['LINK_LOAD']['PER_LINK_INTERNAL'].copy()
    link_load.update(result['LINK_LOAD']['PER_LINK_EXTERNAL'])
    link_load = [link_load[e] if e in link_load else 0 for e in topology.edges()]
    plt.figure()
    nx.draw_graphviz(topology, node_color=node_color, node_size=hits,
                     width=2.0,
                     edge_color=link_load,
                     edge_cmap=mpl.colors.LinearSegmentedColormap.from_list('bluered', ['blue', 'red']),
                     with_labels=False)
    plt.savefig(os.path.join(plotdir, filename), bbox_inches='tight')
