from typing import Tuple

import matrix_utils as mu
import numpy as np
from scipy import sparse

from bw_graph_tools.errors import UnclearProductionExchange


def to_normalized_adjacency_matrix(
    matrix: sparse.spmatrix, log_transform: bool = True
) -> sparse.csr_matrix:
    """Take a technosphere matrix constructed with Brightway conventions, and return a normalized adjacency matrix.

    In the adjacency matrix A, `A[i,j]` indicates a directed edge **from** row `i` **to** column `j`. However,
    this is the opposite of what we normally want, which is to find a path from the functional activity to
    somewhere in its supply chain. In a Brightway technosphere matrix, `A[i,j]` means **activity** `j` consumes
    the output of activity `i`. To go down the supply chain, however, we would need to go from ``j`` to ``i``.
    Therefore, we take the transpose of the technosphere matrix.

    Normalization is done to remove the effect of activities which don't produce one unit of their reference product.
    For example, if activity `foo` produces two units of `bar` and consumes two units of `baz`, the weight of the
    `baz` edge should be :math:`2 / 2 = 1`.

    In addition to this normalization, we subtract the diagonal and flip the signs of all matrix values. Flipping
    the sign is needed because we want to use a shortest path algorithm, but actually want the longest path. The
    longest path is the path with the highest weight, i.e. the path where the most consumption occurs on.

    By default, we also take the natural log of the data values. This is because our supply chain is multiplicative,
    not additive, and :math:`a \\cdot b = e^{\\ln(a) + \\ln(b)}`. The idea of using the log was borrowed from `David Richardby on Stack Overflow <https://cs.stackexchange.com/questions/83656/traverse-direct-graph-with-multiplicative-edges>`__.

    Assumes that production amounts are on the diagonal.
    """
    matrix = matrix.tocsr().T

    # TBD these values should the NET production values, i.e. we use the production exchanges to get the matrix
    # indices, ensure that we have 1-1 match for production-activity, construct the normalization vector, turn
    # into a diagonal matrix, and then multiply
    normalization = sparse.diags(-1 * matrix.diagonal())
    normalized = (matrix * normalization) + sparse.eye(*matrix.shape)

    if log_transform:
        normalized = normalized.tocoo()
        normalized.data = np.log(normalized.data) * -1
        normalized = normalized.tocsr()

    return normalized


def gpe_first_heuristic(mm: mu.MappedMatrix) -> Tuple[np.ndarray, np.ndarray]:
    """Use first heuristic (same input and output ids) to find production exchange indices.

    If we treat activities and products the same, then an exchange with the row and column id
    is definitely a production exchange location. We don't care if there are duplicates (e.g.
    production and some loss), we will return unique pairs.

    If activities have different ids than products, this won't find anything.

    Returns a tuple of numpy integer matrix indices, rows by columns.
    """

    def get_used_mapped_indices_for_group(
        group: mu.ResourceGroup,
    ) -> Tuple[np.ndarray, np.ndarray]:
        indices = group.get_indices_data()

        # Need to check the original input values, not after mapping when they are
        # normalized to [0, X] range.
        ident_mask = indices["row"] == indices["col"]

        # In theory these values should be on the diagonal, as the input row and col
        # values are the same. However, we don't have a strong guarantee that this is
        # true. So to eliminate duplicate values we combine to a (X, 2) array, and get
        # unique rows.
        # Note that `unique` also does sorting, see
        # https://stackoverflow.com/questions/16970982/find-unique-rows-in-numpy-array
        combined = np.unique(
            np.vstack(
                (
                    group.row_mapper.map_array(indices["row"][ident_mask]),
                    group.col_mapper.map_array(indices["col"][ident_mask]),
                )
            ),
            axis=1,
        )
        row_mapped = combined[0, :]
        col_mapped = combined[1, :]

        if (row_mapped == -1).sum() or (col_mapped == -1).sum():
            ERROR = """
Found unmapped values in technosphere matrix generator, but that should be impossible.

{} unmapped values in the row indices: {}
{} unmapped values in the column indices: {}

Please report this as an issue, something went very wrong!
            """
            raise ValueError(
                ERROR.format(
                    (row_mapped == -1).sum(),
                    indices["row"][row_mapped == -1],
                    (col_mapped == -1).sum(),
                    indices["col"][col_mapped == -1],
                )
            )

        return row_mapped, col_mapped

    first_heuristic = [get_used_mapped_indices_for_group(group) for group in mm.groups]

    row_indices = np.hstack([array for array, _ in first_heuristic])
    col_indices = np.hstack([array for _, array in first_heuristic])

    return row_indices, col_indices


