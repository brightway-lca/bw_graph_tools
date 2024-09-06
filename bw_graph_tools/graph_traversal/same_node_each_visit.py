from typing import Optional, Union

from .base import GraphTraversalException
from .graph_objects import Node
from .new_node_each_visit import NewNodeEachVisitGraphTraversal


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
        """
        Perform the graph traversal.

        Repeat calls to traverse from the same node or root node will raise an Exception.
        See `traverse_from_node` for a safe version of repeated calls for traversal.

        Parameters
        ----------
        nodes : list
            list of nodes to traverse, otherwise uses the root node as the starting point
        max_depth : int
            Maximum depth in the supply chain traversal. Default is no maximum.

        Returns
        -------
        `None`
            Modifies the class object's state in-place

        """
        if nodes is None and self._root_node.unique_id in self.visited_nodes:
            raise GraphTraversalException("the root node has already been traversed")
        elif nodes:
            visited_nodes = [node for node in nodes if node.unique_id in self.visited_nodes]
            if visited_nodes:
                raise GraphTraversalException("some node(s) have already been traversed".format(len(visited_nodes)),
                                              visited_nodes)
        super().traverse(nodes, max_depth=max_depth)

    def traverse_edges(
            self,
            *args,
            **kwargs
    ) -> None:
        super().traverse_edges(*args, **kwargs)
        self.visited_nodes.add(kwargs['consumer_unique_id'])

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
