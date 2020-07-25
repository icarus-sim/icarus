"""Utility functions
"""
from __future__ import division
import time
import logging
import collections
import copy
import heapq

import numpy as np
import networkx as nx

__all__ = [
        'Settings',
        'AnyValue',
        'SequenceNumber',
        'config_logging',
        'inheritdoc',
        'timestr',
        'iround',
        'step_cdf',
        'Tree',
        'can_import',
        'overlay_betweenness_centrality',
        'path_links',
        'multicast_tree',
        'apportionment'
           ]


class Tree(collections.defaultdict):
    """Tree data structure

    This class models a tree data structure that is mainly used to store
    experiment parameters and results in a hierarchical form that makes it
    easier to search and filter data in them.
    """

    def __init__(self, data=None, **attr):
        """Constructor

        Parameters
        ----------
        data : input data
            Data from which building a tree. Types supported are Tree objects
            and dicts (or object that can be cast to trees), even nested.
        attr : additional keyworded attributes. Attributes can be trees of leaf
            values. If they're dictionaries, they will be converted to trees
        """
        if data is None:
            data = {}
        elif not isinstance(data, Tree):
            # If data is not a Tree try to cast to dict and iteratively recurse
            # it to convert each node to a tree
            data = dict(data)
            for k in data:
                if not isinstance(data[k], Tree) and isinstance(data[k], dict):
                    data[k] = Tree(data[k])
        # Add processed data to the tree
        super(Tree, self).__init__(Tree, data)
        if attr:
            self.update(attr)

    def __iter__(self, root=[]):
        it = collections.deque()
        for k_child, v_child in self.items():
            base = copy.copy(root)
            base.append(k_child)
            if isinstance(v_child, Tree):
                it.extend(v_child.__iter__(base))
            else:
                it.append((tuple(base), v_child))
        return iter(it)

    def __setitem__(self, k, v):
        if not isinstance(v, Tree) and isinstance(v, dict):
            v = Tree(v)
        super(Tree, self).__setitem__(k, v)

    def __reduce__(self):
        # This code is needed to fix an issue occurring while pickling.
        # Further info here:
        # http://stackoverflow.com/questions/3855428/how-to-pickle-and-unpickle-instances-of-a-class-that-inherits-from-defaultdict
        t = collections.defaultdict.__reduce__(self)
        return (t[0], ()) + t[2:]

    def __str__(self, dictonly=False):
        """Return a string representation of the tree

        Parameters
        ----------
        dictonly : bool, optional
            If True, just return a representation of a corresponding dictionary

        Returns
        -------
        tree : str
            A string representation of the tree
        """
        return "Tree({})".format(self.dict())

    @property
    def empty(self):
        """Return True if the tree is empty, False otherwise"""
        return len(self) == 0

    def update(self, e):
        """Update tree from e, similarly to dict.update

        Parameters
        ----------
        e : Tree
            The tree to update from
        """
        if not isinstance(e, Tree):
            e = Tree(e)
        super(Tree, self).update(e)

    def paths(self):
        """Return a dictionary mapping all paths to final (non-tree) values
        and the values.

        Returns
        -------
        paths : dict
            Path-value mapping
        """
        return dict(iter(self))

    def getval(self, path):
        """Get the value at a specific path, None if not there

        Parameters
        ----------
        path : iterable
            Path to the desired value

        Returns
        -------
        val : any type
            The value at the given path
        """
        tree = self
        for i in path:
            if isinstance(tree, Tree) and i in tree:
                tree = tree[i]
            else:
                return None
        return None if isinstance(tree, Tree) and tree.empty else tree

    def setval(self, path, val):
        """Set a value at a specific path

        Parameters
        ----------
        path : iterable
            Path to the value
        val : any type
            The value to set at the given path
        """
        tree = self
        for i in path[:-1]:
            if not isinstance(tree[i], Tree):
                tree[i] = Tree()
            tree = tree[i]
        tree[path[-1]] = val

    def dict(self, str_keys=False):
        """Convert the tree in nested dictionaries

        Parameters
        ----------
        str_key : bool, optional
            Convert keys to string. This is useful for example to dump a dict
            into a JSON object that requires keys to be strings

        Returns
        -------
        d : dict
            A nested dict representation of the tree
        """
        d = {}
        for k, v in self.items():
            k = str(k) if str_keys else k
            v = v.dict() if isinstance(v, Tree) else v
            d[k] = v
        return d

    def match(self, condition):
        """Check if the tree matches a given condition.

        The condition is another tree. This method iterates to all the values
        of the condition and verify that all values of the condition tree are
        present in this tree and have the same value.

        Note that the operation is not symmetric i.e.
        self.match(condition) != condition.match(self). In fact, this method
        return True if this tree has values not present in the condition tree
        while it would return False if the condition has values not present
        in this tree.

        Parameters
        ----------
        condition : Tree
            The condition to check

        Returns
        -------
        match : bool
            True if the tree matches the condition, False otherwise.
        """
        condition = Tree(condition)
        return all(self.getval(path) == val for path, val in condition.paths().items())