def gpe_second_heuristic(
    mm: mu.MappedMatrix, row_existing: np.ndarray, col_existing: np.ndarray
) -> Tuple[np.ndarray, np.ndarray]:
    """Use second heuristic (single non-flipped entry per column) to find production exchange indices.

    In Brightway convention, consumption exchanges are stored as positive values with ``flip=True``
    so they appear negative in the built matrix. Production exchanges normally have ``flip=False``.
    If exactly one exchange in a column has ``flip=False`` and that column was not already identified
    by the first heuristic, that exchange is the production exchange.

    Operates on raw resource-group data before values are assembled into the matrix, so it is
    unaffected by summing across packages. Columns whose production exchange was already found
    (present in ``col_existing``) are skipped. Resource groups without a flip array are silently
    ignored via ``KeyError``.

    Takes row and column indices already found (``row_existing``, ``col_existing``) and appends any
    new findings. Returns the combined arrays.
    """
    if col_existing.size == mm.matrix.shape[1]:
        return row_existing, col_existing

    not_flipped = []

    for group in mm.groups:
        try:
            # Get indices where flip is false and only one value is present
            h2_col_indices, h2_col_counts = np.unique(
                group.col_masked[~group.flip], return_counts=True
            )
            h2_col_indices = h2_col_indices[h2_col_counts == 1]

            # Remove elements found by first heuristic
            existing_mask = np.isin(h2_col_indices, col_existing)

            # Need mask with correct shape for both row and col indices
            mask = np.isin(group.col_masked[~group.flip], h2_col_indices[~existing_mask])

            not_flipped.append(
                (
                    group.row_masked[~group.flip][mask],
                    group.col_masked[~group.flip][mask],
                )
            )
        except KeyError:
            # No flip array given
            pass

    try:
        row_not_flipped = np.hstack([array for array, _ in not_flipped])
        col_not_flipped = np.hstack([array for _, array in not_flipped])
        return np.hstack([row_existing, row_not_flipped]), np.hstack(
            [col_existing, col_not_flipped]
        )
    except ValueError:
        return row_existing, col_existing


def gpe_third_heuristic(
    mm: mu.MappedMatrix, row_existing: np.ndarray, col_existing: np.ndarray
) -> Tuple[np.ndarray, np.ndarray]:
    """Use third heuristic (single positive value per column) to find production exchange indices.

    Operates on the assembled matrix rather than raw resource-group data. If a column has
    exactly one positive entry and that column was not already identified by earlier heuristics,
    that entry is the production exchange.

    Takes row and column indices already found (``row_existing``, ``col_existing``) and appends
    any new findings. Returns the combined arrays.

    .. note::
        This heuristic can misidentify the production exchange for a waste treatment activity
        that also produces a co-product. If such a column has one positive entry (the co-product)
        and one negative entry (the waste being treated), this heuristic selects the co-product
        row rather than the waste row. The correct assignment would be found by
        :func:`gpe_fourth_heuristic`, but because this heuristic runs first it claims the column
        and the fourth heuristic never inspects it. This is a known ordering limitation.
    """
    if col_existing.size == mm.matrix.shape[1]:
        return row_existing, col_existing

    matrix = mm.matrix.tocoo()

    positive_mask = matrix.data > 0
    row, col = matrix.row[positive_mask], matrix.col[positive_mask]

    existing_mask = ~np.isin(col, col_existing)
    row, col = row[existing_mask], col[existing_mask]

    col_indices, col_counts = np.unique(col, return_counts=True)
    single_mask = np.isin(col, col_indices[col_counts == 1])
    row, col = row[single_mask], col[single_mask]

    if row.size:
        return np.hstack([row_existing, row]), np.hstack([col_existing, col])
    else:
        return row_existing, col_existing


def gpe_fourth_heuristic(
    mm: mu.MappedMatrix, row_existing: np.ndarray, col_existing: np.ndarray
) -> Tuple[np.ndarray, np.ndarray]:
    """Use fourth heuristic (single negative value per column) to find waste-treatment production exchanges.

    Waste treatment activities accept waste as their reference product. In the technosphere matrix
    this appears as a negative entry (the activity consumes the waste flow). If a column has exactly
    one negative entry and that column was not already identified by earlier heuristics, that entry
    is the production exchange for a waste treatment activity.

    Operates on the assembled matrix. Takes row and column indices already found
    (``row_existing``, ``col_existing``) and appends any new findings. Returns the combined arrays.
    """
    if col_existing.size == mm.matrix.shape[1]:
        return row_existing, col_existing

    matrix = mm.matrix.tocoo()

    negative_mask = matrix.data < 0
    row, col = matrix.row[negative_mask], matrix.col[negative_mask]

    existing_mask = ~np.isin(col, col_existing)
    row, col = row[existing_mask], col[existing_mask]

    col_indices, col_counts = np.unique(col, return_counts=True)
    single_mask = np.isin(col, col_indices[col_counts == 1])
    row, col = row[single_mask], col[single_mask]

    if row.size:
        return np.hstack([row_existing, row]), np.hstack([col_existing, col])
    else:
        return row_existing, col_existing


