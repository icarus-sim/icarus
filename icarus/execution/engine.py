"""This module implements the simulation engine.

The simulation engine, given the parameters according to which a single
experiments needs to be run, instantiates all the required classes and executes
the experiment by iterating through the event provided by an event generator
and providing them to a strategy instance. 
"""
from icarus.execution import NetworkModel, NetworkView, NetworkController, CollectorProxy
from icarus.registry import data_collector_register, strategy_register


__all__ = ['exec_experiment']


def exec_experiment(topology, events, strategy, collectors):
    """
    Execute the simulation of a specific scenario
    
    Parameters
    ----------
    topology : Topology
        An FNSS topology object with the network topology used for the
        simulation
    events : iterable
        An iterable object whose elements are (time, event) tuples, where time
        is a float type indicating the timestamp of the event to be executed
        and event is a dictionary storing all the attributes of the event to
        execute
    strategy : 2-tuple
        Strategy definition. It is a 2-tuple where the first element is the
        name of the strategy and the second element is a dictionary of
        strategy attributes
    collectors: list of tuples
        The collectors to be used. It is a list of 2-tuples. Each tuple has as
        first element the name of the collector and as second element a
        dictionary of collector parameters
         
    Returns
    -------
    results : dict
        A dictionary with the aggregated simulation results from all collectors.
    """
    model = NetworkModel(topology)
    view = NetworkView(model)
    controller = NetworkController(model)
    
    collectors_inst = [data_collector_register[name](view, **params)
                  for name, params in collectors]
    collector = CollectorProxy(view, collectors_inst)
    controller.attach_collector(collector)
    
    str_name, str_params = strategy
    strategy_inst = strategy_register[str_name](view, controller, **str_params)
    
    for time, event in events:
        strategy_inst.process_event(time, **event)
    return collector.results()
