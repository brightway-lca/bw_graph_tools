from typing import Optional, Union

from .new_node_each_visit import NewNodeEachVisitGraphTraversal
from .graph_objects import Node


class SameNodeEachVisitGraphTraversal(NewNodeEachVisitGraphTraversal):
    """
    A stateful graph traversal that keeps track of which nodes have been
    visited already, allowing for a partial and dynamic traversal of the graph.
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.visited_nodes = set()

    def traverse(
            self,
            nodes: list = None,
            max_depth: int = None,
    ) -> None:
        super().traverse(nodes=nodes, max_depth=max_depth)
        for node in self._nodes.values():
            if node.terminal is False or node is self._root_node:
                self.visited_nodes.add(node.unique_id)

    def traverse_from_node(self, node: Union[int, Node], max_depth: Optional[int] = None) -> bool:
        """
        Traverse the graph starting from the specified node and exp
        returning a boolean indicating if the node traversed already

        Parameters
        ----------
        node
            either the node's unique id or a `Node` object
        max_depth
            max depth to traverse from this node, otherwise will default to `node.depth + 1`

        Returns
        -------
        bool
            indicates if the node was traversed
        """
        if isinstance(node, int):
            node = self.nodes[node]
        if node.unique_id in self.visited_nodes:
            return False

        self.visited_nodes.add(node.unique_id)
        self.traverse(
            nodes=[node],
            max_depth=node.depth + 1 if max_depth is None else max_depth,
        )

        return True
