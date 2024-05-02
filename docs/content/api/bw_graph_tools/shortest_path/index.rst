:py:mod:`bw_graph_tools.shortest_path`
======================================

.. py:module:: bw_graph_tools.shortest_path

.. autoapi-nested-parse::

   Created on November 12, 2019
   @author: Quentin Lutz <qlutz@enst.fr>
   From scikit-network version 0.30

   BSD License

   Copyright (c) 2018, Scikit-network Developers
   Bertrand Charpentier <bertrand.charpentier@live.fr>
   Thomas Bonald <thomas.bonald@telecom-paristech.fr>
   All rights reserved.

   Redistribution and use in source and binary forms, with or without modification,
   are permitted provided that the following conditions are met:

   * Redistributions of source code must retain the above copyright notice, this
     list of conditions and the following disclaimer.

   * Redistributions in binary form must reproduce the above copyright notice, this
     list of conditions and the following disclaimer in the documentation and/or
     other materials provided with the distribution.

   * Neither the name of the copyright holder nor the names of its
     contributors may be used to endorse or promote products derived from this
     software without specific prior written permission.

   THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS" AND
   ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
   WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE DISCLAIMED.
   IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT,
   INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING,
   BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE,
   DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY
   OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE
   OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED
   OF THE POSSIBILITY OF SUCH DAMAGE.



Module Contents
---------------


Functions
~~~~~~~~~

.. autoapisummary::

   bw_graph_tools.shortest_path.get_distances
   bw_graph_tools.shortest_path.get_shortest_path



.. py:function:: get_distances(adjacency: scipy.sparse.csr_matrix, sources: Optional[Union[int, Iterable]] = None, method: str = 'D', return_predecessors: bool = False, unweighted: bool = False, n_jobs: Optional[int] = None)

   Compute distances between nodes.

   * Graphs
   * Digraphs


   Based on SciPy (scipy.sparse.csgraph.shortest_path)

   :param adjacency: The adjacency matrix of the graph
   :param sources: If specified, only compute the paths for the points at the given indices. Will not work with ``method =='FW'``.
   :param method: The method to be used.

                  * ``'D'`` (Dijkstra),
                  * ``'BF'`` (Bellman-Ford),
                  * ``'J'`` (Johnson).
   :param return_predecessors: If ``True``, the size predecessor matrix is returned
   :param unweighted: If ``True``, the weights of the edges are ignored
   :param n_jobs: If an integer value is given, denotes the number of workers to use (-1 means the maximum number will be used).
                  If ``None``, no parallel computations are made.

   :returns: * **dist_matrix** (*np.ndarray*) -- Matrix of distances between nodes. ``dist_matrix[i,j]`` gives the shortest
               distance from the ``i``-th source to node ``j`` in the graph (infinite if no path exists
               from the ``i``-th source to node ``j``).
             * **predecessors** (*np.ndarray, optional*) -- Returned only if ``return_predecessors == True``. The matrix of predecessors, which can be used to reconstruct
               the shortest paths. Row ``i`` of the predecessor matrix contains information on the shortest paths from the
               ``i``-th source: each entry ``predecessors[i, j]`` gives the index of the previous node in the path from
               the ``i``-th source to node ``j`` (-1 if no path exists from the ``i``-th source to node ``j``).


.. py:function:: get_shortest_path(adjacency: scipy.sparse.csr_matrix, sources: Union[int, Iterable], targets: Union[int, Iterable], method: str = 'D', unweighted: bool = False, n_jobs: Optional[int] = None)

   Compute the shortest paths in the graph.

   :param adjacency: The adjacency matrix of the graph
   :param sources: Sources nodes.
   :type sources: int or iterable
   :param targets: Target nodes.
   :type targets: int or iterable
   :param method: The method to be used.

                  * ``'D'`` (Dijkstra),
                  * ``'BF'`` (Bellman-Ford),
                  * ``'J'`` (Johnson).
   :param unweighted: If ``True``, the weights of the edges are ignored
   :param n_jobs: If an integer value is given, denotes the number of workers to use (-1 means the maximum number will be used).
                  If ``None``, no parallel computations are made.

   :returns: **paths** -- If single source and single target, return a list containing the nodes on the path from source to target.
             If multiple sources or multiple targets, return a list of paths as lists.
             An empty list means that the path does not exist.
   :rtype: list

   .. rubric:: Examples

   >>> from sknetwork.data import linear_digraph
   >>> adjacency = linear_digraph(3)
   >>> get_shortest_path(adjacency, 0, 2)
   [0, 1, 2]
   >>> get_shortest_path(adjacency, 2, 0)
   []
   >>> get_shortest_path(adjacency, 0, [1, 2])
   [[0, 1], [0, 1, 2]]
   >>> get_shortest_path(adjacency, [0, 1], 2)
   [[0, 1, 2], [1, 2]]


