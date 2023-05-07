from typing import List, Optional

from bw2calc import LCA
from scipy import sparse
import sknetwork as skn

from .matrix_tools import to_normalized_adjacency_matrix

try:
    import bw2data as bd
    from bw2data import Edge, Node

    brightway_available = True
except ImportError:

    class Dummy:
        def get_node(self):
            pass

    bd, Node, Edge = Dummy(), Dummy(), Dummy()
    brightway_available = False


def get_path_from_matrix(
    matrix: sparse.spmatrix, source: int, target: int, algorithm: str = "BF"
) -> List:
    """Get the path with the most mass or energetic flow from ``source`` (the function unit) to ``target`` (something deep in the supply chain). Both ``source`` and ``target`` are integer matrix indices.

    ``algorithm`` should be either ``BF`` (Bellman-Ford) or ``J`` (Johnson). Dijkstra is not recommended as we have negative weights.

    Returns a list like ``[source, int, int, int, target]``."""
    return skn.path.get_shortest_path(
        adjacency=to_normalized_adjacency_matrix(matrix=matrix),
        sources=source,
        targets=target,
        method=algorithm,
        unweighted=False,
    )


def path_as_brightway_objects(
    source_node: Node, target_node: Node, lca: Optional[LCA] = None
) -> List[Edge]:
    if not brightway_available:
        raise ImportError("Brightway not available")

    if lca is None:
        lca = LCA({source_node: 1, target_node: 1})
        lca.lci()

    path = skn.path.get_shortest_path(
        adjacency=to_normalized_adjacency_matrix(matrix=lca.technosphere_mm.matrix),
        sources=lca.activity_dict[source_node.id],
        targets=lca.activity_dict[target_node.id],
        method="BF",
        unweighted=False,
    )

    return [
        (
            bd.get_node(id=lca.dicts.product.reversed[x]),
            bd.get_node(id=lca.dicts.activity.reversed[y]),
            -1
            * lca.technosphere_matrix[
                y, x
            ],  # Flip x and y because y is input to activity x
        )
        for x, y in zip(path[:-1], path[1:])
    ]
