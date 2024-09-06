from pprint import pprint
from typing import List, Optional, Union

from .base import GraphTraversalException
from .graph_objects import Node
from .new_node_each_visit import NewNodeEachVisitGraphTraversal


class SameNodeEachVisitGraphTraversal(NewNodeEachVisitGraphTraversal):
    """
    A stateful graph traversal that keeps track of which nodes have been visited already.

    Because each node in the database corresponds to one and one one `Node` instance in this class,
    some simplifications to our data structures can be made.
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.visited_nodes = set()

    def traverse(
        self,
        nodes: List[Node] = None,
        max_depth: int = None,
    ) -> None:
        """
        Perform graph traversal from the given `Node` instances, or from the functional unit.

        Repeat calls to traverse from the same node(s) will raise a `GraphTraversalException`.
        See `traverse_from_node` for a safe version of repeated calls for traversal.

        Parameters
        ----------
        nodes : list[Node]
            List of `Node` instances to traverse from. Uses `self._root_node` as the default.
        max_depth : int
            Maximum depth in the supply chain traversal. Default is no maximum.

        Returns
        -------
        `None`
            Modifies the class object's state in-place

        """
        if nodes is None and self._root_node.unique_id in self.visited_nodes:
            raise GraphTraversalException("The root node has already been traversed")
        elif nodes:
            if seen := {node for node in nodes if node.unique_id in self.visited_nodes}:
                err = "\n".join([pprint(node) for node in seen])
                raise GraphTraversalException(
                    f"The following nodes have been traversed already:\n{err}"
                )
        super().traverse(nodes, max_depth=max_depth)

    def traverse_edges(self, *args, **kwargs) -> None:
        super().traverse_edges(*args, **kwargs)
        self.visited_nodes.add(kwargs["consumer_unique_id"])

    def traverse_from_node(
        self, node: Union[int, Node], max_depth: Optional[int] = None
    ) -> bool:
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

        self.traverse(
            nodes=[node],
            max_depth=node.depth + 1 if max_depth is None else max_depth,
        )
        self.visited_nodes.add(node.unique_id)

        return True
