import typing
from typing import Dict, Generic, List, TypeVar

from bw_graph_tools.graph_traversal.graph_objects import Edge, Flow, Node
from bw_graph_tools.graph_traversal.utils import CachingSolver

if typing.TYPE_CHECKING:
    import bw2calc

Settings = TypeVar("Settings")


class GraphTraversalException(Exception): ...


class BaseGraphTraversal(Generic[Settings]):
    def __init__(
        self,
        lca: "bw2calc.LCA",
        settings: Settings,
        functional_unit_unique_id: int = -1,
        static_activity_indices=None,
    ):
        """
        Base class for common graph traversal methods. Should be inherited from, not used directly.

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

        # internal properties
        self._functional_unit_unique_id = functional_unit_unique_id
        self._max_calc = self.settings.max_calc
        self._root_node = Node(
            unique_id=functional_unit_unique_id,
            activity_datapackage_id=functional_unit_unique_id,
            activity_index=functional_unit_unique_id,
            reference_product_datapackage_id=functional_unit_unique_id,
            reference_product_index=functional_unit_unique_id,
            reference_product_production_amount=1.0,
            depth=0,
            # Not one of any particular product in the functional unit, but one functional
            # unit itself.
            supply_amount=1.0,
            cumulative_score=self.lca.score,
            direct_emissions_score=0.0,
        )
        self._nodes: Dict[int, Node] = {self._functional_unit_unique_id: self._root_node}
        self._edges: List[Edge] = []
        self._flows: List[Flow] = []
        self._caching_solver = CachingSolver(lca)

    @property
    def nodes(self):
        """
        List of `Node` dataclass instances.

        Each `Node` instance has a `unique_id`, regardless of graph traversal class. In some
        classes, each node in the database will only appear once in this list of graph traversal
        node instances, but in `NewNodeEachVisitGraphTraversal`, we create a new `Node` every time
        we reach a database node, even if we have seen it before.

        See the `Node` documentation for its other attributes.
        """
        return self._nodes

    @property
    def edges(self):
        """
        List of `Edge` instances. Edges link two `Node` instances.

        Note that there are no `Edge` instances which link `Flow` instances - these are handled
        separately.

        See the `Edge` documentation for its other attributes.
        """
        return self._edges

    @property
    def flows(self):
        """
        List of `Flow` instances.

        A `Flow` instance is a *characterized biosphere flow* associated with a specific `Node`
        instance.

        See the `Flow` documentation for its other attributes.
        """
        return self._flows
