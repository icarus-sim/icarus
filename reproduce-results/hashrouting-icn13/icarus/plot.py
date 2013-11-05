import matplotlib.pyplot as plt
from os import path
from collections import defaultdict 
from numpy import arange, zeros, asarray
from icarus.analysis import SummaryAnalyzer
import icarus.config as config


SUMMARY_LOG_DIR     = config.LOG_DIR
GRAPHS_DIR          = config.GRAPHS_DIR
GRAPHS_TIME_DIR     = config.GRAPHS_DIR


# List of strategies plotted in cache graphs
CACHE_STRATEGIES = [
         'HrSymm',
#         'HrMCast',      # don't show because superimposed by symm
         'HrAsymm',
         'HrHybStr02', 
#         'HrHybSymMC',   # don't show because superimposed by symm
         'ProbCache',
         'CEE+LRU',
         'Optimal',
                ]

# List of strategies plotted in network load graphs
NETLOAD_STRATEGIES = [
         'HrSymm',
         'HrMCast',  
         'HrAsymm',       
         'HrHybStr02',
         'HrHybSymMC',
         'ProbCache',
         'CEE+LRU',
         'NoCache',
                ]


#--- STYLE PARAMS

# These lines prevent insertion of Type 3 fonts in figures
# Publishers don't want them
plt.rcParams['ps.useafm'] = True
plt.rcParams['pdf.use14corefonts'] = True
plt.rcParams['text.usetex'] = True

plt.rcParams['figure.figsize'] = 8, 4.5

LEGEND_SIZE = 11

# This dict maps name of strategies to the style of the line to be used in the plots
# Off-path strategies: solid lines
# On-path strategies: dashed lines
# No-cache: dotted line
style_dict = {
         'HrSymm':      'b-o',
         'HrAsymm':     'g-D',
         'HrMCast':     'm-^',         
         'HrHybStr02':  'c-s',
         'HrHybSymMC':  'r-v',
         
         'CEE+LRU':     'b--p',
         'CL4M':        'g-->',
         'ProbCache':   'c--<',
         
         'ProbCache05':   'y--<',
         'ProbCache01':   'r--<',
         'ProbCache20':   'g--*',
         
         'NoCache':     'k:o',
         'Optimal':     'k-o'
                }

# This dict maps name of strategies to names to be displayed in the legend
legend_name = {
         'HrSymm':      'HR Symm',
         'HrAsymm':     'HR Asymm',
         'HrMCast':     'HR Multicast',         
         'HrHybStr02':  'HR Hybrid AM',
         'HrHybSymMC':  'HR Hybrid SM',
         
         'CEE+LRU':     'Ubiquitous',
         'CL4M':        'CL4M',
         'ProbCache':   'ProbCache',

         'NoCache':     'No caching',
         'Optimal':     'Optimal'
                }

cache_legend_list = [legend_name[s] for s in CACHE_STRATEGIES]
netload_legend_list = [legend_name[s] for s in NETLOAD_STRATEGIES]


def main():
    """Plot all the graphs of the SIGCOMM ICN 13 hash-routing paper
    """
    print('[PLOT] Plotting cache hit ratio vs alpha')
    plot_chr_alpha_sensitivity()
    print('[PLOT] Plotting cache hit ratio vs cache size')
    plot_chr_cache_size_sensitivity()
    print('[PLOT] Plotting cache hit ratio for various topologies')
    plot_bar_graph_chr()
    print('[PLOT] Plotting link load vs alpha')
    plot_netload_alpha_sensitivity()
    print('[PLOT] Plotting link load vs cache size')
    plot_netload_cache_size_sensitivity()
    print('[PLOT] Plotting link load for various topologies')
    plot_bar_graph_netload()


def plot_chr_alpha_sensitivity():
    """
    Plot sensitivity of network load vs alpha
    """
    # Parameters
    T = ['GEANT']
    C = ['0.002']
    # Execution
    for t in T:
        for c in C:
            plt.figure()
            plt.ylabel('Cache hit ratio')
            plt.xlabel(r'Content popularity skewness ($\alpha$)')
            S = SummaryAnalyzer(path.join(SUMMARY_LOG_DIR, 'SUMMARY_CACHE_HIT_RATIO.txt'))
            for strategy in CACHE_STRATEGIES:
                cond = (S.param['T'] == t) &  (S.param['C'] == c) &  (S.param['S'] == strategy)
                x = S.param['A'][cond]
                y = S.data['CacheHitRatio'][cond]
                x, y = _sort_xy(x, y)
                plt.plot(x, y, style_dict[strategy])
            plt.xlim((0.6,1.1))
            plt.legend(tuple(cache_legend_list), loc='upper left', prop={'size': LEGEND_SIZE})
            plt.savefig(path.join(GRAPHS_DIR, 'geant-cache-hit-alpha.pdf'), bbox_inches='tight')

