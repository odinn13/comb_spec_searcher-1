
from grids import *
from permuta import *
from permuta.misc import UnionFind
from itertools import combinations, chain
from atrap.tools import basis_partitioning


# Overly strict version, should we just remove it?
def components(tiling, basis):

    cell_to_int = {}

    for cell,_ in tiling:
        # TODO: use integer mapping
        cell_to_int[cell] = len(cell_to_int)

    components = UnionFind(len(cell_to_int))

    # TODO: work through permset first rather than regeneate for each pattern.
    for patt in basis:
        verification_length = tiling.total_points + len(patt)
        verification_length += sum(1 for _, block in tiling.non_points if isinstance(block, PositiveClass))
        for perm_length in range(verification_length + 1):
            containing_perms, _ = basis_partitioning(tiling, perm_length, basis)

            for perm, cell_infos in containing_perms.items():
                assert len(cell_infos) == 1
                for cell_info in cell_infos:
                    cell_perm = [ 0 for i in range(len(perm))]
                    for cell in cell_info.keys():
                        _, _, cell_indices = cell_info[cell]
                        for index in cell_indices:
                            cell_perm[index] = cell

                for occurrence in perm.occurrences_of(patt):
                    cells_to_be_joined = set( cell_perm[i] for i in occurrence )
                    for cell1, cell2 in combinations(list(cells_to_be_joined), 2):
                        components.unite(cell_to_int[cell1], cell_to_int[cell2])

    all_components = {}
    for cell, _ in tiling:
        i = components.find( cell_to_int[cell] )
        if i in all_components:
            all_components[i].append(cell)
        else:
            all_components[i] = [cell]
    cells_of_new_tilings = list( all_components.values() )

    if len(cells_of_new_tilings) == 1:
        return
    strategy = []
    for new_cells in cells_of_new_tilings:
        new_tiling_dict = {}
        for cell in new_cells:
            new_tiling_dict[cell] = tiling[cell]
        strategy.append(Tiling(new_tiling_dict))

    yield ( "the components of tiling", strategy  )
    # Consider unions of components.
