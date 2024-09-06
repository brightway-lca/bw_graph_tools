import typing
from typing import TypeVar, Generic, Dict, List

from .graph_objects import Node, Edge, Flow
from .utils import CachingSolver

if typing.TYPE_CHECKING:
    import bw2calc

Settings = TypeVar("Settings")


class GraphTraversalException(Exception):
    ...


class BaseGraphTraversal(Generic[Settings]):

    def __init__(
            self,
            lca: "bw2calc.LCA",
            settings: Settings,
            functional_unit_unique_id: int = -1,
            static_activity_indices=None,
    ):
        """
        Parameters
        ----------
        lca : bw2calc.LCA
            Already instantiated `LCA` object with inventory and impact
            assessment calculated.
        settings: object
            Settings for the graph traversal
        functional_unit_unique_id : int
            An integer id we can use for the functional unit virtual activity.
            Shouldn't overlap any other activity ids. Don't change unless you
            really know what you are doing.
        static_activity_indices : set
            A set of activity matrix indices which we don't want the graph to
            traverse - i.e. we stop traversal when we hit these nodes, but
            still add them to the returned `nodes` dictionary, and calculate
            their direct and cumulative scores.
        """
        if static_activity_indices is None:
            static_activity_indices = set()
        self.lca = lca
        self.settings = settings
        self.static_activity_indices = static_activity_indices
        # allows the user to store metadata from the traversal
        self.metadata = dict()

        self._nodes: Dict[int, Node] = {
            functional_unit_unique_id: Node(
                unique_id=functional_unit_unique_id,
                activity_datapackage_id=functional_unit_unique_id,
                activity_index=functional_unit_unique_id,
                reference_product_datapackage_id=functional_unit_unique_id,
                reference_product_index=functional_unit_unique_id,
                reference_product_production_amount=1.0,
                depth=0,
                supply_amount=1.0,
                cumulative_score=self.lca.score,
                direct_emissions_score=0.0,
            )
        }
        self._root_node = self._nodes[functional_unit_unique_id]
        self._edges: List[Edge] = []
        self._flows: List[Flow] = []
        self._heap: List[Node] = []

        # internal properties
        self._caching_solver = CachingSolver(lca)

    @property
    def nodes(self):
        """
        instances of the `Node` dataclass. Each `Node` has a `unique_id`, as every time we
        arrive at an activity (even if we have seen it before via another branch of the supply
        chain), we create a new `Node` object with a unique id. See the `Node` documentation
        for its other attributes.
        """
        return self._nodes

    @property
    def edges(self):
        """
        is a list of `Edge` instances. Edges link two `Node` instances (but not `Flow`
        instances, that is handled separately). The `Edge` amount is the amount demanded of
        the producer at that point in the supply chain, scaled to the amount of the producer
        requested.
        """
        return self._edges

    @property
    def flows(self):
        """
        is a list of `Flow` instances; biosphere flows are linked to a particular `Node`.
        """
        return self._flows
