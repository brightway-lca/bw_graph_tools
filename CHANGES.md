# `bw_graph_tools` Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

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
