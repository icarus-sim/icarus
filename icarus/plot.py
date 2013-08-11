import matplotlib.pyplot as plt
from os import path
from collections import defaultdict 
from numpy import arange
from icarus.analysis import SummaryAnalyzer
import icarus.config as config

#--- CONFIG PARAMS

#--- SCOPE PARAMS

# Topologies to be plotted
TOPOLOGIES = ['GEANT', 'GARR', 'WIDE', 'TISCALI']

# Range of alpha used in alpha sensitivity plots
ALPHA_RANGE = arange(0.6, 1.11, 0.1)
# Fixed Value(s) of C used for alpha sensitivity plots
C_ALPHA_PLOT = [0.0004, 0.002, 0.01, 0.05]

# Range of C used in C sensitivity plots
C_RANGE = [0.0004, 0.002, 0.01, 0.05]
# Fixed Value(s) of alpha used for C sensitivity plots
ALPHA_C_PLOT = [0.6, 0.8, 1.0, 1.2]

# Link types used in netload plots
LINK_TYPES = ['internal', 'external']

#--- DIR PARAMS

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
         'CL4M',          # not shown in paper graphs
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
         'CL4M',          # not shown in paper graphs
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

def paper_graphs():
    """Plot all the graphs of the SIGCOMM ICN 13 paper
    """
    paper_plot_chr_alpha_sensitivity()
    paper_plot_chr_cache_size_sensitivity()
    paper_plot_bar_graph_chr()
    paper_plot_netload_alpha_sensitivity()
    paper_plot_netload_cache_size_sensitivity()
    paper_plot_bar_graph_netload()

def main():
    """Run the plot script
    """
    paper_graphs()


def plot_chr_alpha_sensitivity(show=True, save=True):
    """
    Plot sensitivity of network load vs alpha
    """
    # Parameters
    T = TOPOLOGIES
    C = C_ALPHA_PLOT
    A = ALPHA_RANGE
    # Execution
    for t in T:
        for c in [str(nc) for nc in C]:
            plt.figure()
            plt.title('Cache hit: T=%s C=%s' % (t, c))
            plt.ylabel('Cache hit ratio')
            plt.xlabel(u'Content distribution \u03b1')
            S = SummaryAnalyzer(path.join(SUMMARY_LOG_DIR, 'SUMMARY_CACHE_HIT_RATIO.txt'))
            for strategy in CACHE_STRATEGIES:
                cond = (S.param['T'] == t) &  (S.param['C'] == c) &  (S.param['S'] == strategy)
                plt.plot(S.param['A'][cond], S.data['CacheHitRatio'][cond], style_dict[strategy])
            plt.xlim(min(A),max(A))
            plt.legend(tuple(cache_legend_list), prop={'size': LEGEND_SIZE}, loc='upper left')
            if show: plt.show()
            if save: plt.savefig(path.join(GRAPHS_DIR , 'CACHE_HIT_T=%s@C=%s.pdf' % (t, c)), bbox_inches='tight')


def plot_netload_alpha_sensitivity(show=True, save=True):
    """
    Plot sensitivity of network load vs alpha
    """
    # Parameters
    T = TOPOLOGIES
    C = C_ALPHA_PLOT
    A = ALPHA_RANGE
    LT = LINK_TYPES
    # Execution
    for t in T:
        for c in [str(nc) for nc in C]:
            for lt in LT:
                plt.figure()
                plt.title('Network load: LINK=%s T=%s C=%s' % (lt, t, c))
                plt.ylabel('Average link load (Mbps)')
                plt.xlabel(u'Content distribution \u03b1')
                S = SummaryAnalyzer(path.join(SUMMARY_LOG_DIR, 'SUMMARY_NETWORK_LOAD.txt'))
                for strategy in NETLOAD_STRATEGIES:
                    cond = (S.param['T'] == t) &  (S.param['C'] == c) &  (S.param['S'] == strategy) & (S.data['LinkType'] == lt)
                    plt.plot(S.param['A'][cond], S.data['NetworkLoad'][cond], style_dict[strategy])
                plt.xlim(min(A),max(A))
                plt.legend(tuple(netload_legend_list), prop={'size': LEGEND_SIZE}, loc='lower left')
                if show: plt.show()
                if save: plt.savefig(path.join(GRAPHS_DIR ,'NETLOAD_LT=%s@T=%s@C=%s.pdf' % (lt, t, c)), bbox_inches='tight')


