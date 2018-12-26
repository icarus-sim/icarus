"""Implementations of base strategies"""
from __future__ import division
import abc

from icarus.registry import register_strategy
from icarus.util import inheritdoc

__all__ = [
        'Strategy',
        'NoCache'
          ]


class Strategy(object):
    """Base strategy imported by all other strategy classes"""

    __metaclass__ = abc.ABCMeta

    def __init__(self, view, controller, **kwargs):
        """Constructor

        Parameters
        ----------
        view : NetworkView
            An instance of the network view
        controller : NetworkController
            An instance of the network controller
        kwargs : keyworded arguments, optional
            Additional strategy parameters
        """
        self.view = view
        self.controller = controller

    @abc.abstractmethod
    def process_event(self, time, receiver, content, log):
        """Process an event received from the simulation engine.

        This event is processed by executing relevant actions of the network
        controller, potentially based on the current status of the network
        retrieved from the network view.

        Parameters
        ----------
        time : int
            The timestamp of the event
        receiver : any hashable type
            The receiver node requesting a content
        content : any hashable type
            The content identifier requested by the receiver
        log : bool
            Indicates whether the event must be registered by the data
            collectors attached to the network.
        """
        raise NotImplementedError('The selected strategy must implement '
                                  'a process_event method')


@register_strategy('NO_CACHE')
class NoCache(Strategy):
    """Strategy without any caching

    This corresponds to the traffic in a normal TCP/IP network without any
    CDNs or overlay caching, where all content requests are served by the
    original source.
    """

    @inheritdoc(Strategy)
    def __init__(self, view, controller, **kwargs):
        super(NoCache, self).__init__(view, controller)

    @inheritdoc(Strategy)
    def process_event(self, time, receiver, content, log):
        # get all required data
        source = self.view.content_source(content)
        path = self.view.shortest_path(receiver, source)
        # Route requests to original source
        self.controller.start_session(time, receiver, content, log)
        self.controller.forward_request_path(receiver, source)
        self.controller.get_content(source)
        # Route content back to receiver
        path = list(reversed(path))
        self.controller.forward_content_path(source, receiver, path)
        self.controller.end_session()