class Settings(object):
    """Object storing all settings"""

    def __init__(self):
        """Constructor
        """
        # This kind of assignment using __setattr__ is to prevent infinite
        # recursion
        object.__setattr__(self, '__conf', dict())
        object.__setattr__(self, '__frozen', False)

    def __len__(self):
        """Return the number of settings

        Returns
        -------
        len : int
            The number of settings
        """
        return len(self.__conf)

    def __getitem__(self, name):
        """Return value of settings with given name

        Parameters
        ----------
        name : str
            Name of the setting

        Returns
        -------
        value : any hashable type
            The value of the setting
        """
        if name in self.__conf:
            return self.__conf[name]
        else:
            raise ValueError('Setting %s not found' % str(name))

    def __getstate__(self):
        """Return a representation of the object for pickling purposes.

        Returns
        -------
        state : dict
            State of current object
        """
        # This function was implemented because otherwise pickling
        # under Python 3.x fails
        return self.__dict__

    def __getattr__(self, name):
        """Return value of settings with given name

        Parameters
        ----------
        name : str
            Name of the setting

        Returns
        -------
        value : any hashable type
            The value of the setting
        """
        if name == '_Settings__conf':
            return object.__getattribute__(self, '__conf')
        if name == '_Settings__frozen':
            return object.__getattribute__(self, '__frozen')
        if name in self.__conf:
            return self.__conf[name]
        else:
            raise ValueError('Setting %s not found' % str(name))

    def __setitem__(self, name, value):
        """Sets a given value for a settings with given name

        Parameters
        ----------
        name : str
            Name of the setting
        value : any hashable type
            The value of the setting
        """
        return self.set(name, value)

    def __setattr__(self, name, value):
        """Sets a given value for a settings with given name

        Parameters
        ----------
        name : str
            Name of the setting
        value : any hashable type
            The value of the setting
        """
        if name == '_Settings__conf':
            object.__setattr__(self, '__conf', value)
        return self.set(name, value)

    def __delitem__(self, name):
        """Removes a specific setting

        Parameters
        ----------
        name : str
            Name of the setting
        """
        if self.__frozen:
            raise ValueError('Settings are frozen and cannot be modified')
        del self.__conf[name]

    def __contains__(self, name):
        """Checks if a specific setting exists or not

        Parameters
        ----------
        name : str
            The name of the setting

        Returns
        -------
        contains : bool
            *True* if present, *False* otherwise
        """
        return name in self.__conf

    @property
    def frozen(self):
        "Return whether the object is frozen or not."
        return self.__frozen

    def read_from(self, path, freeze=False):
        """Initialize settings by reading from a file

        Parameters
        ----------
        path : str
            The path of the file from which settings are read
        freeze : bool, optional
            If *True*, freezes object so that settings cannot be changed
        """
        if self.__frozen:
            raise ValueError('Settings are frozen and cannot be modified')
        exec(open(path).read(), self.__conf)
        for k in list(self.__conf):
            if k != k.upper():
                del self.__conf[k]
        if freeze:
            self.freeze()

    def freeze(self):
        "Freeze the objects. No settings can be added or modified any more"
        self.__frozen = True

    def get(self, name):
        """Return value of settings with given name

        Parameters
        ----------
        name : str
            Name of the setting

        Returns
        -------
        value : any hashable type
            The value of the setting
        """
        if name in self.__conf:
            return self.__conf[name]
        else:
            raise ValueError('Setting %s not found' % str(name))

    def set(self, name, value):
        """Sets a given value for a settings with given name

        Parameters
        ----------
        name : str
            Name of the setting
        value : any hashable type
            The value of the setting
        """
        if self.frozen:
            raise ValueError('Settings are frozen and cannot be modified')
        self.__conf[name] = value


