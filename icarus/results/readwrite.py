"""Functions for reading and writing results
"""
import collections
import copy
try:
    import cPickle as pickle
except ImportError:
    import pickle

from icarus.registry import register_results_reader, register_results_writer


__all__ = [
    'ResultSet',
    'write_results_pickle',
    'read_results_pickle'
           ]

class ResultSet(object):
    """This class can be used to store results from different experiments,
    accessed and filtered.
    
    All operations that write data are thread-safe so that this object can 
    be shared by different processes.
    """
    
    def __init__(self):
        """Constructor
        """
        self._results = collections.deque()
        # Dict of global attributes common to all experiments
        self.attr = {}
    
    def __len__(self):
        """Returns the number of results in the resultset
        
        Returns
        -------
        len : int
            The length of the resultset
        """
        return len(self._results)
    
    def __iter__(self):
        """Returns iterator over the resultset
        """
        return iter(self._results)
        
    def __getitem__(self, i):
        """Returns a specified item of the resultset
        
        Parameters
        ----------
        i : int
            The index of the result
            
        Returns
        -------
        result : tuple
            Result
        """
        return self._results[i]

    def __add__(self, resultset):
        """Merges two resultsets.
        
        Parameters
        ----------
        resultset : ResultSet
            The result set to merge
        
        Returns
        -------
        resultset : ResultSet
            The resultset containing results from this resultset and the one
            passed as argument
        """
        if self.attr != resultset.attr:
            raise ValueError('The resultsets cannot be merged because '
                             'they have different global attributes')
        rs = copy.deepcopy(self)
        for i in iter(resultset):
            rs.add(i)
        return rs

    def add(self, result):
        """Add a result to the result set. This method is thread safe
        
        Parameters
        ----------
        results : 2-value tuple
            2-value tuples where the first value is a dictionary of experiment
            parameters and the second value is the dictionary of experiment
            results
        """
        self._results.append(result)
    
    def dump(self):
        """Dump all results.
        
        Returns
        -------
        results : list
            A list of 2-value tuples where the first value is the dictionary
            of experiment parameters and the second value is the dictionary
            of experiment results.
        """
        return list(self._results)

    
    def filter(self, parameters, metrics=None):
        """Return subset of results matching specific conditions
        
        Parameters
        ----------
        parameters : dict
            Dictionary listing all parameters and values to be matched in the
            results set
        metrics : dict, optional
            List of metrics to be reported
        
        Returns
        -------
        filtered_results : list
            List of 2-tuples of filtered results, where the first element is a
            dictionary of all experiment parameters and the second value is 
            a dictionary with experiment results.
        """
        filtered_results = collections.deque()
        for exp_params, exp_metrics in self._results:
            match = True
            for k, v in parameters.iteritems():
                if k not in exp_params or exp_params[k] != v:
                    match = False
                    break
            if match:
                filtered_metrics = exp_metrics if metrics is None else \
                    dict((m, exp_metrics[m]) for m in metrics if m in exp_metrics)
                filtered_results.append((exp_params, filtered_metrics))
        return list(filtered_results)


@register_results_writer('PICKLE')
def write_results_pickle(results, path):
    """Write a resultset to a pickle file
    
    Parameters
    ----------
    results : ResultSet
        The set of results
    path : str
        The path of the file to which write
    """
    with open(path, 'wb') as pickle_file:
        pickle.dump(results, pickle_file)


@register_results_reader('PICKLE')
def read_results_pickle(path):
    """Reads a resultset from a pickle file.
    
    Parameters
    ----------
    path : str
        The file path from which results are read
    
    Returns
    -------
    results : ResultSet
        The read result set
    """
    with open(path, 'rb') as pickle_file:
        return pickle.load(pickle_file)