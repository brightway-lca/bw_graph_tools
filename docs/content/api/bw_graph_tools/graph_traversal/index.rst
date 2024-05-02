:py:mod:`bw_graph_tools.graph_traversal`
========================================

.. py:module:: bw_graph_tools.graph_traversal


Module Contents
---------------

Classes
~~~~~~~

.. autoapisummary::

   bw_graph_tools.graph_traversal.AssumedDiagonalGraphTraversal
   bw_graph_tools.graph_traversal.CachingSolver
   bw_graph_tools.graph_traversal.Counter
   bw_graph_tools.graph_traversal.Edge
   bw_graph_tools.graph_traversal.Flow
   bw_graph_tools.graph_traversal.NewNodeEachVisitGraphTraversal
   bw_graph_tools.graph_traversal.Node




Attributes
~~~~~~~~~~

.. autoapisummary::

   bw_graph_tools.graph_traversal.databases


.. py:class:: AssumedDiagonalGraphTraversal


   Bases: :py:obj:`NewNodeEachVisitGraphTraversal`

   Traverse a supply chain, following paths of greatest impact.

   This implementation uses a queue of datasets to assess. As the supply chain is traversed, activities are added to a list sorted by LCA score. Each activity in the sorted list is assessed, and added to the supply chain graph, as long as its impact is above a certain threshold, and the maximum number of calculations has not been exceeded.

   Because the next dataset assessed is chosen by its impact, not its position in the graph, this is neither a breadth-first nor a depth-first search, but rather "importance-first".

   This class is written in a functional style, and the class serves mainly to collect methods which belong together. There are only `classmethods` and no state is stored on the class itself.

   Should be used by calling the ``calculate`` method. All other functions should be considered an internal API.

   .. warning:: Graph traversal with multioutput processes only works when other inputs are substituted (see `Multioutput processes in LCA <http://chris.mutel.org/multioutput.html>`__ for a description of multiputput process math in LCA).


   .. py:method:: get_production_exchanges(mapped_matrix: matrix_utils.MappedMatrix) -> (numpy.ndarray, numpy.ndarray)
      :classmethod:

      Assume production exchanges are always on the diagonal instead of
      examining matrix structure and input data.

      :param mapped_matrix: A matrix and mapping data (from database ids to matrix indices)
                            from the ``matrix_utils`` library. Normally built automatically by
                            an ``LCA`` class. Should be the ``technosphere_matrix`` or
                            equivalent.
      :type mapped_matrix: matrix_utils.MappedMatrix

      :returns: The matrix row and column indices of the production exchanges.
      :rtype: (numpy.array, numpy.array)



.. py:class:: CachingSolver(lca: bw2calc.LCA)


   Class which caches expensive linear algebra solution vectors.

   .. py:method:: calculate(index: int) -> numpy.ndarray

      Compute cumulative LCA score for one unit of a given activity



.. py:class:: Counter


   Custom counter to have easy access to current value


.. py:class:: Edge


   An edge between two *activities*. The `amount` is the amount of the product demanded by the `consumer`.

   :param consumer_index: The matrix column index of the consuming activity
   :type consumer_index: int
   :param consumer_unique_id: The traversal-specific unique id of the consuming activity
   :type consumer_unique_id: int
   :param producer_index: The matrix column index of the producing activity
   :type producer_index: int
   :param producer_unique_id: The traversal-specific unique id of the producing activity
   :type producer_unique_id: int
   :param product_index: The matrix row index of the consumed product
   :type product_index: int
   :param amount: The amount of the product demanded by the consumer. Not scaled to producer production amount.
   :type amount: float

   .. py:attribute:: amount
      :type: float

      

   .. py:attribute:: consumer_index
      :type: int

      

   .. py:attribute:: consumer_unique_id
      :type: int

      

   .. py:attribute:: producer_index
      :type: int

      

   .. py:attribute:: producer_unique_id
      :type: int

      

   .. py:attribute:: product_index
      :type: int

      


