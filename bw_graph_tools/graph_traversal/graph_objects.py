from dataclasses import dataclass
from typing import List, Optional


@dataclass
class Node:
    """
    A visited activity in a supply chain graph. Although our graph is cyclic, we treat each
    activity as a separate node every time we visit it.

    Parameters
    ----------
    unique_id : int
        A unique integer id for this visit to this activity node
    activity_datapackage_id : int
        The id that identifies this activity in the datapackage, and hence in the database
    activity_index : int
        The technosphere matrix column index of this activity
    reference_product_datapackage_id : int
        The id that identifies the reference product of this activity in the datapackage
    reference_product_index : int
        The technosphere matrix row index of this activity's reference product
    reference_product_production_amount : float
        The *net* production amount of this activity's reference product
    depth : int
        Depth in the supply chain graph, starting from 0 as the functional unit
    supply_amount : float
        The amount of the *activity* (not reference product!) needed to supply the demand from the
        requesting supply chain edge.
    cumulative_score : float
        Total LCIA score attributed to `supply_amount` of this activity, including impacts from
        direct emissions.
    direct_emissions_score : float
        Total LCIA score attributed only to the direct characterized biosphere flows of
        `supply_amount` of this activity.
    direct_emissions_score_outside_specific_flows : float
        The score attributable to *direct emissions* of this node which isn't broken out into
        separate `Flow` objects.
    remaining_cumulative_score_outside_specific_flows : float
        The *cumulative* score of this node, including direct emissions, which isn't broken out
        into separate `Flow` objects.
    terminal : bool
        Boolean flag indicating whether graph traversal was cutoff at this node

    """

    unique_id: int
    activity_datapackage_id: int
    activity_index: int
    reference_product_datapackage_id: int
    reference_product_index: int
    reference_product_production_amount: float
    depth: int
    supply_amount: float
    cumulative_score: float
    direct_emissions_score: float
    max_depth: Optional[int] = None
    direct_emissions_score_outside_specific_flows: float = 0.0
    remaining_cumulative_score_outside_specific_flows: float = 0.0
    terminal: bool = False

    def __lt__(self, other):
        # Needed for sorting
        return self.cumulative_score < other.cumulative_score


@dataclass
class GroupedNodes:
    """
    A group of nodes
    """

    nodes: List[Node]
    label: str
    unique_id: int
    depth: int
    supply_amount: float
    cumulative_score: float
    direct_emissions_score: float
    max_depth: Optional[int] = None
    direct_emissions_score_outside_specific_flows: float = 0.0
    terminal: bool = False
    activity_index: int = None

    def __lt__(self, other):
        # Needed for sorting
        return self.cumulative_score < other.cumulative_score


@dataclass
class Edge:
    """
    An edge between two `Node` instances. The `amount` is the amount of the product demanded by the
    `consumer`.

    Parameters
    ----------
    consumer_index : int
        The matrix column index of the consuming activity
    consumer_unique_id : int
        The traversal-specific unique id of the consuming activity
    producer_index : int
        The matrix column index of the producing activity
    producer_unique_id : int
        The traversal-specific unique id of the producing activity
    product_index : int
        The matrix row index of the consumed product
    amount : float
        The amount of the product demanded by the consumer. Not scaled to producer production
        amount.
    """

    consumer_index: int
    consumer_unique_id: int
    producer_index: int
    producer_unique_id: int
    product_index: int
    amount: float


@dataclass
class Flow:
    """
    A characterized biosphere flow associated with a given `Node` instance.

    Parameters
    ----------
    flow_datapackage_id : int
        The id that identifies the biosphere flow in the datapackage
    flow_index : int
        The matrix row index of the biosphere flow
    activity_unique_id : int
        The `Node.unique_id` of this instance of the emitting activity
    activity_id : int
        The id that identifies the emitting activity in the datapackage
    activity_index : int
        The matrix column index of the emitting activity
    amount : float
        The amount of the biosphere flow being emitting by this activity instance
    score : float
        The LCIA score for `amount` of this biosphere flow
    """

    flow_datapackage_id: int
    flow_index: int
    activity_unique_id: int
    activity_id: int
    activity_index: int
    amount: float
    score: float

    def __lt__(self, other):
        # Needed for sorting
        return self.score < other.score
