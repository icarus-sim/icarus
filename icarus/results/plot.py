#!/usr/bin/env python
"""Plot results read from a result set
"""
from __future__ import division
import os
import collections

import numpy as np
import matplotlib
import matplotlib.pyplot as plt

from icarus.util import Tree, step_cdf
from icarus.tools import means_confidence_interval


__all__ = ['plot_lines', 'plot_bar_chart', 'plot_cdf']


# These lines prevent insertion of Type 3 fonts in figures
# Publishers don't want them. However, in some case these commands block the
# embedding of fonts raising complaints for example from EDAS
# plt.rcParams['ps.useafm'] = True
# plt.rcParams['pdf.use14corefonts'] = True

# If True text is interpreted as LaTeX, e.g. underscore are interpreted as
# subscript. If False, text is interpreted literally
plt.rcParams['text.usetex'] = False

# Aspect ratio of the output figures
plt.rcParams['figure.figsize'] = 8, 5

# Size of font in legends
LEGEND_SIZE = 14

# Plot
PLOT_EMPTY_GRAPHS = False

# Catalogue of possible bw shades (for bar charts)
BW_COLOR_CATALOGUE = ['k', '0.2', '0.3', '0.4', '0.5', '0.6', '0.7', '0.8', '0.9']

# Catalogue of possible hatch styles (for bar charts)
HATCH_CATALOGUE = [None, '/', '\\', '\\\\', '//', '+', 'x', '*', 'o', '.', '|', '-', 'O']


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
     * xparam : iterable
         Path to the value of the x axis metric, e.g. ['workload', 'alpha']
     * xvals : list
         Range of x values, e.g. [0.6, 0.7, 0.8, 0.9]
     * filter : dict, optional
         A dictionary of values to filter in the resultset.
         Example: {'network_cache': 0.004, 'topology_name': 'GEANT'}
         If not specified or None, no filtering is executed on the results
         and possibly heterogeneous results may be plotted together
     * ymetrics : list of tuples
         List of metrics to be shown on the graph. The i-th metric of the list
         is the metric that the i-th line on the graph will represent. If
         all lines are for the same metric, then all elements of the list are
         equal.
         Each single metric (i.e. each element of the list) is a tuple modeling
         the path to identify a specific metric into an entry of a result set.
         Normally, it is a 2-value list where the first value is the name of
         the collector which measured the metric and the second value is the
         metric name. Example values could be ('CACHE_HIT_RATIO', 'MEAN'),
         ('LINK_LOAD', 'MEAN_INTERNAL') or ('LATENCY', 'MEAN').
         For example, if in a graph of N lines all lines of the graph show mean
         latency, then ymetrics = [('LATENCY', 'MEAN')]*5.
     * ycondnames : list of tuples, optional
         List of condition names specific to each line of the graph. Different
         from the conditions expressed in the filter parameter, which are
         global, these conditions are specific to one bar. Ech condition name,
         different from the filter parameter is a path to a condition to be
         checked, e.g. ('topology', 'name'). Values to be matched for this
         conditions are specified in ycondvals. This list must be as long as
         the number of lines to plot. If not specified, all lines are filtered
         by the conditions of filter parameter only, but in this case all
         ymetrics should be different.
     * ycondvals : list of tuples, optional
         List of values that the conditions of ycondnames must meet. This list
         must be as long as the number of lines to plot. If not specified,
         all lines are filtered by the conditions of filter parameter only,
         but in this case all ymetrics should be different.
     * xscale : ('linear' | 'log'), optional
         The scale of x axis. Default value is 'linear'
     * yscale : ('linear' | 'log'), optional
         The scale of y axis. Default value is 'linear'
     * xticks : list, optional
         Values to display as x-axis ticks.
     * yticks : list, optional
         Values to display as y-axis ticks.
     * line_style : dict, optional
         Dictionary mapping each value of yvals with a line style
     * plot_args : dict, optional
         Additional args to be provided to the Pyplot errorbar function.
         Example parameters that can be specified here are *linewidth* and
         *elinewidth*
     * legend : dict, optional
         Dictionary mapping each value of yvals with a legend label. If not
         specified, it is not plotted. If you wish to plot it with the
         name of the line, set it to put yvals or ymetrics, depending on which
         one is used
     * legend_loc : str, optional
         Legend location, e.g. 'upper left'
     * legend_args : dict, optional
         Optional legend arguments, such as ncol
     * plotempty : bool, optional
         If *True*, plot and save graph even if empty. Default is *True*
     * xmin, xmax: float, optional
        The limits of the x axis. If not specified, they're set to the min and
        max values of xvals
     * ymin, ymax: float, optional
        The limits of the y axis. If not specified, they're automatically
        selected by Matplotlib
    """
    fig = plt.figure()
    _, ax1 = plt.subplots()
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
    if 'filter' not in desc or desc['filter'] is None:
        desc['filter'] = {}
    xvals = sorted(desc['xvals'])
    if 'xticks' in desc:
        ax1.set_xticks(desc['xticks'])
        ax1.get_xaxis().set_major_formatter(matplotlib.ticker.ScalarFormatter())
        ax1.set_xticklabels([str(xtick) for xtick in desc['xticks']])
    if 'yticks' in desc:
        ax1.set_yticks(desc['yticks'])
        ax1.get_yaxis().set_major_formatter(matplotlib.ticker.ScalarFormatter())
        ax1.set_yticklabels([str(ytick) for ytick in desc['yticks']])
    ymetrics = desc['ymetrics']
    ycondnames = desc['ycondnames'] if 'ycondnames' in desc else None
    ycondvals = desc['ycondvals'] if 'ycondvals' in desc else None
    if ycondnames is not None and ycondvals is not None:
        if not len(ymetrics) == len(ycondnames) == len(ycondvals):
            raise ValueError('ymetrics, ycondnames and ycondvals must have the same length')
        # yvals is basically the list of values that differentiate each line
        # it is used for legends and styles mainly
        yvals = ycondvals if len(set(ymetrics)) == 1 else zip(ymetrics, ycondvals)
    else:
        yvals = ymetrics
    plot_args = desc['plot_args'] if 'plot_args' in desc else {}
    plot_empty = desc['plotempty'] if 'plotempty' in desc else True
    empty = True
    for i in range(len(yvals)):
        means = np.zeros(len(xvals))
        err = np.zeros(len(xvals))
        for j in range(len(xvals)):
            condition = Tree(desc['filter'])
            condition.setval(desc['xparam'], xvals[j])
            if ycondnames is not None:
                condition.setval(ycondnames[i], ycondvals[i])
            data = [v.getval(ymetrics[i])
                    for _, v in resultset.filter(condition)
                    if v.getval(ymetrics[i]) is not None]
            confidence = desc['confidence'] if 'confidence' in desc else 0.95
            means[j], err[j] = means_confidence_interval(data, confidence)
        yerr = None if 'errorbar' in desc and not desc['errorbar'] or all(err == 0) else err
        fmt = desc['line_style'][yvals[i]] if 'line_style' in desc \
              and yvals[i] in desc['line_style'] else '-'
        # This check is to prevent crashing when trying to plot arrays of nan
        # values with axes log scale
        if all(np.isnan(x) for x in xvals) or all(np.isnan(y) for y in means):
            plt.errorbar([], [], fmt=fmt)
        else:
            plt.errorbar(xvals, means, yerr=yerr, fmt=fmt, **plot_args)
            empty = False
    if empty and not plot_empty:
        return
    x_min = desc['xmin'] if 'xmin' in desc else min(xvals)
    x_max = desc['xmax'] if 'xmax' in desc else max(xvals)
    plt.xlim(x_min, x_max)
    if 'ymin' in desc:
        plt.ylim(ymin=desc['ymin'])
    if 'ymax' in desc:
        plt.ylim(ymax=desc['ymax'])
    if 'legend' in desc:
        legend = [desc['legend'][l] for l in yvals]
        legend_args = desc['legend_args'] if 'legend_args' in desc else {}
        if 'legend_loc' in desc:
            legend_args['loc'] = desc['legend_loc']
        plt.legend(legend, prop={'size': LEGEND_SIZE}, **legend_args)
    plt.savefig(os.path.join(plotdir, filename), bbox_inches='tight')
    plt.close(fig)


def plot_bar_chart(resultset, desc, filename, plotdir):
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
     * filter : tree or dict of dicts, optional
         A tree or nested dictionary of values to include from the resultset.
         Example: {'cache_placement': {'network_cache': 0.004},
         'topology': {'name', 'GEANT'}}.
         If not specified or None, no filtering is executed on the results
         and possibly heterogeneous results may be plotted together.
     * xparam : tuple
         The path of the x axis metric, e.g. ('workload', 'alpha')
     * xvals : list
         Range of x values, e.g. [0.6, 0.7, 0.8, 0.9]
     * xticks : list, optional
         Names to display as ticks. If not specified, xvals is used instead
     * ymetrics : list of tuples
         List of metrics to be shown on the graph. The i-th metric of the list
         is the metric that the i-th bar on the graph will represent. If
         all bars are for the same metric, then all elements of the list are
         equal.
         Each single metric (i.e. each element of the list) is a tuple modeling
         the path to identify a specific metric into an entry of a result set.
         Normally, it is a 2-value list where the first value is the name of
         the collector which measured the metric and the second value is the
         metric name. Example values could be ('CACHE_HIT_RATIO', 'MEAN'),
         ('LINK_LOAD', 'MEAN_INTERNAL') or ('LATENCY', 'MEAN').
         For example, if in a graph of N bars all bar of the graph show mean
         latency, then ymetrics = [('LATENCY', 'MEAN')]*5.
     * ycondnames : list of tuples, optional
         List of condition names specific to each bar of the graph. Different
         from the conditions expressed in the filter parameter, which are
         global, these conditions are specific to one bar. Ech condition name,
         different from the filter parameter is a path to a condition to be
         checked, e.g. ('topology', 'name'). Values to be matched for this
         conditions are specified in ycondvals. This list must be as long as
         the number of bars to plot. If not specified, all bars are filtered
         by the conditions of filter parameter only, but in this case all
         ymetrics should be different.
     * ycondvals : list of values, optional
         List of values that the conditions of ycondnames must meet. This list
         must be as long as the number of bars to plot. If not specified,
         all bars are filtered by the conditions of filter parameter only,
         but in this case all ymetrics should be different.
     * placement : (grouped | stacked | [x, y, ...])
         Defines how to place bars in the plot. If grouped, defaults, all
         bars for a specific xval are grouped next to each other, if stacked,
         they are plot on top of each other. It is also possible to specify a
         custom grouped+stacked placement with a list of integers, in which
         the number of items is the number of columns and the actual value of
         an items is the number of metrics stacked on the column. For example
         [4,2,3] means plotting 4 + 2 + 3 = 9 metrics: 4 stacked in the first
         column, 2 stacked on the second and 3 stacked on the third
         If *True*, draw all bars of a group stacked on top of each other.
         Default value is *False*.
     * group_width : float, default: 0.4
         Width of a group of bars
     * bar_color : dict, optional
         Dictionary mapping each value of yvals with a bar color
     * bar_hatch : dict, optional
         Dictionary mapping each value of yvals with a bar hatch. If set to
         None all bars will be plotted without hatch. If not set, hatches will
         be plotted randomly
     * legend : dict, optional
         Dictionary mapping each value of yvals with a legend label. If not
         specified, it is not plotted. If you wish to plot it with the
         name of the line, set it to put yvals or ymetrics, depending on which
         one is used
     * legend_loc : str, optional
         Legend location, e.g. 'upper left'
     * legend_args : dict, optional
         Optional legend arguments, such as ncol
     * plotempty : bool, optional
         If *True*, plot and save graph even if empty. Default is *True*
     * ymax: float, optional
        The upper limit of the y axis. If not specified, it is automatically
        selected by Matplotlib
    """
    fig = plt.figure()
    if 'title' in desc:
        plt.title(desc['title'])
    _, ax1 = plt.subplots()
    plt.grid(b=True, which='major', color='k', axis='y', linestyle=':')
    # Set axis below bars
    ax1.set_axisbelow(True)
    if 'xlabel' in desc:
        plt.xlabel(desc['xlabel'])
    if 'ylabel' in desc:
        plt.ylabel(desc['ylabel'])
    if 'filter' not in desc or desc['filter'] is None:
        desc['filter'] = {}
    plot_empty = desc['plotempty'] if 'plotempty' in desc else True

    ymetrics = desc['ymetrics']
    ycondnames = desc['ycondnames'] if 'ycondnames' in desc else None
    ycondvals = desc['ycondvals'] if 'ycondvals' in desc else None
    if ycondnames is not None and ycondvals is not None:
        if not len(ymetrics) == len(ycondnames) == len(ycondvals):
            raise ValueError('ymetrics, ycondnames and ycondvals must have the same length')
        # yvals is basically the list of values that differentiate each bar
        # it is used for legends and styles mainly
        yvals = ycondvals if len(set(ymetrics)) == 1 else zip(ymetrics, ycondvals)
    else:
        yvals = ymetrics
    placement = desc['placement'] if 'placement' in desc else 'grouped'
    if placement == 'grouped':
        placement = [1 for _ in range(len(yvals))]
    elif placement == 'stacked':
        placement = [len(yvals)]
    else:
        if sum(placement) != len(yvals):
            raise ValueError('Placement definition incorrect. '
                             'The sum of values of the list must be equal to '
                             'the number of y values')
    xticks = desc['xticks'] if 'xticks' in desc else desc['xvals']
    empty = True
    # Spacing attributes
    # width of a group of bars
    group_width = desc['group_width'] if 'group_width' in desc else 0.4
    width = group_width / len(placement)  # width of a single bar
    separation = width / 2  # space between adjacent groups
    border = 0.6 * separation  # left and right borders

    elem = collections.defaultdict(int)  # bar objects (for legend)
    # Select colors and hatches
    if 'bar_color' in desc and all(y in desc['bar_color'] for y in yvals):
        color = desc['bar_color']
    elif len(yvals) <= len(BW_COLOR_CATALOGUE):
        color = dict((y, BW_COLOR_CATALOGUE[yvals.index(y)]) for y in yvals)
    else:
        color = collections.defaultdict(lambda: None)
    if 'bar_hatch' in desc and desc['bar_hatch'] is None:
        hatch = collections.defaultdict(lambda: None)
    elif 'bar_hatch' in desc and all(y in desc['bar_hatch'] for y in yvals):
        hatch = desc['bar_hatch']
    elif len(yvals) <= len(BW_COLOR_CATALOGUE):
        hatch = dict((y, HATCH_CATALOGUE[yvals.index(y)]) for y in yvals)
    else:
        hatch = collections.defaultdict(lambda: None)
    # Plot bars
    left = border  # left-most point of the bar about to draw
    for i in range(len(desc['xvals'])):
        l = 0
        for x in placement:
            bottom = 0  # Bottom point of a bar. It is alway 0 if stacked is False
            for y in range(x):
                condition = Tree(desc['filter'])
                condition.setval(desc['xparam'], desc['xvals'][i])
                if ycondnames is not None:
                    condition.setval(ycondnames[l], ycondvals[l])
                data = [v.getval(ymetrics[l])
                        for _, v in resultset.filter(condition)
                        if v.getval(ymetrics[l]) is not None]
                confidence = desc['confidence'] if 'confidence' in desc else 0.95
                meanval, err = means_confidence_interval(data, confidence)
                yerr = None if 'errorbar' in desc and not desc['errorbar'] else err
                if not np.isnan(meanval):
                    empty = False
                elem[yvals[l]] = plt.bar(left, meanval, width,
                                         color=color[yvals[l]],
                                         yerr=yerr, bottom=bottom, ecolor='k',
                                         hatch=hatch[yvals[l]], label=yvals[l])
                bottom += meanval
                l += 1
            left += width
        left += separation
    if empty and not plot_empty:
        return
    n_bars = len(placement)
    plt.xticks(border + 0.5 * (n_bars * width) +
               (separation + n_bars * width) * np.arange(len(xticks)),
               xticks)
    if 'legend' in desc:
        legend = [desc['legend'][l] for l in yvals] if 'legend'in desc else yvals
        legend_args = desc['legend_args'] if 'legend_args' in desc else {}
        if 'legend_loc' in desc:
            legend_args['loc'] = desc['legend_loc']
        plt.legend([elem[x] for x in yvals], legend,
                   prop={'size': LEGEND_SIZE},
                   **legend_args)
    xmin, _ = plt.xlim()
    plt.xlim(xmin, left - separation + border)
    if 'ymax' in desc:
        plt.ylim(ymax=desc['ymax'])
    plt.savefig(os.path.join(plotdir, filename), bbox_inches='tight')
    plt.close(fig)