def plot_netload_alpha_sensitivity():
    """
    Plot sensitivity of network load vs alpha
    """
    # Parameters
    T = ['GEANT']
    C = ['0.002']
    LT = ['internal']
    # Execution
    for t in T:
        for c in C:
            for lt in LT:
                plt.figure()
                plt.ylabel('Average link load (Mbps)')
                plt.xlabel(r'Content popularity skewness ($\alpha$)')
                S = SummaryAnalyzer(path.join(SUMMARY_LOG_DIR, 'SUMMARY_NETWORK_LOAD.txt'))
                for strategy in NETLOAD_STRATEGIES:
                    cond = (S.param['T'] == t) &  (S.param['C'] == c) &  (S.param['S'] == strategy) & (S.data['LinkType'] == lt)
                    x = S.param['A'][cond]
                    y = S.data['NetworkLoad'][cond]
                    x, y = _sort_xy(x, y)
                    plt.plot(x, y, style_dict[strategy])
                plt.xlim((0.6,1.1))
                plt.legend(tuple(netload_legend_list), loc='upper right', prop={'size': LEGEND_SIZE})
                plt.savefig(path.join(GRAPHS_DIR, 'geant-netload-alpha.pdf'), bbox_inches='tight')


def plot_chr_cache_size_sensitivity():
    """
    Plot sensitivity of network load vs cache size
    """
    # Parameters
    T = ['GEANT']
    A = ['0.8']
    # Execution
    for t in T:
        for a in [str(al) for al in A]:
            plt.figure()
            plt.ylabel('Cache hit ratio')
            plt.xlabel(r'Cache to population ratio ($C$)')
            plt.xscale('log')
            S = SummaryAnalyzer(path.join(SUMMARY_LOG_DIR, 'SUMMARY_CACHE_HIT_RATIO.txt'))
            for strategy in CACHE_STRATEGIES:
                cond = (S.param['T'] == t) &  (S.param['A'] == a) &  (S.param['S'] == strategy)
                x = S.param['C'][cond]
                y = S.data['CacheHitRatio'][cond]
                x, y = _sort_xy(x, y)
                plt.plot(x, y, style_dict[strategy])
            plt.xlim((0.0004, 0.05))
            plt.legend(tuple(cache_legend_list), loc='upper left', prop={'size': LEGEND_SIZE})
            plt.savefig(path.join(GRAPHS_DIR, 'geant-cache-hit-c.pdf'), bbox_inches='tight')


def plot_netload_cache_size_sensitivity():
    """
    Plot sensitivity of network load vs cache size
    """
    # Parameters
    T = ['GEANT']
    A = ['0.8']
    LT = ['internal']
    # Execution
    for t in T:
        for a in [str(al) for al in A]:
            for lt in LT:
                plt.figure()
                plt.ylabel('Average link load (Mbps)')
                plt.xlabel(r'Cache to population ratio ($C$)')
                plt.xscale('log')
                S = SummaryAnalyzer(path.join(SUMMARY_LOG_DIR, 'SUMMARY_NETWORK_LOAD.txt'))
                for strategy in NETLOAD_STRATEGIES:
                    cond = (S.param['T'] == t) &  (S.param['A'] == a) &  (S.param['S'] == strategy) & (S.data['LinkType'] == lt)
                    x = S.param['C'][cond]
                    y = S.data['NetworkLoad'][cond]
                    x, y = _sort_xy(x, y)
                    plt.plot(x, y, style_dict[strategy])
                plt.xlim((0.0004, 0.05))
                plt.legend(tuple(netload_legend_list), loc='upper right', prop={'size': LEGEND_SIZE})
                plt.savefig(path.join(GRAPHS_DIR, 'geant-netload-c.pdf'), bbox_inches='tight')




