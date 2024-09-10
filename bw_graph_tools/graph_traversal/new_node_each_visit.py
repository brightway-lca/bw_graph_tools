import warnings
from heapq import heappop, heappush
from typing import Dict, List, Optional

import matrix_utils as mu
import numpy as np
from bw2calc import LCA
from scipy.sparse import spmatrix
from typing_extensions import deprecated

try:
    from bw2data import databases
except ImportError:
    databases = {}

from bw_graph_tools.graph_traversal.base import BaseGraphTraversal
from bw_graph_tools.graph_traversal.graph_objects import Edge, Flow, Node
from bw_graph_tools.graph_traversal.settings import GraphTraversalSettings
from bw_graph_tools.graph_traversal.utils import (
    CachingSolver,
    Counter,
    get_demand_vector_for_activity,
)
from bw_graph_tools.matrix_tools import guess_production_exchanges


class NewNodeEachVisitGraphTraversal(BaseGraphTraversal[GraphTraversalSettings]):
    """
    Traverse a supply chain, following paths of greatest impact.

    This implementation uses a queue of datasets to assess. As the supply chain is traversed,
    activities are added to a list sorted by LCA score. Each activity in the sorted list is
    assessed, and added to the supply chain graph, as long as its impact is above a certain
    threshold, and the maximum number of calculations has not been exceeded.

    Because the next dataset assessed is chosen by its impact, not its position in the graph, this
    is neither a breadth-first nor a depth-first search, but rather "importance-first".

    Priority-first traversal (i.e. follow the past of highest score) of the supply chain graph.
    This class unrolls the graph, i.e. every time it arrives at a given activity, it treats
    it as a separate node in the graph.

    In contrast with previous graph traversal implementations, we do not assume reference
    production exchanges are on the diagonal. It should also correctly handle the following:

    * Functional unit has more than one link to a given product
    * Non-unitary reference production amounts
    * Negative reference production amounts
    * Co-production edge traversal, if desired. Requires co-products to be substituted (can be
        implicit substitution).

    You must provide an `lca_object` which is already instantiated, and for which you have
    already done LCI and LCIA calculations. The `lca_object` does not have to be an instance of
    `bw2calc.LCA`, but it needs to support the following methods and attributes:

    * `technosphere_matrix`
    * `technosphere_mm`
    * `solve_linear_system()`
    * `demand`
    * `demand_array`

    You can subclass `NewNodeEachVisitGraphTraversal` and redefine
    `get_characterized_biosphere` if your LCA class does not have a traditional
    `characterization_matrix` and `biosphere_matrix`. For example, regionalization has its
    own characterization framework without a single `characterization_matrix`.

    Without further manipulation, the results will have double counting if you add all scores
    together. Specifically, each `Node` has both a `cumulative_score` and a
    `direct_emissions_score`; the `cumulative_score` **includes** the `direct_emissions_score`.
    See the following attributes of the `Node` object to find the numbers you are looking for
    in your specific case:

    * cumulative_score
    * direct_emissions_score
    * direct_emissions_score_outside_specific_flows
    * remaining_cumulative_score_outside_specific_flows

    .. warning:: Graph traversal with multioutput processes only works when other inputs are
        substituted (see `Multioutput processes in LCA <http://chris.mutel.org/multioutput.html>`__
        for a description of multiputput process math in LCA).

    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        total_score = self.lca.score
        if total_score == 0:
            raise ValueError("Zero total LCA score makes traversal impossible")

        self.cutoff_score = abs(total_score * self.settings.cutoff)
        self.biosphere_cutoff_score = abs(total_score * self.settings.biosphere_cutoff)
        self.production_exchange_mapping = {
            x: y for x, y in zip(*self.get_production_exchanges(self.lca.technosphere_mm))
        }
        self._calculation_count = Counter()
        self.characterized_biosphere = self.get_characterized_biosphere(self.lca)

    @classmethod
    @deprecated(
        "Use `NewNodeEachVisitGraphTraversal(lca, settings)` instead of `NNEVGT().calculate(stuff)`"
    )
    def calculate(
        cls,
        lca_object: LCA,
        cutoff: Optional[float] = 5e-3,
        biosphere_cutoff: Optional[float] = 1e-4,
        max_calc: Optional[int] = 1000,
        max_depth: Optional[int] = None,
        skip_coproducts: Optional[bool] = False,
        separate_biosphere_flows: Optional[bool] = True,
        static_activity_indices: Optional[set[int]] = set(),
        functional_unit_unique_id: Optional[int] = -1,
    ) -> dict:
        """
        Priority-first traversal (i.e. follow the past of highest score) of the supply chain graph.
        This class unrolls the graph, i.e. every time it arrives at a given activity, it treats
        it as a separate node in the graph.

        In contrast with previous graph traversal implementations, we do not assume reference
        production exchanges are on the diagonal. It should also correctly handle the following:

        * Functional unit has more than one link to a given product
        * Non-unitary reference production amounts
        * Negative reference production amounts
        * Co-production edge traversal, if desired. Requires co-products to be substituted (can be
            implicit substitution).

        You must provide an `lca_object` which is already instantiated, and for which you have
        already done LCI and LCIA calculations. The `lca_object` does not have to be an instance of
        `bw2calc.LCA`, but it needs to support the following methods and attributes:

        * `technosphere_matrix`
        * `technosphere_mm`
        * `solve_linear_system()`
        * `demand`
        * `demand_array`

        You can subclass `NewNodeEachVisitGraphTraversal` and redefine
        `get_characterized_biosphere` if your LCA class does not have a traditional
        `characterization_matrix` and `biosphere_matrix`. For example, regionalization has its
        own characterization framework without a single `characterization_matrix`.

        The return object is a dictionary with four values.

        * `nodes` is a dictionary of visited **activities**; the keys in this dictionary are
            unique increasing integer ids (not related to any other ids or indices), and values are
            instances of the `Node` dataclass. Each `Node` has a `unique_id`, as every time we
            arrive at an activity (even if we have seen it before via another branch of the supply
            chain), we create a new `Node` object with a unique id. See the `Node` documentation
            for its other attributes.
        * `edges` is a list of `Edge` instances. Edges link two `Node` instances (but not `Flow`
            instances, that is handled separately). The `Edge` amount is the amount demanded of
            the producer at that point in the supply chain, scaled to the amount of the producer
            requested.
        * `flows` is a list of `Flow` instances; biosphere flows are linked to a particular `Node`.
            We apply the `biosphere_cutoff` to determine if individual biosphere flows should
            be stored separately. Will be empty is `separate_biosphere_flows` is false.

        Finally, `calculation_count` gives the total number of inventory calculations performed.

        Without further manipulation, the results will have double counting if you add all scores
        together. Specifically, each `Node` has both a `cumulative_score` and a
        `direct_emissions_score`; the `cumulative_score` **includes** the `direct_emissions_score`.
        See the following attributes of the `Node` object to find the numbers you are looking for
        in your specific case:

        * cumulative_score
        * direct_emissions_score
        * direct_emissions_score_outside_specific_flows
        * remaining_cumulative_score_outside_specific_flows

        Parameters
        ----------
        lca_object : bw2calc.LCA
            Already instantiated `LCA` object with inventory and impact
            assessment calculated.
        cutoff : float
            Cutoff value used to stop graph traversal. Fraction of total score,
            should be in `(0, 1)`
        biosphere_cutoff : float
            Cutoff value used to determine if a separate biosphere node is
            added. Fraction of total score.
        max_calc : int
            Maximum number of inventory calculations to perform
        max_depth : int
            Maximum depth in the supply chain traversal. Default is no maximum.
        skip_coproducts : bool
            Don't traverse co-production edges, i.e. production edges other
            than the reference product
        separate_biosphere_flows : bool
            Add separate `Flow` nodes for important individual biosphere
            emissions
        static_activity_indices : set
            A set of activity matrix indices which we don't want the graph to
            traverse - i.e. we stop traversal when we hit these nodes, but
            still add them to the returned `nodes` dictionary, and calculate
            their direct and cumulative scores.
        functional_unit_unique_id : int
            An integer id we can use for the functional unit virtual activity.
            Shouldn't overlap any other activity ids. Don't change unless you
            really know what you are doing.

        Returns
        -------
        dict
            Dictionary with keys `nodes`, `edges`, `flows`, `calculation_counter`

        """
        instance = cls(
            lca_object,
            GraphTraversalSettings(
                cutoff=cutoff,
                biosphere_cutoff=biosphere_cutoff,
                max_calc=max_calc,
                max_depth=max_depth,
                skip_coproducts=skip_coproducts,
                separate_biosphere_flows=separate_biosphere_flows,
            ),
            functional_unit_unique_id=functional_unit_unique_id,
            static_activity_indices=static_activity_indices,
        )

        instance.traverse()

        return {
            "nodes": instance.nodes,
            "edges": instance.edges,
            "flows": instance.flows,
            "calculation_count": instance.calculation_count,
        }

    @property
    def calculation_count(self):
        """
        gives the total number of inventory calculations performed.
        """
        return self._calculation_count.value

    def _max_depth_for_node(self, node: Node, relative_depth: Optional[int] = None) -> int:
        """Find `max_depth` for a given node when inputs are all optional."""
        if relative_depth is None and self.settings.max_depth is None:
            return None
        elif self.settings.max_depth is None:
            return node.depth + relative_depth
        elif relative_depth is None:
            return self.settings.max_depth
        else:
            return min(node.depth + relative_depth, self.settings.max_depth)

    def traverse(
        self,
        nodes: Optional[List[Node]] = None,
        depth: Optional[int] = None,
        reset_results: bool = False,
    ) -> None:
        """
        Perform the graph traversal following `NewNodeEachVisitGraphTraversal` logic.

        If `nodes` is not specified, start at the given functional unit. If `nodes` is specified,
        *only* traverse the graph starting from the given nodes. These nodes can be anywhere in the
        supply chain.

        Passing multiple `Node` objects in `nodes` must be done carefully. This function assumes
        that all such nodes should be placed on the heap together. This means that we do
        priority-first traversal based on the scores of these nodes - i.e. if node A has a much
        higher score than B, it could be that the supply chain of B is never explored at all. To
        avoid this behaviour, call `traverse()` separately with each input node.

        Note that traversing from nodes which are already at or greater than `settings.max_depth`
        will not do anything. `settings.max_depth` is a global maximum depth regardless of the value
        pass as `depth`.

        `depth` is *relative* to the depth of the given `nodes` - i.e. if the first node is at depth
        7, and `depth` is 3, then *for that node*, we traverse up to depth 10. Relative depth is
        calculated separately for each input node.

        You may already have some results stored in `self.nodes`, `self.edges`, etc. Use
        `reset_results` to purge this cache if you want to only see the results of this traversal.

        The calculation count is reset each time `traverse()` is run.

        Parameters
        ----------
        nodes : List[Node]
            List of nodes to traverse. Uses the functional unit (`self._root_node`) as the default
        depth : int
            Relative depth to traverse for each node provided up to `settings.max_depth`
        reset_results : bool
            Reset `self.nodes`, `self.edges`, and `self.flows`.

        Returns
        -------
        `None`
            Modifies the class object's state in-place

        """
        if reset_results:
            self._nodes: Dict[int, Node] = {}
            self._edges: List[Edge] = []
            self._flows: List[Flow] = []
        if self.calculation_count > 0:
            # Have already done traversal; need to bump maximum number of maximum calculations
            self._max_calc += self.settings.max_calc

        if nodes is None:
            self._nodes[self._functional_unit_unique_id] = self._root_node
            self._traverse([(0, self._root_node)], self._max_depth_for_node(self._root_node, depth))
        else:
            heap = []
            for node in nodes:
                node.max_depth = self._max_depth_for_node(node, depth)
                node.depth = 0
                self._nodes[node.unique_id] = node
                if self.settings.separate_biosphere_flows:
                    self.add_biosphere_flows(
                        flows=self._flows,
                        matrix=(
                            node.supply_amount
                            * self.characterized_biosphere[:, node.activity_index]
                        ).tocoo(),
                        lca=self.lca,
                        node=node,
                        biosphere_cutoff_score=self.biosphere_cutoff_score,
                    )

                heappush(heap, (abs(1 / node.cumulative_score), node))
            self._traverse(heap, max_depth=self.settings.max_depth)

        self._flows.sort(reverse=True)

        non_terminal_nodes = {edge.consumer_unique_id for edge in self._edges}
        for key, obj in self._nodes.items():
            obj.terminal = key not in non_terminal_nodes

    @property
    def exceeded_calculation_count(self):
        return self.calculation_count > self._max_calc

    def _traverse(self, heap: list, max_depth: Optional[int] = None):
        """
        Traverse the graph.

        Parameters
        ----------
        heap:
            nodes to traverse
        max_depth:
            global maximum depth to traverse
        """
        while heap:
            if self.exceeded_calculation_count:
                warnings.warn("Stopping traversal due to calculation count.")
                break
            _, node = heappop(heap)

            product_indices, product_amounts = self.get_demand_vector_for_activity(
                node=node,
                skip_coproducts=self.settings.skip_coproducts,
                matrix=self.lca.technosphere_matrix,
            )

            self.traverse_edges(
                consumer_index=node.activity_index,
                consumer_unique_id=node.unique_id,
                consumer_max_depth=node.max_depth,
                product_indices=product_indices,
                product_amounts=product_amounts,
                lca=self.lca,
                current_depth=node.depth,
                max_depth=max_depth or self.settings.max_depth,
                calculation_count=self._calculation_count,
                characterized_biosphere=self.characterized_biosphere,
                matrix=self.lca.technosphere_matrix,
                edges=self._edges,
                flows=self._flows,
                nodes=self._nodes,
                heap=heap,
                caching_solver=self._caching_solver,
                static_activity_indices=self.static_activity_indices,
                production_exchange_mapping=self.production_exchange_mapping,
                separate_biosphere_flows=self.settings.separate_biosphere_flows,
                cutoff_score=self.cutoff_score,
                biosphere_cutoff_score=self.biosphere_cutoff_score,
            )

    def traverse_edges(
        self,
        *,
        consumer_index: int,
        consumer_unique_id: int,
        consumer_max_depth: Optional[int],
        product_indices: list[int],
        product_amounts: list[float],
        lca: LCA,
        current_depth: int,
        calculation_count: Counter,
        characterized_biosphere: spmatrix,
        matrix: spmatrix,
        edges: list[Edge],
        flows: list[Flow],
        nodes: Dict[int, Node],
        heap: list,
        production_exchange_mapping: dict[int, int],
        static_activity_indices: set[int],
        separate_biosphere_flows: bool,
        caching_solver: CachingSolver,
        biosphere_cutoff_score: float,
        cutoff_score: float,
        max_depth: Optional[int] = None,
    ) -> None:
        for product_index, product_amount in zip(product_indices, product_amounts):
            producer_index = production_exchange_mapping[product_index]

            if producer_index in static_activity_indices:
                continue

            supply = caching_solver(product_index, product_amount)
            cumulative_score = float((characterized_biosphere * supply).sum())
            reference_product_net_production_amount = matrix[product_index, producer_index]
            scale = product_amount / reference_product_net_production_amount

            if abs(cumulative_score) < cutoff_score:
                continue

            producing_node = Node(
                unique_id=next(calculation_count),
                activity_datapackage_id=lca.dicts.activity.reversed[producer_index],
                activity_index=producer_index,
                reference_product_datapackage_id=lca.dicts.product.reversed[product_index],
                reference_product_index=product_index,
                reference_product_production_amount=reference_product_net_production_amount,
                supply_amount=scale,
                depth=current_depth + 1,
                max_depth=consumer_max_depth,
                cumulative_score=cumulative_score,
                direct_emissions_score=(scale * characterized_biosphere[:, producer_index]).sum(),
            )
            edges.append(
                Edge(
                    consumer_index=consumer_index,
                    consumer_unique_id=consumer_unique_id,
                    producer_index=producer_index,
                    producer_unique_id=producing_node.unique_id,
                    product_index=product_index,
                    amount=product_amount,
                )
            )

            if separate_biosphere_flows:
                flow_score = self.add_biosphere_flows(
                    flows=flows,
                    matrix=(scale * characterized_biosphere[:, producer_index]).tocoo(),
                    lca=lca,
                    node=producing_node,
                    biosphere_cutoff_score=biosphere_cutoff_score,
                )
            else:
                flow_score = 0

            producing_node.direct_emissions_score_outside_specific_flows = (
                producing_node.direct_emissions_score - flow_score
            )
            producing_node.remaining_cumulative_score_outside_specific_flows = (
                producing_node.cumulative_score - flow_score
            )

            nodes[producing_node.unique_id] = producing_node

            if producing_node.max_depth is not None:
                # Local max depth overrides everything, and already include global max depth
                satisfies_depth_constraint = producing_node.max_depth > producing_node.depth
            else:
                satisfies_depth_constraint = (max_depth is None) or (
                    producing_node.depth < max_depth
                )

            if satisfies_depth_constraint:
                heappush(heap, (abs(1 / cumulative_score), producing_node))

    @classmethod
    def get_characterized_biosphere(cls, lca: LCA) -> spmatrix:
        """
        Pre-calculate the characterized biosphere matrix.

        Broken out as a separate method because subclasses like regionalized
        LCA could have more complicated characterization.

        Parameters
        ----------
        lca : bw2calc.LCA
            LCA class instance

        Returns
        -------
        scipy.sparse.spmatrix
            Unmapped matrix of biosphere flows by activities.

        """
        return lca.characterization_matrix * lca.biosphere_matrix

    @classmethod
    def get_production_exchanges(cls, mapped_matrix: mu.MappedMatrix) -> (np.array, np.array):
        """
        Get matrix row and column indices of productions exchanges by trying a
        series of heuristics. See documentation for
        ``guess_production_exchanges``.

        Broken out as a separate method because subclasses could change this logic.

        Parameters
        ----------
        mapped_matrix : matrix_utils.MappedMatrix
            A matrix and mapping data (from database ids to matrix indices)
            from the ``matrix_utils`` library. Normally built automatically by
            an ``LCA`` class. Should be the ``technosphere_matrix`` or
            equivalent.

        Returns
        -------
        (numpy.array, numpy.array)
            The matrix row and column indices of the production exchanges.

        """
        return guess_production_exchanges(mapped_matrix)

    @classmethod
    def add_biosphere_flows(
        cls,
        flows: list[Flow],
        matrix: spmatrix,
        lca: LCA,
        node: Node,
        biosphere_cutoff_score: float,
    ) -> float:
        """
        Add individual biosphere flows as `Flow` instances to `flow` if their score is above
        `biosphere_cutoff_score`.

        Parameters
        ----------
        flows : list
            List of existing `Flow` instances
        matrix : scipy.sparse.spmatrix
            Pre-calculated characterization times biosphere matrix
        lca : bw2calc.LCA
            LCA class instance
        node : `Node`
            Node whose direct biosphere flows we are examining
        biosphere_cutoff_score : float
            Score below which individual characterized biosphere flows are ignored

        Returns
        -------
        The total LCIA score broken out to separate `Flow` instances

        """
        added_score = 0.0
        for index, score in zip(matrix.row, matrix.data):
            if abs(score) > biosphere_cutoff_score:
                added_score += score
                flows.append(
                    Flow(
                        flow_datapackage_id=lca.dicts.biosphere.reversed[index],
                        flow_index=index,
                        activity_unique_id=node.unique_id,
                        activity_id=node.activity_datapackage_id,
                        activity_index=node.activity_index,
                        amount=(
                            lca.biosphere_matrix[index, node.activity_index] * node.supply_amount
                        ),
                        score=score,
                    )
                )
        return added_score

    def get_demand_vector_for_activity(
        self,
        node: Node,
        skip_coproducts: bool,
        matrix: spmatrix,
    ) -> (list[int], list[float]):
        if node is self._root_node:
            product_indices = [self.lca.dicts.product[key] for key in self.lca.demand]
            product_amounts = self.lca.demand.values()
            return product_indices, product_amounts

        return get_demand_vector_for_activity(
            node=node, skip_coproducts=skip_coproducts, matrix=matrix
        )