def plot_cdf(resultset, desc, filename, plotdir):
    """Plot a CDF with characteristics described in the plot descriptor
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
         The y label. The default value is 'Cumulative probability'
     * confidence : float, optional
         The confidence used to plot error bars. Default value is 0.95
     * metric : list
         A list of values representing the metric to plot. These values are the
         path to identify a specific metric into an entry of a result set.
         Normally, it is a 2-value list where the first value is the name of
         the collector which measured the metric and the second value is the
         metric name. The metric must be a CDF.
         Example values could be ['LATENCY', 'CDF'].
     * filter : dict, optional
         A dictionary of values to filter in the resultset.
         Example: {'network_cache': 0.004, 'topology_name': 'GEANT'}
         If not specified or None, no filtering is executed on the results
         and possibly heterogeneous results may be plotted together
     * ymetrics : list of tuples
         List of metrics to be shown on the graph. The i-th metric of the list
         is the metric that the i-th line on the graph will represent. If
         all lines are for the same metric, then all elements of the list are
         equal.
         Each single metric (i.e. each element of the list) is a tuple modeling
         the path to identify a specific metric into an entry of a result set.
         Normally, it is a 2-value list where the first value is the name of
         the collector which measured the metric and the second value is the
         metric name. Example values could be ('CACHE_HIT_RATIO', 'MEAN'),
         ('LINK_LOAD', 'MEAN_INTERNAL') or ('LATENCY', 'MEAN').
         For example, if in a graph of N lines all lines of the graph show mean
         latency, then ymetrics = [('LATENCY', 'MEAN')]*5.
     * ycondnames : list of tuples, optional
         List of condition names specific to each line of the graph. Different
         from the conditions expressed in the filter parameter, which are
         global, these conditions are specific to one bar. Ech condition name,
         different from the filter parameter is a path to a condition to be
         checked, e.g. ('topology', 'name'). Values to be matched for this
         conditions are specified in ycondvals. This list must be as long as
         the number of lines to plot. If not specified, all lines are filtered
         by the conditions of filter parameter only, but in this case all
         ymetrics should be different.
     * ycondvals : list of tuples, optional
         List of values that the conditions of ycondnames must meet. This list
         must be as long as the number of lines to plot. If not specified,
         all lines are filtered by the conditions of filter parameter only,
         but in this case all ymetrics should be different.
     * xscale : str, optional
         The scale of x axis. Options allowed are 'linear' and 'log'.
         Default value is 'linear'
     * yscale : str, optional
         The scale of y axis. Options allowed are 'linear' and 'log'.
         Default value is 'linear'
     * step : bool, optional
         If *True* draws the CDF with steps. Default value is *True*
     * line_style : dict, optional
         Dictionary mapping each value of yvals with a line style
     * legend : dict, optional
         Dictionary mapping each value of yvals with a legend label. If not
         specified, it is not plotted. If you wish to plot it with the
         name of the line, set it to put yvals or ymetrics, depending on which
         one is used
     * legend_loc : str, optional
         Legend location, e.g. 'upper left'
     * legend_args : dict, optional
         Optional legend arguments, such as ncol
     * plotempty : bool, optional
         If *True*, plot and save graph even if empty. Default is *True*
    """
    fig = plt.figure()
    if 'title' in desc:
        plt.title(desc['title'])
    if 'xlabel' in desc:
        plt.xlabel(desc['xlabel'])
    plt.ylabel(desc['ylabel'] if 'ylabel' in desc else 'Cumulative probability')
    if 'xscale' in desc:
        plt.xscale(desc['xscale'])
    if 'yscale' in desc:
        plt.yscale(desc['yscale'])
    if 'filter' not in desc or desc['filter'] is None:
        desc['filter'] = {}
    step = desc['step'] if 'step' in desc else True
    plot_empty = desc['plotempty'] if 'plotempty' in desc else True
    ymetrics = desc['ymetrics']
    ycondnames = desc['ycondnames'] if 'ycondnames' in desc else None
    ycondvals = desc['ycondvals'] if 'ycondvals' in desc else None
    if ycondnames is not None and ycondvals is not None:
        if not len(ymetrics) == len(ycondnames) == len(ycondvals):
            raise ValueError('ymetrics, ycondnames and ycondvals must have the same length')
        # yvals is basically the list of values that differentiate each line
        # it is used for legends and styles mainly
        yvals = ycondvals if len(set(ymetrics)) == 1 else zip(ymetrics, ycondvals)
    else:
        yvals = ymetrics
    x_min = np.infty
    x_max = -np.infty
    empty = True
    for i in range(len(yvals)):
        condition = Tree(desc['filter'])
        if ycondnames is not None:
            condition.setval(ycondnames[i], ycondvals[i])
        data = [v.getval(ymetrics[i])
                for _, v in resultset.filter(condition)
                if v.getval(ymetrics[i]) is not None]
        # If there are more than 1 CDFs in the resultset, take the first one
        if data:
            x_cdf, y_cdf = data[0]
            if step:
                x_cdf, y_cdf = step_cdf(x_cdf, y_cdf)
        else:
            x_cdf, y_cdf = [], []
        fmt = desc['line_style'][yvals[i]] if 'line_style' in desc \
              and yvals[i] in desc['line_style'] else '-'
        # This check is to prevent crashing when trying to plot arrays of nan
        # values with axes log scale
        if all(np.isnan(x) for x in x_cdf) or all(np.isnan(y) for y in y_cdf):
            plt.plot([], [], fmt)
        else:
            plt.plot(x_cdf, y_cdf, fmt)
            empty = False
            x_min = min(x_min, x_cdf[0])
            x_max = max(x_max, x_cdf[-1])
    if empty and not plot_empty:
        return
    plt.xlim(x_min, x_max)
    if 'legend' in desc:
        legend = [desc['legend'][l] for l in desc['yvals']]
        legend_args = desc['legend_args'] if 'legend_args' in desc else {}
        if 'legend_loc' in desc:
            legend_args['loc'] = desc['legend_loc']
        plt.legend(legend, prop={'size': LEGEND_SIZE}, **legend_args)
    plt.legend(legend, prop={'size': LEGEND_SIZE}, loc=desc['legend_loc'])
    plt.savefig(os.path.join(plotdir, filename), bbox_inches='tight')
    plt.close(fig)