def gpe_fifth_heuristic(
    mm: mu.MappedMatrix, row_existing: np.ndarray, col_existing: np.ndarray
) -> Tuple[np.ndarray, np.ndarray]:
    """Use fifth heuristic (unique product across remaining columns) to find production exchange indices.

    For each product (row) that appears in exactly one of the still-unidentified columns, that
    column is unambiguously the producer or consumer of that product, so the entry is the
    production exchange. To remain fully deterministic, a column is only assigned when exactly
    one such uniquely-pointing row identifies it — if two different unique rows both point to the
    same column we cannot choose between them and that column is left unassigned.

    Operates on the assembled matrix. Takes row and column indices already found
    (``row_existing``, ``col_existing``) and appends any new findings. Returns the combined arrays.
    """
    matrix = mm.matrix.tocoo()

    all_cols = np.arange(mm.matrix.shape[1])
    missing_cols = np.setdiff1d(all_cols, col_existing)

    if not missing_cols.size:
        return row_existing, col_existing

    # Restrict to entries in unidentified columns
    missing_mask = np.isin(matrix.col, missing_cols)
    row, col = matrix.row[missing_mask], matrix.col[missing_mask]

    # Keep only rows that appear in exactly one of the remaining columns
    row_indices, row_counts = np.unique(row, return_counts=True)
    unique_rows = row_indices[row_counts == 1]

    unique_row_mask = np.isin(row, unique_rows)
    new_row, new_col = row[unique_row_mask], col[unique_row_mask]

    # Only assign a column when exactly one unique-row points to it;
    # if two unique rows both point to the same column we can't choose.
    col_indices, col_counts = np.unique(new_col, return_counts=True)
    single_col_mask = np.isin(new_col, col_indices[col_counts == 1])
    new_row, new_col = new_row[single_col_mask], new_col[single_col_mask]

    if new_row.size:
        return np.hstack([row_existing, new_row]), np.hstack([col_existing, new_col])
    else:
        return row_existing, col_existing


def guess_production_exchanges(mm: mu.MappedMatrix) -> Tuple[np.ndarray, np.ndarray]:
    """Try to guess productions exchanges in a mapped technosphere matrix using heuristics from the input data packages.

    Try the following in order per activity (column):

    * Same input and output index
    * Single value where ``flip`` is negative
    * Single positive value
    * Single negative value (waste treatment)
    * Unique product across remaining unidentified columns

    Raises ``UnclearProductionExchange`` if these conditions are not met for any activity.

    Returns integer arrays of the matrix row and column indices where production exchanges were found.

    """
    if mm.matrix.shape[0] == 0:
        raise ValueError("Empty matrix")

    row_indices, col_indices = gpe_first_heuristic(mm)

    # Every column must have an activity with some reference product or the system
    # is not solvable. Therefore we can look across all columns. We will do
    # all the work in matrix indices.
    missing = np.setdiff1d(np.arange(mm.matrix.shape[0]), col_indices, assume_unique=True)

    # Short circuit other steps if possible; assumption is that this step will
    # be taken for most matrices
    if not missing.size:
        return (row_indices, col_indices)

    row_indices, col_indices = gpe_second_heuristic(mm, row_indices, col_indices)
    row_indices, col_indices = gpe_third_heuristic(mm, row_indices, col_indices)
    row_indices, col_indices = gpe_fourth_heuristic(mm, row_indices, col_indices)
    row_indices, col_indices = gpe_fifth_heuristic(mm, row_indices, col_indices)

    # No idea how this could happen, but better raise an error than pass bad data
    if row_indices.shape != col_indices.shape:
        raise ValueError("Guessed row indices do not match guessed column indices.")

    missing = np.setdiff1d(np.arange(mm.matrix.shape[0]), col_indices, assume_unique=True)
    if missing.size:
        raise UnclearProductionExchange(
            "Can't find production exchanges for columns: {}".format(list(missing))
        )

    return (row_indices, col_indices)
