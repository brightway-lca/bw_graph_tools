import warnings
from dataclasses import dataclass
from functools import lru_cache
from heapq import heappop, heappush

from bw2calc import LCA
from scipy.sparse import spmatrix
import matrix_utils as mu
import numpy as np

try:
    from bw2data import databases
except ImportError:
    databases = {}


from .matrix_tools import guess_production_exchanges


class CachingSolver:
    """Class which caches expensive linear algebra solution vectors."""

    def __init__(self, lca: LCA):
        self.lca = lca

    @lru_cache(maxsize=8096)
    def calculate(self, index: int) -> np.ndarray:
        """Compute cumulative LCA score for one unit of a given activity"""
        self.lca.demand_array[:] = 0
        self.lca.demand_array[index] = 1
        return self.lca.solve_linear_system()

    def __call__(self, index: int, amount: float) -> np.ndarray:
        return self.calculate(index) * amount


class Counter:
    """Custom counter to have easy access to current value"""

    def __init__(self):
        self.value = -1

    def __next__(self):
        self.value += 1
        return self.value

    def __gt__(self, other):
        return self.value > other


@dataclass
class Node:
    """
    A visited activity in a supply chain graph. Although our graph is cyclic, we treat each activity as a separate node every time we visit it.

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
    supply_amount : float
        The amount of the *activity* (not reference product!) needed to supply the demand from the requesting supply chain edge.
    cumulative_score : float
        Total LCIA score attributed to `supply_amount` of this activity. Includes direct emissions unless explicitly removed.
    direct_emissions_score : float
        Total LCIA score attributed only to the direct characterized biosphere flows of `supply_amount` of this activity.

    """

    unique_id: int
    activity_datapackage_id: int
    activity_index: int
    reference_product_datapackage_id: int
    reference_product_index: int
    reference_product_production_amount: float
    supply_amount: float
    cumulative_score: float
    direct_emissions_score: float

    def __lt__(self, other):
        # Needed for sorting
        return self.cumulative_score < other.cumulative_score


