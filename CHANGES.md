# `bw_graph_tools` Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.6] - 2025-06-26

* Remove Numpy `<2` version pin
* Fix tests for upstream API changes

## [0.5] - 2024-09-10

This release is a big shift from purely functional programming to storing state in the graph traversal class instances. Storing state was necessary to support `SameNodeEachVisitGraphTraversal`, which needs to remember when a node has been visited.

The old API still works but is deprecated; please shift from `NewNodeEachVisitGraphTraversal.calculate()` to `NewNodeEachVisitGraphTraversal().traverse()`. Note that the graph traversal input configuration is now wrapped in a Pydantic class `GraphTraversalSettings`.

* [#21 Clean up changes from shift to stateful calculations](https://github.com/brightway-lca/bw_graph_tools/pull/21)
* [#20 Add `SameNodeEachVisitGraphTraversal`](https://github.com/brightway-lca/bw_graph_tools/pull/20)
* [#17 Major documentation upgrade](https://github.com/brightway-lca/bw_graph_tools/pull/17)

## [0.4.1] - 2024-05-24

* Fix [#16](https://github.com/brightway-lca/bw_graph_tools/issues/16) - Add optional `max_depth` argument to graph traversal

## [0.4] - 2024-05-24

Added the following attributes to `Node` dataclasses:

* direct_emissions_score_outside_specific_flows (float): The score attributable to *direct emissions* of this node which isn't broken out into separate `Flow` objects.
* remaining_cumulative_score_outside_specific_flows (float): The *cumulative* score of this node, including direct emissions, which isn't broken out into separate `Flow` objects.
* terminal (bool): Boolean flag indicating whether graph traversal was cutoff at this node

## [0.3.1] - 2024-05-11

* Fix [#18 - Duplication of values from first heuristic](https://github.com/brightway-lca/bw_graph_tools/issues/18)
* Update packaging
* Python 3.9 compatibility

## [0.3] - 2023-10-13

* Remove `scikit-network` dependency

## [0.2.5] - 2023-08-08

* Updated CI scripts

## [0.2.4] - 2023-08-08

* Fix [#8: `traverse_edges` returns when values below cutoff or excluded](https://github.com/brightway-lca/bw_graph_tools/issues/8)

## [0.2.3] - 2023-05-22

* Fix scikit-network dependency as API changed in new version

## [0.2.2] - 2023-05-08

* Refactor some testing functions

## [0.2.1] - 2023-05-07

* Fix dependencies for pip installation

## [0.2.0] - 2023-05-07

* Corrected graph traversal scaling and switched to `NewNodeEachVisitGraphTraversal` class name.
* Fixed bug in first heuristic for guessing production exchanges
* Integration tests for graph traversal

## [0.1.0] - 2023-04-26

First release

### Added

### Changed

### Removed