def plot_bar_graph_chr():
    """
    Plot bar graphs of cache hit ratio for specific values of alpha and C
    for various topologies.
    
    The objective here is to show that our algorithms works well on all
    topologies considered
    """
    # params
    alpha = '0.8'
    C = '0.002'
    T = ['GARR', 'WIDE', 'TISCALI', 'GEANT']
    St = ['CEE+LRU', 'HrAsymm', 'HrHybStr02','HrHybSymMC', 'HrSymm']
    # style
    color = {'CEE+LRU': 'k', 'HrAsymm': '0.4', 'HrHybStr02': '0.5','HrHybSymMC': '0.6', 'HrSymm': '0.7'}
    hatch = {'CEE+LRU': None, 'HrAsymm': '//', 'HrHybStr02': 'x','HrHybSymMC': '+', 'HrSymm': '\\'}
    # execution
    S = SummaryAnalyzer(path.join(SUMMARY_LOG_DIR, 'SUMMARY_CACHE_HIT_RATIO.txt'))
    plt.figure()
    plt.subplot(111)
    plt.grid(b=True, which='major', color='k', axis='y', linestyle='--')
    plt.ylabel('Cache hit ratio')
    width = 0.15       # the width of the bars
    left = 0.15 # offset left of first bar
    offset = 0
    elem = defaultdict(int) # bar objects (for legend)
    for s in St:
        index = 0
        for t in T:
            cond = (S.param['T'] == t) &  (S.param['C'] == C) & (S.param['S'] == s) & (S.param['A'] == alpha)
            val = S.data['CacheHitRatio'][cond][0]
            elem[s] = plt.bar(left + index + offset, val, width, color=color[s], hatch=hatch[s], label=s)
            index += 1
        offset += width
    plt.xticks(left + arange(len(T)) +0.5*len(St)*width, T)
    plt.legend([elem[x] for x in St], [legend_name[s] for s in St], prop={'size': LEGEND_SIZE}, loc='lower right')
    xmin, _ = plt.xlim()
    plt.xlim(xmin, left + len(T) - 1 + len(St)*width + left)
    plt.savefig(path.join(GRAPHS_DIR, 'bar-cache-hit.pdf'), bbox_inches='tight')
        
        

def plot_bar_graph_netload():
    """
    Plot bar graphs of cache hit ratio for specific values of alpha and C
    for various topologies.
    
    The objective here is to show that our algorithms works well on all
    topologies considered
    """
    # params
    alpha = '0.8'
    C = '0.002'
    T = ['GARR', 'WIDE', 'TISCALI', 'GEANT']
    St = ['CEE+LRU', 'HrAsymm', 'HrHybStr02','HrHybSymMC', 'HrSymm']
    LT = ['internal'] 
    # style
    color = {'CEE+LRU': 'k', 'HrAsymm': '0.4', 'HrHybStr02': '0.5','HrHybSymMC': '0.6', 'HrSymm': '0.7'}
    hatch = {'CEE+LRU': None, 'HrAsymm': '//', 'HrHybStr02': 'x','HrHybSymMC': '+', 'HrSymm': '\\'}
    # execution
    S = SummaryAnalyzer(path.join(SUMMARY_LOG_DIR, 'SUMMARY_NETWORK_LOAD.txt'))
    for lt in LT:
        plt.figure()
        plt.subplot(111)
        plt.grid(b=True, which='major', color='k', axis='y', linestyle='--')
        plt.ylabel('Average link load (Mbps)')
        width = 0.15       # the width of the bars
        left = 0.15 # offset left of first bar
        offset = 0
        elem = defaultdict(int) # bar objects (for legend)
        for s in St:
            index = 0
            for t in T:
                cond = (S.param['T'] == t) &  (S.param['C'] == C) & (S.param['S'] == s) & (S.param['A'] == alpha) & (S.data['LinkType'] == lt)
                val = S.data['NetworkLoad'][cond][0]
                elem[s] = plt.bar(left + index + offset, val, width, color=color[s], hatch=hatch[s], label=s)
                index += 1
            offset += width
        plt.xticks(left + arange(len(T)) +0.5*len(St)*width, T)
        plt.legend([elem[x] for x in St], [legend_name[s] for s in St], prop={'size': LEGEND_SIZE}, loc='lower right')
        xmin, _ = plt.xlim()
        plt.xlim(xmin, left + len(T) - 1 + len(St)*width + left)
        plt.savefig(path.join(GRAPHS_DIR, 'bar-netload.pdf'), bbox_inches='tight')


def _sort_xy(x , y):
    if len(x) != len(y):
        raise ValueError('x and y array must have the same size')
    argsort = asarray(x).argsort()
    xs = asarray([x[i] for i in argsort])
    ys = asarray([y[i] for i in argsort])
    return xs, ys
    
if __name__ == '__main__':
    main()

