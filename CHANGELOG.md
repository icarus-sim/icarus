# CHANGELOG

## 0.8.0

* Migrate all tests from unittest to pytest
* Fix PEP 479 compliance issues
* Drop support for Python 3.4 and add support for python 3.8
* Move CI to Github actions
* Add latency models for hash-routing strategies
* Add Fagin's model of LRU cache hit ratio
* Improve speed of characteristic time numerical computation
* Improve coverage of test cases for characteristic time approximations
* Improvements to PEP8 compliance
* Bug-fix: icarus/results/plot.py: set title when specified
* Fix deprecations warnings up to Python 3.8
* Port to Networkx 2.x and remove support for Networkx 1.x
* Fixes and improvements to examples

## 0.7.0

* Style fixes
* Pin to NetworkX version 1.x
* Add Docker support
* Remove script and consolidate all functionalities in `icarus` command
* Proper packaging and installation with `make install`
* Fix bug in icarus.util.apportionment
* Fix randomly failing test cases

## 0.6.0

* Add Perfect LFU, MIN and CLIMB replacement policies
* Add new hash-routing caching strategies
* Add ring and mesh topologies
* Add many new cache placement algorithms
* Add YCSB workload
* Add generalized Che's approximation
* Add support for dynamic node/link removal/restore and link rewiring
* Improve Python 3 compatibility
* Port test cases to py.test
* Code refactoring
* Bug fixes

## 0.5.0

* Add RocketFuel topologies
* Add trace-driven workload
* Great performance improvement with large catalogues
* Refactoring and documentation improvement
* Bug fixes
* Add Edge and Nearest Replica Routing strategies
* Add parsers for UMass YouTube and URL list traces

## 0.4.0

* Major refactoring
* Add TTL cache implementation
* Add key-val cache implementation
* Improve trace parsers

## 0.3.0

* Improve LRU cache policy implementation
* Add Segmented LRU policy
* Improve logging with clearer output information and add printing of error
  messages with traceback in parallel execution mode
* Add function for plotting CDFs
* Considerably improve existing plotting functions
* Add graph visualization functions
* Add examples section
* Add support for NetworkX 1.9
* Various bug fixes

## 0.2.1

* Added API reference documentation
* Fixed bug in Hashrouting Hybrid AM strategy
* Fixed bug in CL4M strategy
* Added test cases for routing and caching strategies

## 0.2

* Major refactoring
* Add new models
* Add tools for modelling cache performance and processing content request traces

## 0.1.1

* Version used to generate results for hash-routing ICN'13 paper

## 0.1

* Initial version