class AnyValue(object):
    """Pseudo-value that returns True when compared to any other object.

    This object can be used for example to store parameters in resultsets.

    One concrete usage example is the following: let's assume that a user runs
    an experiment using various strategies under different values of a
    specific parameter and that the user knows that one strategy does not
    depend on that parameters while others do.
    If a user wants to plot the sensitivity of all these strategies against
    this parameter, he would want the strategy insensitive to that parameter to
    be selected from the resultset when filtering it against any value of that
    parameter. This can be achieved by setting AnyValue() to this parameter in
    the result related to that strategy.
    """

    def __eq__(self, other):
        """Return always True

        Parameters
        ----------
        other : any
            The object to be compared

        Returns
        -------
        eq : bool
            Always True
        """
        return True

    def __ne__(self, other):
        """Return always False

        Parameters
        ----------
        other : any
            The object to be compared

        Returns
        -------
        en : bool
            Always False
        """
        return False


class SequenceNumber(object):
    """This class models an increasing sequence number.

    It is used to assign a sequence number for an experiment in a thread-safe
    manner.
    """

    def __init__(self, initval=1):
        """Constructor

        Parameters
        ----------
        initval :int, optional
            The starting sequence number
        """
        self.__seq = initval - 1

    def assign(self):
        """Assigns a new sequence number.

        Returns
        -------
        seq : int
            The sequence number
        """
        self.__seq += 1
        seq = self.__seq
        return seq

    def current(self):
        """Return the latest sequence number assigned

        Returns
        -------
        seq : int
            The latest assigned sequence number
        """
        return self.__seq


def config_logging(log_level='INFO'):
    """Configure logging level

    Parameters
    ----------
    log_level : int
        The granularity of logging
    """
    FORMAT = "[%(asctime)s|%(levelname)s|%(name)s] %(message)s"
    DATE_FMT = "%H:%M:%S %Y-%m-%d"
    log_level = eval('logging.%s' % log_level.upper())
    logging.basicConfig(format=FORMAT, datefmt=DATE_FMT, level=log_level)


def inheritdoc(cls):
    """Decorator that inherits docstring from the overridden method of the
    superclass.

    Parameters
    ----------
    cls : Class
        The superclass from which the method docstring is inherit

    Notes
    -----
    This decorator requires to specify the superclass the contains the method
    (with the same name of the method to which this decorator is applied) whose
    docstring is to be replicated. It is possible to implement more complex
    decorators which identify the superclass automatically. There are examples
    available in the Web (e.g., http://code.activestate.com/recipes/576862/),
    however, the increased complexity leads to issues of interactions with
    other decorators.
    This implementation is simple, easy to understand and works well with
    Icarus code.
    """
    def _decorator(function):
        # This assignment is needed to maintain a reference to the superclass
        sup = cls
        name = function.__name__
        function.__doc__ = eval('sup.%s.__doc__' % name)
        return function
    return _decorator


def timestr(sec, with_seconds=True):
    """Get a time interval in seconds and returns it formatted in a string.

    The returned string includes days, hours, minutes and seconds as
    appropriate.

    Parameters
    ----------
    sec : float
        The time interval
    with_seconds : bool
        If *True* the time string includes seconds, otherwise only minutes

    Returns
    -------
    timestr : str
        A string expressing the time in days, hours, minutes and seconds
    """
    t = time.gmtime(iround(sec))
    days = t.tm_yday - 1
    hours = t.tm_hour
    mins = t.tm_min
    secs = t.tm_sec
    units = collections.deque(('d', 'h', 'm', 's'))
    vals = collections.deque((days, hours, mins, secs))
    if not with_seconds:
        units.pop()
        vals.pop()
    if all(x == 0 for x in vals):
        return "0%s" % units[-1]
    while vals[0] == 0:
        vals.popleft()
        units.popleft()
    while vals[-1] == 0:
        vals.pop()
        units.pop()
    return "".join("%d%s " % (vals[i], units[i]) for i in range(len(vals)))[:-1]


