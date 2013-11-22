# Dictionary storying all cache policy implementations keyed by ID
cache_policy_register = {}

# Dictionary storying all strategy implementations keyed by ID
strategy_register = {}

# Dictionary storying all network topologies keyed by ID
topology_factory_register = {}

# Dictionary storying all network topologies keyed by ID
data_collector_register = {}

# Dictionary storying all results reader functions keyed by ID
results_reader_register = {}

# Dictionary storying all results writer functions keyed by ID
results_writer_register = {}

def register_decorator(register):
    """Returns a decorator that register a class or function to a specified
    register
    
    Parameters
    ----------
    register : dict
        The register to which the class or function is register
    
    Returns
    -------
    decorator : func
        The decorator
    """
    def decorator(name):
        """Decorator that register a class or a function to a register.
        
        Parameters
        ----------
        name : str
            The name assigned to the class or function to store in the register
        """
        def _decorator(function):
            register[name] = function
            function.name = name
            return function
        return _decorator
    return decorator

register_cache_policy = register_decorator(cache_policy_register)
register_strategy = register_decorator(strategy_register)
register_topology_factory = register_decorator(topology_factory_register)
register_data_collector = register_decorator(data_collector_register)
register_results_reader = register_decorator(results_reader_register)
register_results_writer = register_decorator(results_writer_register)
