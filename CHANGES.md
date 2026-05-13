# `bw_graph_tools` Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.8] - 2026-05-13

* [#43 Add fourth and fifth production-exchange heuristics](https://github.com/brightway-lca/bw_graph_tools/pull/43): `gpe_fourth_heuristic` identifies waste treatment activities by finding columns with a single negative entry in the assembled matrix; `gpe_fifth_heuristic` deterministically resolves remaining columns by finding products that appear in exactly one unidentified column (columns with multiple candidate rows are left unassigned rather than guessed); both are wired into `guess_production_exchanges`
* [#43](https://github.com/brightway-lca/bw_graph_tools/pull/43): Added docstrings to `gpe_second_heuristic`, `gpe_third_heuristic`, and all new heuristic functions; added early-return guards to heuristics 2–4; documented a known ordering limitation in `gpe_third_heuristic` (can misidentify waste-treatment co-product as production exchange before the fourth heuristic runs) with an xfail test
* [#43](https://github.com/brightway-lca/bw_graph_tools/pull/43): Removed unused `reorder_mapped_matrix` stub

## [0.7] - 2026-04-15

* [#36 Injectable `CachingSolver` with external cache pre-population](https://github.com/brightway-lca/bw_graph_tools/pull/36): New `caching_solver` field on `GraphTraversalSettings` allows sharing a solver across multiple traversals; `CachingSolver` now exposes `in_cache()` and `add_to_cache()` for external pre-population
* [#39 Warn when graph traversal coverage is below threshold](https://github.com/brightway-lca/bw_graph_tools/pull/39): New `min_coverage_fraction` field on `GraphTraversalSettings` (default 0.9); emits a warning if traversal covers less than the threshold fraction of total LCA score
* [#38 Replace deprecated `np.in1d` with `np.isin`](https://github.com/brightway-lca/bw_graph_tools/pull/38): Fixes `AttributeError` with NumPy ≥ 2.0
* [#32 Ensure `static_activity_indices` are added to the graph](https://github.com/brightway-lca/bw_graph_tools/pull/32)

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