.. py:class:: Flow


   A characterized biosphere flow associated with a given `Node` instance.

   :param flow_datapackage_id: The id that identifies the biosphere flow in the datapackage
   :type flow_datapackage_id: int
   :param flow_index: The matrix row index of the biosphere flow
   :type flow_index: int
   :param activity_unique_id: The `Node.unique_id` of this instance of the emitting activity
   :type activity_unique_id: int
   :param activity_id: The id that identifies the emitting activity in the datapackage
   :type activity_id: int
   :param activity_index: The matrix column index of the emitting activity
   :type activity_index: int
   :param amount: The amount of the biosphere flow being emitting by this activity instance
   :type amount: float
   :param score: The LCIA score for `amount` of this biosphere flow
   :type score: float

   .. py:attribute:: activity_id
      :type: int

      

   .. py:attribute:: activity_index
      :type: int

      

   .. py:attribute:: activity_unique_id
      :type: int

      

   .. py:attribute:: amount
      :type: float

      

   .. py:attribute:: flow_datapackage_id
      :type: int

      

   .. py:attribute:: flow_index
      :type: int

      

   .. py:attribute:: score
      :type: float

      


.. py:class:: NewNodeEachVisitGraphTraversal


   Traverse a supply chain, following paths of greatest impact.

   This implementation uses a queue of datasets to assess. As the supply chain is traversed, activities are added to a list sorted by LCA score. Each activity in the sorted list is assessed, and added to the supply chain graph, as long as its impact is above a certain threshold, and the maximum number of calculations has not been exceeded.

   Because the next dataset assessed is chosen by its impact, not its position in the graph, this is neither a breadth-first nor a depth-first search, but rather "importance-first".

   This class is written in a functional style, and the class serves mainly to collect methods which belong together. There are only `classmethods` and no state is stored on the class itself.

   Should be used by calling the ``calculate`` method. All other functions should be considered an internal API.

   .. warning:: Graph traversal with multioutput processes only works when other inputs are substituted (see `Multioutput processes in LCA <http://chris.mutel.org/multioutput.html>`__ for a description of multiputput process math in LCA).


   .. py:method:: add_biosphere_flows(flows: list[Flow], matrix: scipy.sparse.spmatrix, lca: bw2calc.LCA, node: Node, biosphere_cutoff_score: float) -> None
      :classmethod:

      Add individual biosphere flows as `Flow` instances to `flow` if their score is above `biosphere_cutoff_score`.

      :param flows: List of existing `Flow` instances
      :type flows: list
      :param matrix: Pre-calculated characterization times biosphere matrix
      :type matrix: scipy.sparse.spmatrix
      :param lca: LCA class instance
      :type lca: bw2calc.LCA
      :param node: Node whose direct biosphere flows we are examining
      :type node: `Node`
      :param biosphere_cutoff_score: Score below which individual characterized biosphere flows are ignored
      :type biosphere_cutoff_score: float

      :returns: Modifies `flows` by adding new `Flow` instances
      :rtype: `None`


   .. py:method:: calculate(lca_object: bw2calc.LCA, cutoff: float | None = 0.005, biosphere_cutoff: float | None = 0.0001, max_calc: int | None = 100000.0, skip_coproducts: bool | None = False, separate_biosphere_flows: bool | None = True, static_activity_indices: set[int] | None = set(), functional_unit_unique_id: int | None = -1) -> dict
      :classmethod:

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

      :param lca_object: Already instantiated `LCA` object with inventory and impact
                         assessment calculated.
      :type lca_object: bw2calc.LCA
      :param cutoff: Cutoff value used to stop graph traversal. Fraction of total score,
                     should be in `(0, 1)`
      :type cutoff: float
      :param biosphere_cutoff: Cutoff value used to determine if a separate biosphere node is
                               added. Fraction of total score.
      :type biosphere_cutoff: float
      :param max_calc: Maximum number of inventory calculations to perform
      :type max_calc: int
      :param skip_coproducts: Don't traverse co-production edges, i.e. production edges other
                              than the reference product
      :type skip_coproducts: bool
      :param separate_biosphere_flows: Add separate `Flow` nodes for important individual biosphere
                                       emissions
      :type separate_biosphere_flows: bool
      :param static_activity_indices: A set of activity matrix indices which we don't want the graph to
                                      traverse
      :type static_activity_indices: set
      :param functional_unit_unique_id: An integer id we can use for the functional unit virtual activity.
                                        Shouldn't overlap any other activity ids. Don't change unless you
                                        really know what you are doing.
      :type functional_unit_unique_id: int

      :returns: Dictionary with keys `nodes`, `edges`, `flows`, `calculation_counter`
      :rtype: dict


   .. py:method:: get_characterized_biosphere(lca: bw2calc.LCA) -> scipy.sparse.spmatrix
      :classmethod:

      Pre-calculate the characterized biosphere matrix.

      Broken out as a separate method because subclasses like regionalized
      LCA could have more complicated characterization.

      :param lca: LCA class instance
      :type lca: bw2calc.LCA

      :returns: Unmapped matrix of biosphere flows by activities.
      :rtype: scipy.sparse.spmatrix


   .. py:method:: get_demand_vector_for_activity(node: Node, skip_coproducts: bool, matrix: scipy.sparse.spmatrix) -> (list[int], list[float])
      :classmethod:

      Get input matrix indices and amounts for a given activity. Ignores the reference production exchanges and optionally other co-production exchanges.

      :param node: Activity whose inputs we are iterating over
      :type node: `Node`
      :param skip_coproducts: Whether or not to ignore positive production exchanges other than the reference product, which is always ignored
      :type skip_coproducts: bool
      :param matrix: Technosphere matrix
      :type matrix: scipy.sparse.spmatrix

      :returns: * **row indices** (*list*) -- Integer row indices for products consumed by `Node`
                * **amounts** (*list*) -- The amount of each product consumed, scaled to `Node.supply_amount`. Same order as row indices.


   .. py:method:: get_production_exchanges(mapped_matrix: matrix_utils.MappedMatrix) -> (numpy.array, numpy.array)
      :classmethod:

      Get matrix row and column indices of productions exchanges by trying a
      series of heuristics. See documentation for
      ``guess_production_exchanges``.

      Broken out as a separate method because subclasses could change this logic.

      :param mapped_matrix: A matrix and mapping data (from database ids to matrix indices)
                            from the ``matrix_utils`` library. Normally built automatically by
                            an ``LCA`` class. Should be the ``technosphere_matrix`` or
                            equivalent.
      :type mapped_matrix: matrix_utils.MappedMatrix

      :returns: The matrix row and column indices of the production exchanges.
      :rtype: (numpy.array, numpy.array)


   .. py:method:: traverse(heap: list, nodes: dict[Node], edges: list[Edge], flows: list[Flow], max_calc: int, cutoff_score: float, characterized_biosphere: scipy.sparse.spmatrix, calculation_count: Counter, static_activity_indices: set, production_exchange_mapping: dict[int, int], technosphere_matrix: scipy.sparse.spmatrix, lca: bw2calc.LCA, caching_solver: CachingSolver, skip_coproducts: bool, separate_biosphere_flows: bool, biosphere_cutoff_score: float) -> None
      :classmethod:

      Perform the graph traversal from the initial functional unit edges.

      :param heap: The `heapq` list of nodes to traverse
      :type heap: list
      :param nodes: Dictionary of already visited `Nodes`
      :type nodes: dict
      :param edges: List of visited `Edges`
      :type edges: list
      :param flows: List of significant seen `Flows`
      :type flows: list
      :param max_calc: Maximum number of inventory calculations to perform
      :type max_calc: int
      :param cutoff_score: Score below which graph edges are ignored. We always consider the absolute value of edges scores.
      :type cutoff_score: float
      :param characterized_biosphere: The pre-calculated characterization time biosphere matrix
      :type characterized_biosphere: spmatrix
      :param calculation_count: Counter object tracking number of lci calculations
      :type calculation_count: `Counter`
      :param static_activity_indices: A set of activity matrix indices which we don't want the graph to
                                      traverse
      :type static_activity_indices: set
      :param production_exchange_mapping: Mapping of product matrix row indices to the activity matrix column indices for which they are reference products
      :type production_exchange_mapping: dict
      :param technosphere_matrix: LCA technosphere matrix
      :type technosphere_matrix: scipy.sparse.spmatrix
      :param lca: Already instantiated `LCA` object with inventory and impact
                  assessment calculated.
      :type lca: bw2calc.LCA
      :param caching_solver: Solver which caches solutions to linear algebra problems
      :type caching_solver: `CachingSolver`
      :param skip_coproducts: Don't traverse co-production edges, i.e. production edges other
                              than the reference product
      :type skip_coproducts: bool
      :param separate_biosphere_flows: Add separate `Flow` nodes for important individual biosphere
                                       emissions
      :type separate_biosphere_flows: bool
      :param biosphere_cutoff_score: Score below which individual biosphere flows are not added to `flows`
      :type biosphere_cutoff_score: float

      :returns: Modifies `heap`, `nodes`, `edges`, and `flows` in-place
      :rtype: `None`


   .. py:method:: traverse_edges(consumer_index: int, consumer_unique_id: int, product_indices: list[int], product_amounts: list[float], lca: bw2calc.LCA, calculation_count: Counter, characterized_biosphere: scipy.sparse.spmatrix, matrix: scipy.sparse.spmatrix, edges: list[Edge], flows: list[Flow], nodes: list[Node], heap: list, production_exchange_mapping: dict[int, int], static_activity_indices: set[int], separate_biosphere_flows: bool, caching_solver: CachingSolver, biosphere_cutoff_score: float, cutoff_score: float) -> None
      :classmethod:



.. py:class:: Node


   A visited activity in a supply chain graph. Although our graph is cyclic, we treat each activity as a separate node every time we visit it.

   :param unique_id: A unique integer id for this visit to this activity node
   :type unique_id: int
   :param activity_datapackage_id: The id that identifies this activity in the datapackage, and hence in the database
   :type activity_datapackage_id: int
   :param activity_index: The technosphere matrix column index of this activity
   :type activity_index: int
   :param reference_product_datapackage_id: The id that identifies the reference product of this activity in the datapackage
   :type reference_product_datapackage_id: int
   :param reference_product_index: The technosphere matrix row index of this activity's reference product
   :type reference_product_index: int
   :param reference_product_production_amount: The *net* production amount of this activity's reference product
   :type reference_product_production_amount: float
   :param supply_amount: The amount of the *activity* (not reference product!) needed to supply the demand from the requesting supply chain edge.
   :type supply_amount: float
   :param cumulative_score: Total LCIA score attributed to `supply_amount` of this activity. Includes direct emissions unless explicitly removed.
   :type cumulative_score: float
   :param direct_emissions_score: Total LCIA score attributed only to the direct characterized biosphere flows of `supply_amount` of this activity.
   :type direct_emissions_score: float

   .. py:attribute:: activity_datapackage_id
      :type: int

      

   .. py:attribute:: activity_index
      :type: int

      

   .. py:attribute:: cumulative_score
      :type: float

      

   .. py:attribute:: direct_emissions_score
      :type: float

      

   .. py:attribute:: reference_product_datapackage_id
      :type: int

      

   .. py:attribute:: reference_product_index
      :type: int

      

   .. py:attribute:: reference_product_production_amount
      :type: float

      

   .. py:attribute:: supply_amount
      :type: float

      

   .. py:attribute:: unique_id
      :type: int

      


.. py:data:: databases

   