#
# # We never use this function. Probably should just delete it.
# def is_reversibly_deletable(tiling, cell, basis):
#     perms_to_consider = {}
#     for patt in basis:
#         verification_length = tiling.total_points + len(patt)
#         verification_length += sum(1 for _, block in tiling.non_points if isinstance(block, PositiveClass))
#         for perm_length in range(verification_length + 1):
#             containing_perms, _ = basis_partitioning(tiling, perm_length, basis)
#
#             # where tells you which cell a point belongs to.
#             for perm, cell_infos in containing_perms.items():
#                 assert len(cell_infos) == 1
#                 for cell_info in cell_infos:
#                     cell_perm = [ 0 for i in range(len(perm))]
#                     for cell in cell_info.keys():
#                         _, _, cell_indices = cell_info[cell]
#                         for index in cell_indices:
#                             cell_perm[index] = cell
#
#         occurrences = [ set( [ cell_perm[i] for i in occurrence ] ) for occurrence in perm.occurrences_of(patt) ]
#
#         if len(occurrences) > 0:
#             if perm in perms_to_consider:
#                 perms_to_consider[perm] += occurrences
#             perms_to_consider[perm] = occurrences
#
#
#     for perm, occurrences in perms_to_consider.items():
#         new_occurrences = []
#         for occurrence in occurrences:
#             if not cell in occurrence:
#                 new_occurrences.append(occurrence)
#         if len(new_occurrences) > 0:
#             continue
#         else:
#             return False
#     return True
#
# def some_random_reverisbly_deletable_strategies(tiling, basis):
#
#     for cell, block in tiling:
#         strategy = []
#         if is_reversibly_deletable(tiling, cell, basis):
#             strategy.append( Tiling( { cell: block } ))
#             new_tiling_dict = dict(tiling)
#             new_tiling_dict.pop(cell)
#             new_tiling = Tiling(new_tiling_dict)
#             strategy.append(new_tiling)
#             yield ( "I reversibly deleted the cell " + str(cell) , strategy )
#
#
# def reversibly_deletably_path_finder(tiling, basis):
#
#     tilingpermset = PermSetTiled(tiling)
#
#     perms_to_consider = {}
#     max_patt_length = max(len(patt) for patt in basis)
#     max_length = tiling.total_points + max_patt_length
#
#     for perm_length in range(max_length + 1):
#         # where tells you which cell a point belongs to.
#         for perm, where in tilingpermset.of_length_with_positions(perm_length):
#             for patt in basis:
#                 if max_length - tiling.total_points >= max_patt_length:
#                     occurrences = [ [ where[ perm[i] ] for i in occurrence ] for occurrence in perm.occurrences_of(patt) ]
#                     if len(occurrences) > 0:
#                         if perm in perms_to_consider:
#                             perms_to_consider[perm] += occurrences
#                         else:
#                             perms_to_consider[perm] = occurrences
#
#     paths = set()
#     for cell in tiling:
#         for path in reversibly_deletably_path_finder_helper( cell, perms_to_consider, tiling ):
#             yield path
#
# def reversibly_deletably_path_finder_helper(cell, perms_to_consider, tiling):
#
#     new_perms_to_consider = {}
#     for perm, occurrences in perms_to_consider.items():
#         new_occurrences = []
#         for occurrence in occurrences:
#             if not any( i == cell for i in occurrence ):
#                 new_occurrences.append(occurrence)
#         if len(new_occurrences) > 0:
#             new_perms_to_consider[perm] = new_occurrences
#         else:
#             return
#     yield [cell]
#     for cell2 in tiling:
#         if cell2 > cell:
#             for path in reversibly_deletably_path_finder_helper(cell2, new_perms_to_consider, tiling):
#                 yield [cell] + path
#
# # def unmixed_subtile(tiling, subtile): # TODO: This is pseudo-code
# #     # I think this is the fastest way to do this, because if we do it row by
# #     # row and then column by column, we need to call the get_row, get_column
# #     # functions, which currently go through all the cells to collect them into
# #     # rows and columns
# #     all_cells = list(tiling.cells())
# #     lac = len(all_cells)
# #     for c1 in range(lac):
# #         for c2 in range(c1+1,lac):
# #             cell1 = all_cells[c1]
# #             cell2 = all_cells[c2]
# #             if cell1[0] == cell2[0] or cell1[1] == cell2[1]: # If the cells share a row or column
# #                 if (cell1 in subtile) != (cell2 in subtile): # If the cells not both in the same place
# #                     return False
# #     return True
#
#
#
# def reachable_tilings_by_reversibly_deleting(tiling, basis, unmixed=False):
#
#     if unmixed:
#         popped_rows = {}
#         popped_columns = {}
#
#     for path in reversibly_deletably_path_finder(tiling, basis):
#
#         new_tiling = dict(tiling)
#
#         for cell in path:
#             new_tiling.pop(cell)
#
#             if unmixed:
#                 if cell[0] in popped_rows:
#                     popped_rows[cell[0]].append( cell[1] )
#                 else:
#                     popped_rows[cell[0]] = [ cell[1] ]
#                 if cell[1] in popped_columns:
#                     popped_columns[cell[1]].append( [cell[0]] )
#                 else:
#                     popped_columns[cell[1]] =  [ cell[0] ]
#
#         if unmixed:
#             mixing = False
#             for row in popped_rows:
#                 if len(popped_rows[row]) != len(tiling.get_row(row)):
#                     mixing = True
#                     break
#             if mixing:
#                 continue
#             for column in popped_columns:
#                 if len(popped_columns[column]) != len(tiling.get_col(column)):
#                     mixing = True
#                     break
#             if mixing:
#                 continue
#
#         yield Tiling(new_tiling), list(new_tiling.keys())