def plot_chr_cache_size_sensitivity(show=True, save=True):
    """
    Plot sensitivity of network load vs cache size
    """
    # Parameters
    T = TOPOLOGIES
    C = C_RANGE
    A = ALPHA_C_PLOT
    # Execution
    for t in T:
        for a in [str(al) for al in A]:
            plt.figure()
            plt.title('Cache hit: T=%s A=%s' % (t, a))
            plt.ylabel('Cache hit ratio')
            plt.xlabel('Cache to population ratio')
            plt.xscale('log')
            S = SummaryAnalyzer(path.join(SUMMARY_LOG_DIR, 'SUMMARY_CACHE_HIT_RATIO.txt'))
            for strategy in CACHE_STRATEGIES:
                cond = (S.param['T'] == t) &  (S.param['A'] == a) &  (S.param['S'] == strategy)
                plt.plot(S.param['C'][cond], S.data['CacheHitRatio'][cond], style_dict[strategy])
            plt.xlim(min(C), max(C))
            plt.legend(tuple(cache_legend_list), prop={'size': LEGEND_SIZE}, loc='upper left')
            if show: plt.show()
            if save: plt.savefig(path.join(GRAPHS_DIR ,'CACHE_HIT_C_SENS_T=%s@A=%s.pdf' % (t, a)), bbox_inches='tight')


def plot_netload_cache_size_sensitivity(show=True, save=True):
    """
    Plot sensitivity of network load vs cache size
    """
    # Parameters
    T = TOPOLOGIES
    C = C_RANGE
    A = ALPHA_C_PLOT
    LT = LINK_TYPES
    # Execution
    for t in T:
        for a in [str(al) for al in A]:
            for lt in LT:
                plt.figure()
                plt.title('Network load: LINK=%s T=%s A=%s' % (lt, t, a))
                plt.ylabel('Average link load (Mbps)')
                plt.xlabel('Cache to population ratio')
                plt.xscale('log')
                S = SummaryAnalyzer(path.join(SUMMARY_LOG_DIR, 'SUMMARY_NETWORK_LOAD.txt'))
                for strategy in NETLOAD_STRATEGIES:
                    cond = (S.param['T'] == t) &  (S.param['A'] == a) &  (S.param['S'] == strategy) & (S.data['LinkType'] == lt)
                    plt.plot(S.param['C'][cond], S.data['NetworkLoad'][cond], style_dict[strategy])
                plt.xlim(min(C), max(C))
                plt.legend(tuple(netload_legend_list), prop={'size': LEGEND_SIZE}, loc='lower left')
                if show: plt.show()
                if save: plt.savefig(path.join(GRAPHS_DIR ,'NETLOAD_C_SENS_LT=%s@T=%s@A=%s.pdf' % (lt, t, a)), bbox_inches='tight')



def plot_bar_graph_chr(show=True, save=True):
    """
    Plot bar graphs of cache hit ratio for specific values of alpha and C
    for various topologies.
    
    The objective here is to show that our algorithms works well on all
    topologies considered
    """
    # params
    alpha = '0.8'
    C = '0.0004'
    T = ['GARR', 'WIDE', 'TISCALI', 'GEANT']
    St = ['CEE+LRU', 'HrAsymm', 'HrSymm']
    # style
    color = {'CEE+LRU': 'k', 'HrSymm': '0.4', 'HrAsymm': '0.6'}
    hatch = {'CEE+LRU': None, 'HrSymm': '//', 'HrAsymm': '\\'}
    # execution
    S = SummaryAnalyzer(path.join(SUMMARY_LOG_DIR, 'SUMMARY_CACHE_HIT_RATIO.txt'))
    plt.figure()
    plt.subplot(111)
    plt.grid(b=True, which='major', color='k', axis='y', linestyle='--')
    plt.title('Cache hit ratio: Alpha=%s C=%s' % (alpha, C))
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
    plt.legend([elem[x] for x in St], St)
    xmin, _ = plt.xlim()
    plt.xlim(xmin, left + len(T) - 1 + len(St)*width + left)
    if show: plt.show()
    if save: plt.savefig(path.join(GRAPHS_DIR, 'BAR_CACHE_HIT_A=%s@C=%s.pdf' % (alpha, C)), bbox_inches='tight')



