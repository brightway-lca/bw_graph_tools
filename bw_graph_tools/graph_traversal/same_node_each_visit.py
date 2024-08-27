from .new_node_each_visit import NewNodeEachVisitGraphTraversal
from bw2calc import LCA
from typing import Optional, Dict, List
from .utils import Counter, CachingSolver
from .graph_objects import Node, Edge


class SameNodeEachVisitGraphTraversal(NewNodeEachVisitGraphTraversal):
    """
    A stateful graph traversal that keeps track of which nodes have been
    visited already, allowing for a partial and dynamic traversal of the graph.
    """

    def __init__(
        self,
        lca_object: LCA,
        cutoff: Optional[float] = 5e-3,
        biosphere_cutoff: Optional[float] = 1e-4,
        max_calc: Optional[int] = 10000,
        max_depth: Optional[int] = None,
        skip_coproducts: Optional[bool] = False,
        separate_biosphere_flows: Optional[bool] = True,
        static_activity_indices: Optional[set[int]] = set(),
        functional_unit_unique_id: Optional[int] = -1,
    ):
        """
        See `NewNodeEachVisitGraphTraversal.calculate` for more information

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
            Maximum depth in the supply chain for the initial traversal. Default is no maximum.
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
            Shouldn't overlap any other activity ids. Don't change unless you
            really know what you are doing.

        """
        super().__init__()
        self.lca_object = lca_object
        self.cutoff = cutoff
        self.max_calc = max_calc
        self.skip_coproducts = skip_coproducts
        self.separate_biosphere_flows = separate_biosphere_flows
        self.static_activity_indices = static_activity_indices
        total_score = lca_object.score
        if total_score == 0:
            raise ValueError("Zero total LCA score makes traversal impossible")

        self.cutoff_score = abs(total_score * cutoff)
        self.biosphere_cutoff_score = abs(total_score * biosphere_cutoff)
        self.technosphere_matrix = lca_object.technosphere_matrix
        self.production_exchange_mapping = {
            x: y for x, y in zip(*self.get_production_exchanges(lca_object.technosphere_mm))
        }
        self.heap, self.edges, self.flows = [], [], []
        self.calculation_count = Counter()
        self.characterized_biosphere = self.get_characterized_biosphere(lca_object)
        self.caching_solver = CachingSolver(lca_object)

        self.nodes: Dict[int, Node] = {
            functional_unit_unique_id: Node(
                unique_id=functional_unit_unique_id,
                activity_datapackage_id=functional_unit_unique_id,
                activity_index=functional_unit_unique_id,
                reference_product_datapackage_id=functional_unit_unique_id,
                reference_product_index=functional_unit_unique_id,
                reference_product_production_amount=1.0,
                depth=0,
                supply_amount=1.0,
                cumulative_score=lca_object.score,
                direct_emissions_score=0.0,
            )
        }
        self.edges: List[Edge] = []
        self.flows = []
        self.calculation_count = Counter()
        self.visited_nodes = set()
        self.metadata = dict()

        self.traverse_edges(
            consumer_index=functional_unit_unique_id,
            consumer_unique_id=functional_unit_unique_id,
            product_indices=[lca_object.dicts.product[key] for key in lca_object.demand],
            product_amounts=lca_object.demand.values(),
            lca=lca_object,
            current_depth=0,
            max_depth=max_depth,
            calculation_count=self.calculation_count,
            characterized_biosphere=self.characterized_biosphere,
            matrix=self.technosphere_matrix,
            edges=self.edges,
            flows=self.flows,
            nodes=self.nodes,
            heap=self.heap,
            caching_solver=self.caching_solver,
            production_exchange_mapping=self.production_exchange_mapping,
            separate_biosphere_flows=separate_biosphere_flows,
            cutoff_score=self.cutoff_score,
            static_activity_indices=self.static_activity_indices,
            biosphere_cutoff_score=self.biosphere_cutoff_score,
        )

        self.traverse_from_node(functional_unit_unique_id, max_depth=max_depth)

    def traverse_from_node(self, node_id: int, max_depth: Optional[int] = None) -> bool:
        """
        Traverse the graph starting from the specified node and exp
        returning a boolean indicating if the node traversed already

        Parameters
        ----------
        node_id
            node's unique id
        max_depth
            max depth to traverse from this node, otherwise will default to `node.depth + 1`

        Returns
        -------
        bool
            indicates if the node was traversed
        """
        node = self.nodes[node_id]
        if node.unique_id in self.visited_nodes:
            return False

        self.visited_nodes.add(node.unique_id)
        self.traverse(
            heap=[(0, node)],
            nodes=self.nodes,
            edges=self.edges,
            flows=self.flows,
            max_depth=node.depth + 1 if max_depth is None else max_depth,
            max_calc=self.max_calc,
            cutoff_score=self.cutoff_score,
            characterized_biosphere=self.characterized_biosphere,
            calculation_count=self.calculation_count,
            static_activity_indices=self.static_activity_indices,
            caching_solver=self.caching_solver,
            production_exchange_mapping=self.production_exchange_mapping,
            technosphere_matrix=self.technosphere_matrix,
            lca=self.lca_object,
            skip_coproducts=self.skip_coproducts,
            separate_biosphere_flows=self.separate_biosphere_flows,
            biosphere_cutoff_score=self.biosphere_cutoff_score,
        )

        self.flows.sort(reverse=True)

        non_terminal_nodes = {edge.consumer_unique_id for edge in self.edges}
        for node_id_key in self.nodes:
            if node_id_key not in non_terminal_nodes:
                terminal = True
            else:
                terminal = False
            self.nodes[node_id_key].terminal = terminal

        return True
