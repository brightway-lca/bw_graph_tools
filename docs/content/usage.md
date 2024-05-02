# Usage

`bw_graph_tools` has three main components: A graph traversal class `NewNodeEachVisitGraphTraversal`; a function to guess production exchanges using only `bw_processing` datapackages `guess_production_exchanges`; and a function to find the path from node `A` to node `B` with the largest amount of the reference product of `A`, `get_path_from_matrix` and it's sister `path_as_brightway_objects`.

### `NewNodeEachVisitGraphTraversal`

Normally we construct matrices and solve the resulting set of linear equations to get a life cycle inventory or impact assessment result. The matrix approach is elegant, in that it simultaneously solves all equations and handles cycles in the graph, and much faster than graph traversal. However, in some cases we want to actually traverse the supply chain graph and calculate the individual impact of visiting nodes at that point in the graph. Graph traversal's use cases include:

* Distinguishing between different paths to the same object
* Convolving temporal distributions

If we add temporal information using `bw_temporalis`, then the same node can occur at different times depending on how the temporal dynamics its preceding path. For example:

## Some Examples

- [`1 - Spatiotemporal calculations.ipynb`](https://github.com/brightway-lca/from-the-ground-up/blob/327e2af95249135a71a57cfb3eb0c7d73f6e5239/spatiotemporal/1%20-%20Spatiotemporal%20calculations.ipynb#L16)
- [`1 - Introduction.ipynb`](https://github.com/brightway-lca/from-the-ground-up/blob/327e2af95249135a71a57cfb3eb0c7d73f6e5239/temporal/1%20-%20Introduction.ipynb#L215)
- [`Example usage.ipynb`](https://github.com/brightway-lca/bw_temporalis/blob/911a7729d5ac065bbae862df5c1381aa1058cf48/dev/Example%20usage.ipynb#L17)
