import hashlib
from dataclasses import dataclass, field
from typing import List, Dict, Tuple, Union, Optional, Set

import bw2data as bd

from bw_graph_tools.graph_traversal import SameNodeEachVisitGraphTraversal
from bw_graph_tools.graph_traversal.base import BaseGraphTraversal
from bw_graph_tools.graph_traversal.graph_objects import GroupedNodes, Edge, Node
from bw_graph_tools.graph_traversal.new_node_each_visit import SupplyChainTraversalSettings, \
    NewNodeEachVisitGraphTraversal


@dataclass
class TaggedSupplyChainTraversalSettings(SupplyChainTraversalSettings):
    """
    Supply Chain Traversal Settings with a functional unit tag

    Parameters
    ----------
    tags : List[str]
        A list of tags to group nodes by
    """

    tags: List[str] = field(default_factory=list)


class NewNodeEachVisitTaggedGraphTraversal(NewNodeEachVisitGraphTraversal,
                                           BaseGraphTraversal[TaggedSupplyChainTraversalSettings]):
    """
    Traverse the graph with leaves nodes grouped by their tags
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._tagged_nodes = {}
        self._tagged_edges = []
        self._tagged_flows = []

    def generate_id_for_grouped_node(self, parent_node: Node, node: Node, tag_group: str) -> int:
        """
        Generate an id for a grouped node
        """
        return next(self._calculation_count)

    def should_group_leaves_for_parent(self, parent_node: Node) -> bool:
        """
        Whether to group leaves for a specific parent
        """
        return True

    def traverse(
            self,
            nodes: list = None,
            max_depth: int = None,
    ) -> None:
        super().traverse(nodes=nodes, max_depth=max_depth)

        non_terminal_nodes = {edge.consumer_unique_id for edge in self._edges}

        grouped_nodes: Dict[str, GroupedNodes] = {}
        edges: Dict[Tuple[int, int], Edge] = {}
        self._tagged_edges = []
        self._tagged_nodes = {}
        self._tagged_flows = {}

        leaf_nodes_by_parent: Dict[str, Set[int]] = {}
        for edge in self._edges:
            if edge.producer_unique_id not in non_terminal_nodes:
                leaf_nodes_by_parent.setdefault(edge.consumer_unique_id, set()).add(edge.producer_unique_id)

        for parent, children in leaf_nodes_by_parent.items():
            parent_node = self._nodes[parent]
            if not self.should_group_leaves_for_parent(parent_node):
                continue
            nodes_by_tags = {}
            for node_id in children:
                node = self._nodes[node_id]
                activity = bd.get_activity(id=node.activity_datapackage_id)
                atags = activity.get("tags", None) or {}
                if all([atags.get(tag, None) is None for tag in self.settings.tags]):
                    # means that no tags are set on this node, just add the node
                    self._tagged_nodes[node_id] = node
                    continue
                label = ' '.join(['{}: {}'.format(tag, atags.get(tag, None) or "") for tag in self.settings.tags])
                nodes_by_tags.setdefault(label, []).append(node)

            for tag_group, nodes in nodes_by_tags.items():
                lookup = self.generate_id_for_grouped_node(parent_node, nodes[0], tag_group)
                gn = GroupedNodes(
                    nodes=nodes,
                    label=tag_group,
                    unique_id=lookup,
                    depth=nodes[0].depth,
                    supply_amount=0,
                    cumulative_score=0,
                    direct_emissions_score=0,
                    direct_emissions_score_outside_specific_flows=0,
                    terminal=True
                )

                for node in nodes:
                    gn.supply_amount += node.supply_amount
                    gn.cumulative_score += node.cumulative_score
                    gn.direct_emissions_score += node.direct_emissions_score
                    gn.direct_emissions_score_outside_specific_flows += node.direct_emissions_score_outside_specific_flows

                self._tagged_nodes[gn.unique_id] = gn
                grouped_nodes[gn.unique_id] = gn

        visited_group_nodes = {
            gn_node.unique_id
            for gn in grouped_nodes.values()
            for gn_node in gn.nodes
        }
        for idx, node in self._nodes.items():
            if node.unique_id in self._tagged_nodes or node.unique_id in visited_group_nodes:
                continue
            self._tagged_nodes[idx] = node

        for edge in self._edges:
            if edge.consumer_unique_id in self._tagged_nodes and edge.producer_unique_id in self._tagged_nodes:
                self._tagged_edges.append(edge)
                continue
            # we have to now search from the missing edge
            for gn in grouped_nodes.values():
                for node in gn.nodes:
                    if edge.producer_unique_id == node.unique_id:
                        gedge = edges.setdefault((edge.consumer_unique_id, gn.unique_id), Edge(
                            consumer_index=edge.consumer_index,
                            consumer_unique_id=edge.consumer_unique_id,
                            producer_index=None,
                            producer_unique_id=gn.unique_id,
                            product_index=None,
                            amount=0,
                        ))
                        gedge.amount += edge.amount

        self._tagged_edges.extend(edges.values())

    @property
    def nodes(self):
        return self._tagged_nodes

    @property
    def edges(self):
        return self._tagged_edges

    @property
    def flows(self):
        return self._tagged_flows


class SameNodeEachVisitTaggedGraphTraversal(NewNodeEachVisitTaggedGraphTraversal, SameNodeEachVisitGraphTraversal):
    """
    A tagged variant of same node each visit
    """

    def generate_id_for_grouped_node(self, parent_node: Node, node: Node, tag_group: str) -> int:
        """
        Generate a consistent id for a grouped node
        """
        label_parent_depth = '{}:{}:{}'.format(parent_node.unique_id, node.depth, tag_group)
        lookup = hashlib.sha256(label_parent_depth.encode()).hexdigest()[16]
        return int(lookup, 16)

    def traverse_from_node(self, node: Union[int, Node], max_depth: Optional[int] = None) -> bool:
        if isinstance(node, int):
            node = self.nodes[node]
        if isinstance(node, GroupedNodes):
            if node.unique_id in self.visited_nodes:
                return False
            self.visited_nodes.add(node.unique_id)
            for child_node in node.nodes:
                self.visited_nodes.add(child_node.unique_id)
            super().traverse(nodes=node.nodes, max_depth=node.depth + 1 if max_depth is None else max_depth)
            return True
        return super().traverse_from_node(node=node, max_depth=max_depth)
