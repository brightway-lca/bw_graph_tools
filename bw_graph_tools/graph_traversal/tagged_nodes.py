import hashlib
from collections import defaultdict
from typing import Dict, Iterable, List, Optional, Set, Tuple, Union

import bw2data as bd

from bw_graph_tools.graph_traversal import SameNodeEachVisitGraphTraversal
from bw_graph_tools.graph_traversal.base import BaseGraphTraversal
from bw_graph_tools.graph_traversal.graph_objects import Edge, Flow, GroupedNodes, Node
from bw_graph_tools.graph_traversal.new_node_each_visit import NewNodeEachVisitGraphTraversal
from bw_graph_tools.graph_traversal.settings import TaggedGraphTraversalSettings


class NewNodeEachVisitTaggedGraphTraversal(
    NewNodeEachVisitGraphTraversal,
    BaseGraphTraversal[TaggedGraphTraversalSettings],
):
    """
    Traverse the graph with leaves nodes grouped by their tags
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._tagged_nodes: Dict[int, Union[GroupedNodes, Node]] = {}
        self._tagged_edges: List[Edge] = []
        self._tagged_flows: List[Flow] = []

    @classmethod
    def group_nodes_by_tags(
        cls, children: Iterable[Node], tags: List[str]
    ) -> Dict[str, List[Node]]:
        """
        Organize child nodes by their tags for a given parent node.

        Groups child nodes based on the tags found in their associated activity

        Parameters
        ----------
        children : set
            A set of child nodes to be organized by tags.
        tags : list
            A list of string for the nodes to be grouped by

        Returns
        -------
        nodes_by_tags : dict
            A dictionary where the keys are tag labels and the values are lists of nodes
            grouped by those tags. Nodes with no applicable tags are grouped under an empty string.
        """
        nodes_by_tags = {
            # nodes with no applicable tags
            "": []
        }
        for node in children:
            activity = bd.get_activity(id=node.activity_datapackage_id)
            atags = activity.get("tags", None) or {}

            if all([atags.get(tag, None) is None for tag in tags]):
                # means that no tags are set on this node
                nodes_by_tags[""].append(node)
                continue
            label = ",".join(["{}: {}".format(tag, atags.get(tag, None) or "") for tag in tags])
            nodes_by_tags.setdefault(label, []).append(node)
        return nodes_by_tags

    @classmethod
    def group_leaf_nodes_by_parent(cls, edges: List[Edge]):
        """
        Group leaf nodes by their parent nodes.

        Identifies leaf nodes (nodes that are terminal) and groups them
        according to their parent nodes.

        Parameters
        ----------
        edges: list
            A list of graph edges

        Returns
        -------
        leaf_nodes_by_parent : dict
            A dictionary where the keys are parent node IDs and the values are sets of
            child node IDs (leaf nodes).
        """
        non_terminal_nodes = {edge.consumer_unique_id for edge in edges}
        leaf_nodes_by_parent: Dict[int, Set[int]] = defaultdict(set)
        for edge in edges:
            if edge.producer_unique_id not in non_terminal_nodes:
                leaf_nodes_by_parent[edge.consumer_unique_id].add(edge.producer_unique_id)
        return leaf_nodes_by_parent

    def generate_id_for_grouped_node(
        self, parent_node: Node, nodes: List[Node], tag_group: str
    ) -> int:
        """
        Generate an id for a grouped node

        Parameters
        ----------
        parent_node: Node
            parent node
        nodes: List[Node]
            nodes that belong to the parent
        tag_group: str
            tag value for this group

        Returns
        -------
        int
            unique id for GroupedNodes
        """
        return next(self._calculation_count)

    def should_group_leaves(self, parent_node: Node, nodes: List[Node], tag_group: str) -> bool:
        """
        Whether to group leaves for a specific parent and tag group
        """
        return True

    def create_group_tagged_nodes(
        self, parent_node, nodes_by_tags, grouped_edges
    ) -> Tuple[Dict[int, GroupedNodes], List[Edge]]:
        """
        Create grouped nodes for child nodes that should be grouped based on their tags.

        Aggregates nodes that share the same tag group into a single grouped node, summing
        their relevant attributes.

        Parameters
        ----------
        parent_node : Node
            The parent node to which the child nodes belong.
        nodes_by_tags : dict
            A dictionary where the keys are tag labels and the values are lists of child nodes
            that share those tags.
        grouped_edges: Dict[Tuple[int, int], Edge]
            A dictionary of mapping from (consumer, producer) to Edge

        Returns
        -------
        grouped_nodes : dict
            A dictionary where the keys are unique IDs for grouped nodes, and the values are
            GroupedNodes instances representing nodes grouped by tags.
        edges: list
            A list of Edges for the newly grouped Nodes
        """
        grouped_nodes = {}
        edges = []
        for tag_group, nodes in nodes_by_tags.items():
            if not self.should_group_leaves(parent_node, nodes, tag_group):
                continue
            lookup = self.generate_id_for_grouped_node(parent_node, nodes, tag_group)
            g_node = GroupedNodes(
                nodes=nodes,
                label=tag_group,
                unique_id=lookup,
                depth=nodes[0].depth,
                supply_amount=0,
                cumulative_score=0,
                direct_emissions_score=0,
                direct_emissions_score_outside_specific_flows=0,
                terminal=True,
            )
            edge = Edge(
                consumer_index=parent_node.activity_index,
                consumer_unique_id=parent_node.unique_id,
                producer_index=None,
                producer_unique_id=g_node.unique_id,
                product_index=None,
                amount=0,
            )
            for node in nodes:
                # handle node aggregation
                g_node.supply_amount += node.supply_amount
                g_node.cumulative_score += node.cumulative_score
                g_node.direct_emissions_score += node.direct_emissions_score
                g_node.direct_emissions_score_outside_specific_flows += (
                    node.direct_emissions_score_outside_specific_flows
                )

                # handle edge aggregation
                node_edge = grouped_edges.get((parent_node.unique_id, node.unique_id))
                edge.amount += node_edge.amount

            grouped_nodes[g_node.unique_id] = g_node
            edges.append(edge)
        return grouped_nodes, edges

    def traverse(
        self,
        nodes: list = None,
        depth: int = None,
    ) -> None:
        super().traverse(nodes=nodes, depth=depth)

        grouped_nodes: Dict[int, GroupedNodes] = {}
        edges: Dict[Tuple[int, int], Edge] = {
            (edge.consumer_unique_id, edge.producer_unique_id): edge for edge in self._edges
        }
        self._tagged_edges = []
        self._tagged_nodes = {}
        self._tagged_flows = {}

        leaf_nodes_by_parent = self.group_leaf_nodes_by_parent(self._edges)

        for parent, children in leaf_nodes_by_parent.items():
            parent_node = self._nodes[parent]
            nodes_by_tags = self.group_nodes_by_tags(
                map(lambda x: self._nodes[x], children), self.settings.tags
            )
            if untagged_nodes := nodes_by_tags.pop(""):
                self._tagged_nodes.update({node.unique_id: node for node in untagged_nodes})
            gnodes, gedges = self.create_group_tagged_nodes(parent_node, nodes_by_tags, edges)
            grouped_nodes.update(gnodes)
            self._tagged_edges.extend(gedges)

        visited_group_nodes = {
            gn_node.unique_id for gn in grouped_nodes.values() for gn_node in gn.nodes
        }
        # add nodes that may have been excluded from groupings
        missing_nodes = {
            idx: node
            for idx, node in self._nodes.items()
            if node.unique_id not in self._tagged_nodes
            and node.unique_id not in visited_group_nodes
        }
        self._tagged_nodes.update(missing_nodes)

        # add remaining edges
        missing_edges = [
            edge
            for edge in self._edges
            if edge.consumer_unique_id in self._tagged_nodes
            and edge.producer_unique_id in self._tagged_nodes
        ]

        self._tagged_edges.extend(missing_edges)
        self._tagged_nodes.update(grouped_nodes)

    @property
    def nodes(self):
        return self._tagged_nodes

    @property
    def edges(self):
        return self._tagged_edges

    @property
    def flows(self):
        return self._tagged_flows


class SameNodeEachVisitTaggedGraphTraversal(
    NewNodeEachVisitTaggedGraphTraversal, SameNodeEachVisitGraphTraversal
):
    """
    A tagged variant of same node each visit
    """

    def generate_id_for_grouped_node(
        self, parent_node: Node, nodes: List[Node], tag_group: str
    ) -> int:
        """
        Generate a consistent id for a grouped node
        """
        label_parent_depth = "{}:{}:{}".format(parent_node.unique_id, nodes[0].depth, tag_group)
        lookup = hashlib.sha256(label_parent_depth.encode()).hexdigest()[16]
        return int(lookup, 16)

    def should_group_leaves(self, parent_node: Node, nodes: List[Node], tag_group: str) -> bool:
        gen_id = self.generate_id_for_grouped_node(parent_node, nodes, tag_group)
        return gen_id not in self.visited_nodes

    def traverse_from_node(self, node: Union[int, Node], depth: Optional[int] = 1) -> bool:
        if isinstance(node, int):
            node = self.nodes[node]
        if isinstance(node, GroupedNodes):
            if node.unique_id in self.visited_nodes:
                return False
            self.visited_nodes.add(node.unique_id)
            super().traverse(
                nodes=node.nodes,
                depth=depth,
            )
            return True
        return super().traverse_from_node(node=node, depth=depth)