def iround(x):
    """Round float to closest integer

    This code was taken from here:
    http://www.daniweb.com/software-development/python/threads/299459/round-to-nearest-integer

    Parameters
    ----------
    x : float
        The number to round

    Returns
    -------
    xr : int
        The rounded number
    """
    y = round(x) - .5
    return int(y) + (y > 0)


def step_cdf(x, y):
    """Convert an empirical CDF in set of points representing steps.

    Normally this is conversion is done for plotting purposes.

    Parameters
    ----------
    x : array
        The x values of the CDF
    y : array
        The y values of the CDF

    Returns
    -------
    x : array
        The x values of the CDF
    y : array
        The y values of the CDF
    """
    if len(x) != len(y):
        raise ValueError('x and y must have the same size')
    sx = np.empty(2 * (len(x)))
    sy = np.empty(2 * (len(y)))
    for i in range(len(x)):
        sx[2 * i] = x[i]
        sx[2 * i + 1] = x[i]
        sy[2 * i] = y[i - 1]
        sy[2 * i + 1] = y[i]
    sy[0] = 0
    return sx, sy


def overlay_betweenness_centrality(topology, origins=None, destinations=None,
                                  normalized=True, endpoints=False):
    """Calculate the betweenness centrality of a graph but only regarding the
    paths from a set of origins nodes to a set of destinations node.

    Parameters
    ----------
    topology : fnss.Topology
        The topology
    origins : iterable, optional
        The origin nodes. If not specified, nodes with *receiver* stack are
        selected
    destinations : iterable, optional
        The destination nodes. If not specified, nodes with *source* stack are
        selected
    normalized : bool, optional
        If *True*, returned normalized values
    endpoints : bool, optional
        If *True* endpoints are included in path calculation.

    Returns
    -------
    betw : dict
        Dictionary of betweenness centralities keyed by node
    """
    if origins is None:
        origins = [v for v, (stack, _) in topology.stacks().items() if stack == 'receiver']
    if destinations is None:
        destinations = [v for v, (stack, _) in topology.stacks().items() if stack == 'source']
    betweenness = collections.defaultdict(int)
    path = {v: nx.single_source_shortest_path(topology, v) for v in origins}
    for u in path:
        for v in path[u]:
            if v not in destinations:
                continue
            sp = path[u][v] if endpoints else path[u][v][1:-1]
            for i in sp:
                betweenness[i] += 1
    if normalized:
        norm = len(origins) * len(destinations)
        for v in betweenness:
            betweenness[v] /= norm
    return betweenness


def path_links(path):
    """Convert a path expressed as list of nodes into a path expressed as a
    list of edges.

    Parameters
    ----------
    path : list
        List of nodes

    Returns
    -------
    path : list
        List of edges
    """
    return [(path[i], path[i + 1]) for i in range(len(path) - 1)]


def multicast_tree(shortest_paths, source, destinations):
    """Return a multicast tree expressed as a set of edges, without any
    ordering

    Parameters
    ----------
    shortest_paths : dict of dicts
        Return all pairs shortest paths
    source : any hashable object
        The source node of the multicast tree
    destinations : iterable
        All destinations of the multicast tree

    Return
    ------
    multicast_tree : set
        Set of edges
    """
    tree = set()
    for d in destinations:
        if d == source:
            continue
        tree = tree.union(set(path_links(shortest_paths[source][d])))
    return tree


def apportionment(n, fracs):
    """Allocate items to buckets according to a given proportion.

    This function uses the Largest remainder method with the Hare quota.

    Parameters
    ----------
    n : int
        Number of items to allocate to buckets
    fracs : list of float
        Proportion of items to allocate to each bucket

    Return
    ------
    apportionment : list of int
        Apportionment of items to buckets
    """
    ints, remainders = zip(*[divmod(n * f, 1) for f in fracs])
    to_alloc = int(n - sum(ints))
    ints = list(ints)
    if to_alloc == 0:
        return ints
    idx = heapq.nlargest(to_alloc, range(len(remainders)), remainders.__getitem__)
    for i in idx:
        ints[i] += 1
    return ints