def plot_bar_graph_netload(show=True, save=True):
    """
    Plot bar graphs of cache hit ratio for specific values of alpha and C
    for various topologies.
    
    The objective here is to show that our algorithms works well on all
    topologies considered
    """
    # params
    alpha = '0.8'
    C = '0.0004'
    T = ['GARR', 'WIDE', 'TISCALI', 'GEANT']
    St = ['CEE+LRU', 'HrAsymm', 'HrSymm']
    LT = ['internal'] 
    # style
    color = {'CEE+LRU': 'k', 'HrSymm': '0.4', 'HrAsymm': '0.6'}
    hatch = {'CEE+LRU': None, 'HrSymm': '//', 'HrAsymm': '\\'}
    # execution
    S = SummaryAnalyzer(path.join(SUMMARY_LOG_DIR, 'SUMMARY_NETWORK_LOAD.txt'))
    for lt in LT:
        plt.figure()
        plt.subplot(111)
        plt.grid(b=True, which='major', color='k', axis='y', linestyle='--')
        plt.title('Netload: Alpha=%s C=%s' % (alpha, C))
        plt.ylabel('Cache hit ratio')
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
        plt.legend([elem[x] for x in St], St)
        xmin, _ = plt.xlim()
        plt.xlim(xmin, left + len(T) - 1 + len(St)*width + left)
        if show: plt.show()
        if save: plt.savefig(path.join(GRAPHS_DIR, 'BAR_NETLOAD_LT=%s@A=%s@C=%s.pdf' % (lt, alpha, C)), bbox_inches='tight')






#--- PLOTS OF THE ACM SIGCOMM ICN'13 PAPER

def paper_plot_chr_alpha_sensitivity():
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
                plt.plot(S.param['A'][cond], S.data['CacheHitRatio'][cond], style_dict[strategy])
            plt.xlim((0.6,1.1))
            plt.legend(tuple(cache_legend_list), loc='upper left', prop={'size': LEGEND_SIZE})
            plt.savefig(path.join(GRAPHS_DIR, 'paper-geant-cache-hit-alpha.pdf'), bbox_inches='tight')

def paper_plot_netload_alpha_sensitivity():
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
                    plt.plot(S.param['A'][cond], S.data['NetworkLoad'][cond], style_dict[strategy])
                plt.xlim((0.6,1.1))
                plt.legend(tuple(netload_legend_list), loc='upper right', prop={'size': LEGEND_SIZE})
                plt.savefig(path.join(GRAPHS_DIR, 'paper-geant-netload-alpha.pdf'), bbox_inches='tight')


def paper_plot_chr_cache_size_sensitivity():
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
                plt.plot(S.param['C'][cond], S.data['CacheHitRatio'][cond], style_dict[strategy])
            plt.xlim((0.0004, 0.05))
            plt.legend(tuple(cache_legend_list), loc='upper left', prop={'size': LEGEND_SIZE})
            plt.savefig(path.join(GRAPHS_DIR, 'paper-geant-cache-hit-c.pdf'), bbox_inches='tight')


def paper_plot_netload_cache_size_sensitivity():
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
                    plt.plot(S.param['C'][cond], S.data['NetworkLoad'][cond], style_dict[strategy])
                plt.xlim((0.0004, 0.05))
                plt.legend(tuple(netload_legend_list), loc='upper right', prop={'size': LEGEND_SIZE})
                plt.savefig(path.join(GRAPHS_DIR, 'paper-geant-netload-c.pdf'), bbox_inches='tight')




def paper_plot_bar_graph_chr():
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
    plt.savefig(path.join(GRAPHS_DIR, 'paper-bar-cache-hit.pdf'), bbox_inches='tight')
        
        

def paper_plot_bar_graph_netload():
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
        plt.savefig(path.join(GRAPHS_DIR, 'paper-bar-netload.pdf'), bbox_inches='tight')



if __name__ == '__main__':
    main()