@dataclass
class Edge:
    """
    An edge between two *activities*. The `amount` is the amount of the product demanded by the `consumer`.

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
        The amount of the product demanded by the consumer. Not scaled to producer production amount.
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


class NewNodeEachVisitGraphTraversal:
    """
    Traverse a supply chain, following paths of greatest impact.

    This implementation uses a queue of datasets to assess. As the supply chain is traversed, activities are added to a list sorted by LCA score. Each activity in the sorted list is assessed, and added to the supply chain graph, as long as its impact is above a certain threshold, and the maximum number of calculations has not been exceeded.

    Because the next dataset assessed is chosen by its impact, not its position in the graph, this is neither a breadth-first nor a depth-first search, but rather "importance-first".

    This class is written in a functional style, and the class serves mainly to collect methods which belong together. There are only `classmethods` and no state is stored on the class itself.

    Should be used by calling the ``calculate`` method. All other functions should be considered an internal API.

    .. warning:: Graph traversal with multioutput processes only works when other inputs are substituted (see `Multioutput processes in LCA <http://chris.mutel.org/multioutput.html>`__ for a description of multiputput process math in LCA).

    """

    @classmethod
    def calculate(
        cls,
        lca_object: LCA,
        cutoff: float | None = 5e-3,
        biosphere_cutoff: float | None = 1e-4,
        max_calc: int | None = 1e5,
        skip_coproducts: bool | None = False,
        separate_biosphere_flows: bool | None = True,
        static_activity_indices: set[int] | None = set(),
        functional_unit_unique_id: int | None = -1,
    ) -> dict:
        """
        Priority-first traversal (i.e. follow the past of highest score) of the supply chain graph. This class unrolls
        the graph, i.e. every time it arrives at a given activity, it treats
        it as a separate node in the graph.

        In contrast with previous graph traversal implementations, we do not assume reference production exchanges are on the diagonal. It should also correctly handle the following:

        * Functional unit has more than one link to a given product
        * Non-unitary reference production amounts
        * Negative reference production amounts
        * Co-production edge traversal, if desired. Requires co-products to be substituted (can be implicit substitution).

        You must provide an `lca_object` which is already instantiated, and for which you have already done LCI and LCIA calculations. The `lca_object` does not have to be an instance of `bw2calc.LCA`, but it needs to support the following methods and attributes:

        * `technosphere_matrix`
        * `technosphere_mm`
        * `solve_linear_system()`
        * `demand`
        * `demand_array`

        You can subclass `NewNodeEachVisitGraphTraversal` and redefine `get_characterized_biosphere` if your LCA class does not have a traditional `characterization_matrix` and `biosphere_matrix`.

        The return object is a dictionary with four values. The `nodes` is a dictionary of visited **activities**; the keys in this dictionary are unique increasing integer ids (not related to any other ids or indices), and values are instances of the `Node` dataclass. Each `Node` has a `unique_id`, as every time we arrive at an activity (even if we have seen it before via another branch of the supply chain), we create a new `Node` object with a unique id. See the `Node` documentation for its other attributes.

        edges

        flows

        Finally, `calculation_count` gives the total number of inventory calculations performed.

        Without further manipulation, the results will have double counting if you add all scores together. Specifically, each `Node` has both a `cumulative_score` and a `direct_emissions_score`; the direct emissions are counted in both scores. Use XXX to subtract `direct_emissions_score` from `cumulative_score`. Moreover, the `direct_emissions_score` includes all characterized flows, but important flows can also be listed separately as `Flow` objects. Use XXX to subtract specific `Flows` from the `direct_emissions_score`.

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
        skip_coproducts : bool
            Don't traverse co-production edges, i.e. production edges other
            than the reference product
        separate_biosphere_flows : bool
            Add separate `Flow` nodes for important individual biosphere
            emissions
        static_activity_indices : set
            A set of activity matrix indices which we don't want the graph to
            traverse
        functional_unit_unique_id : int
            An integer id we can use for the functional unit virtual activity.
            Shouldn't overlap any other activity ids. Don't change unless you r
            eally know what you are doing.

        Returns
        -------
        dict
            Dictionary with keys `nodes`, `edges`, `flows`, `calculation_counter`

        """
        total_score = lca_object.score
        if total_score == 0:
            raise ValueError("Zero total LCA score makes traversal impossible")

        cutoff_score = abs(total_score * cutoff)
        biosphere_cutoff_score = abs(total_score * biosphere_cutoff)
        technosphere_matrix = lca_object.technosphere_matrix
        production_exchange_mapping = {
            x: y
            for x, y in zip(*cls.get_production_exchanges(lca_object.technosphere_mm))
        }
        heap, edges, flows = [], [], []
        calculation_count = Counter()
        characterized_biosphere = cls.get_characterized_biosphere(lca_object)
        caching_solver = CachingSolver(lca_object)

        nodes = {
            functional_unit_unique_id: Node(
                unique_id=functional_unit_unique_id,
                activity_datapackage_id=functional_unit_unique_id,
                activity_index=functional_unit_unique_id,
                reference_product_datapackage_id=functional_unit_unique_id,
                reference_product_index=functional_unit_unique_id,
                reference_product_production_amount=1.0,
                supply_amount=1.0,
                cumulative_score=lca_object.score,
                direct_emissions_score=0.0,
            )
        }

        cls.traverse_edges(
            consumer_index=functional_unit_unique_id,
            consumer_unique_id=functional_unit_unique_id,
            product_indices=[
                lca_object.dicts.product[key] for key in lca_object.demand
            ],
            product_amounts=lca_object.demand.values(),
            lca=lca_object,
            calculation_count=calculation_count,
            characterized_biosphere=characterized_biosphere,
            matrix=technosphere_matrix,
            edges=edges,
            flows=flows,
            nodes=nodes,
            heap=heap,
            caching_solver=caching_solver,
            production_exchange_mapping=production_exchange_mapping,
            separate_biosphere_flows=separate_biosphere_flows,
            cutoff_score=cutoff_score,
            static_activity_indices=static_activity_indices,
            biosphere_cutoff_score=biosphere_cutoff_score,
        )

        cls.traverse(
            heap=heap,
            nodes=nodes,
            edges=edges,
            flows=flows,
            max_calc=max_calc,
            cutoff_score=cutoff_score,
            characterized_biosphere=characterized_biosphere,
            calculation_count=calculation_count,
            static_activity_indices=static_activity_indices,
            caching_solver=caching_solver,
            production_exchange_mapping=production_exchange_mapping,
            technosphere_matrix=technosphere_matrix,
            lca=lca_object,
            skip_coproducts=skip_coproducts,
            separate_biosphere_flows=separate_biosphere_flows,
            biosphere_cutoff_score=biosphere_cutoff_score,
        )

        flows.sort(reverse=True)

        return {
            "nodes": nodes,
            "edges": edges,
            "flows": flows,
            "calculation_count": calculation_count.value,
        }

    @classmethod
    def traverse(
        cls,
        heap: list,
        nodes: dict[Node],
        edges: list[Edge],
        flows: list[Flow],
        max_calc: int,
        cutoff_score: float,
        characterized_biosphere: spmatrix,
        calculation_count: Counter,
        static_activity_indices: set,
        production_exchange_mapping: dict[int, int],
        technosphere_matrix: spmatrix,
        lca: LCA,
        caching_solver: CachingSolver,
        skip_coproducts: bool,
        separate_biosphere_flows: bool,
        biosphere_cutoff_score: float,
    ) -> None:
        """
        Perform the graph traversal from the initial functional unit edges.

        Parameters
        ----------
        heap : list
            The `heapq` list of nodes to traverse
        nodes : dict
            Dictionary of already visited `Nodes`
        edges : list
            List of visited `Edges`
        flows : list
            List of significant seen `Flows`
        max_calc : int
            Maximum number of inventory calculations to perform
        cutoff_score : float
            Score below which graph edges are ignored. We always consider the absolute value of edges scores.
        characterized_biosphere : spmatrix
            The pre-calculated characterization time biosphere matrix
        calculation_count : `Counter`
            Counter object tracking number of lci calculations
        static_activity_indices : set
            A set of activity matrix indices which we don't want the graph to
            traverse
        production_exchange_mapping : dict
            Mapping of product matrix row indices to the activity matrix column indices for which they are reference products
        technosphere_matrix : scipy.sparse.spmatrix
            LCA technosphere matrix
        lca : bw2calc.LCA
            Already instantiated `LCA` object with inventory and impact
            assessment calculated.
        caching_solver : `CachingSolver`
            Solver which caches solutions to linear algebra problems
        skip_coproducts : bool
            Don't traverse co-production edges, i.e. production edges other
            than the reference product
        separate_biosphere_flows : bool
            Add separate `Flow` nodes for important individual biosphere
            emissions
        biosphere_cutoff_score : float
            Score below which individual biosphere flows are not added to `flows`

        Returns
        -------
        `None`
            Modifies `heap`, `nodes`, `edges`, and `flows` in-place

        """
        while heap:
            if calculation_count > max_calc:
                warnings.warn("Stopping traversal due to calculation count.")
                break
            _, node = heappop(heap)

            product_indices, product_amounts = cls.get_demand_vector_for_activity(
                node=node,
                skip_coproducts=skip_coproducts,
                matrix=technosphere_matrix,
            )

            cls.traverse_edges(
                consumer_index=node.activity_index,
                consumer_unique_id=node.unique_id,
                product_indices=product_indices,
                product_amounts=product_amounts,
                lca=lca,
                calculation_count=calculation_count,
                characterized_biosphere=characterized_biosphere,
                matrix=technosphere_matrix,
                edges=edges,
                flows=flows,
                nodes=nodes,
                heap=heap,
                caching_solver=caching_solver,
                static_activity_indices=static_activity_indices,
                production_exchange_mapping=production_exchange_mapping,
                separate_biosphere_flows=separate_biosphere_flows,
                cutoff_score=cutoff_score,
                biosphere_cutoff_score=biosphere_cutoff_score,
            )

    @classmethod
    def traverse_edges(
        cls,
        consumer_index: int,
        consumer_unique_id: int,
        product_indices: list[int],
        product_amounts: list[float],
        lca: LCA,
        calculation_count: Counter,
        characterized_biosphere: spmatrix,
        matrix: spmatrix,
        edges: list[Edge],
        flows: list[Flow],
        nodes: list[Node],
        heap: list,
        production_exchange_mapping: dict[int, int],
        static_activity_indices: set[int],
        separate_biosphere_flows: bool,
        caching_solver: CachingSolver,
        biosphere_cutoff_score: float,
        cutoff_score: float,
    ) -> None:
        for product_index, product_amount in zip(product_indices, product_amounts):
            producer_index = production_exchange_mapping[product_index]

            if producer_index in static_activity_indices:
                return

            supply = caching_solver(product_index, product_amount)
            cumulative_score = float((characterized_biosphere * supply).sum())
            reference_product_net_production_amount = matrix[
                product_index, producer_index
            ]
            scale = product_amount / reference_product_net_production_amount

            if abs(cumulative_score) < cutoff_score:
                return

            producing_node = Node(
                unique_id=next(calculation_count),
                activity_datapackage_id=lca.dicts.activity.reversed[producer_index],
                activity_index=producer_index,
                reference_product_datapackage_id=lca.dicts.product.reversed[
                    product_index
                ],
                reference_product_index=product_index,
                reference_product_production_amount=reference_product_net_production_amount,
                supply_amount=scale,
                cumulative_score=cumulative_score,
                direct_emissions_score=(
                    scale * characterized_biosphere[:, producer_index]
                ).sum(),
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
                cls.add_biosphere_flows(
                    flows=flows,
                    matrix=(scale * characterized_biosphere[:, producer_index]).tocoo(),
                    lca=lca,
                    node=producing_node,
                    biosphere_cutoff_score=biosphere_cutoff_score,
                )

            heappush(heap, (abs(1 / cumulative_score), producing_node))
            nodes[producing_node.unique_id] = producing_node

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
    def get_production_exchanges(
        cls, mapped_matrix: mu.MappedMatrix
    ) -> (np.array, np.array):
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
    ) -> None:
        """
        Add individual biosphere flows as `Flow` instances to `flow` if their score is above `biosphere_cutoff_score`.

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
        `None`
            Modifies `flows` by adding new `Flow` instances

        """
        for index, score in zip(matrix.row, matrix.data):
            if abs(score) > biosphere_cutoff_score:
                flows.append(
                    Flow(
                        flow_datapackage_id=lca.dicts.biosphere.reversed[index],
                        flow_index=index,
                        activity_unique_id=node.unique_id,
                        activity_id=node.activity_datapackage_id,
                        activity_index=node.activity_index,
                        amount=(
                            lca.biosphere_matrix[index, node.activity_index]
                            * node.supply_amount
                        ),
                        score=score,
                    )
                )

    @classmethod
    def get_demand_vector_for_activity(
        cls,
        node: Node,
        skip_coproducts: bool,
        matrix: spmatrix,
    ) -> (list[int], list[float]):
        """
        Get input matrix indices and amounts for a given activity. Ignores the reference production exchanges and optionally other co-production exchanges.

        Parameters
        ----------
        node : `Node`
            Activity whose inputs we are iterating over
        skip_coproducts : bool
            Whether or not to ignore positive production exchanges other than the reference product, which is always ignored
        matrix : scipy.sparse.spmatrix
            Technosphere matrix

        Returns
        -------

        row indices : list
            Integer row indices for products consumed by `Node`
        amounts : list
            The amount of each product consumed, scaled to `Node.supply_amount`. Same order as row indices.

        """
        matrix = (-1 * node.supply_amount * matrix[:, node.activity_index]).tocoo()

        rows, vals = [], []
        for x, y in zip(matrix.row, matrix.data):
            if x == node.reference_product_index:
                continue
            elif y == 0:
                continue
            elif y < 0 and skip_coproducts:
                continue
            rows.append(x)
            vals.append(y)
        return rows, vals


class AssumedDiagonalGraphTraversal(NewNodeEachVisitGraphTraversal):
    @classmethod
    def get_production_exchanges(
        cls, mapped_matrix: mu.MappedMatrix
    ) -> (np.ndarray, np.ndarray):
        """
        Assume production exchanges are always on the diagonal instead of
        examining matrix structure and input data.

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
        length = mapped_matrix.matrix.shape[0]
        return np.arange(length), np.arange(length)
