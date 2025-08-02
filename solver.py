from cube_utils import CubeUtils
from coordinate_cube import CoordCube
from cubie_cube import CubieCube

class Search:

    MAX_PRE_MOVES = 20
    TRY_INVERSE_SOLUTION = True
    TRY_ALL_THREE_AXES = True
    
    USE_CONJUGATE_PRUNING = CubeUtils.USE_TWIST_FLIP_PRUNING
    MIN_PHASE1_LENGTH_AFTER_PREMOVES = 7
    MAX_PHASE2_DEPTH = 13

    inited = False

    def __init__(self):
        self.move = [0] * 31
        self.solution_move_sequence = [0] * 31

        self.phase1_nodes = [CoordCube() for _ in range(21)]
        self.phase1_cubie_cubes = [CubieCube() for _ in range(21)]

        self.urf_conjugated_cubie_cubes = [CubieCube() for _ in range(6)]
        self.urf_conjugated_coordinate_cubes = [CoordCube() for _ in range(6)]

        self.pre_move_cubie_cubes = [None] * (self.MAX_PRE_MOVES + 1)
        for i in range(self.MAX_PRE_MOVES):
            self.pre_move_cubie_cubes[i + 1] = CubieCube()

        self.pre_move_sequence = [0] * self.MAX_PRE_MOVES
        self.pre_move_sequence_length = 0
        self.max_pre_moves_to_try = 0
        self.phase2_cubie_cube = None

        self.self_symmetries = 0
        self.conjugate_mask = 0
        self.urf_conjugate_index = 0
        self.phase1_length = 0
        self.current_phase1_depth = 0
        self.max_phase2_depth_allowed = 0
        self.sol = 0
        self.solution_string = ""
        self.probe = 0
        self.max_probes = 0
        self.min_probes = 0
        self.verbosity_level = 0
        self.valid_phase1_moves_count = 0
        self.allow_shorter_phase1 = False
        self.cc = CubieCube()
        self.is_recursive_call = False

    # verbosity_level flags
    USE_SEPARATOR = 0x1
    INVERSE_SOLUTION = 0x2
    APPEND_LENGTH = 0x4
    OPTIMAL_SOLUTION = 0x8

    def solution(self, facelets: str, maxDepth: int, max_probes: int, min_probes: int, verbosity_level: int) -> str:
        check = self.verify_facelet_string(facelets)
        if check != 0:
            return f"Error {abs(check)}"

        self.sol = maxDepth + 1
        self.probe = 0
        self.max_probes = max_probes
        self.min_probes = min(min_probes, max_probes)
        self.verbosity_level = verbosity_level
        self.solution = None
        self.is_recursive_call = False

        Search.init()
        self.initialize_search_parameters()

        return self.search()
        
    def initialize_search_parameters(self):
        self.conjugate_mask = (0 if self.TRY_INVERSE_SOLUTION else 0x38) | (0 if self.TRY_ALL_THREE_AXES else 0x36)
        self.self_symmetries = self.cc.calculate_self_symmetries()

        if (self.self_symmetries >> 16) & 0xffff:
            self.conjugate_mask |= 0x12
        if (self.self_symmetries >> 32) & 0xffff:
            self.conjugate_mask |= 0x24
        if (self.self_symmetries >> 48) & 0xffff:
            self.conjugate_mask |= 0x38

        self.self_symmetries &= 0xffffffffffff
        self.max_pre_moves_to_try = 0 if self.conjugate_mask > 7 else self.MAX_PRE_MOVES

        for i in range(6):
            self.urf_conjugated_cubie_cubes[i].copy(self.cc)
            self.urf_conjugated_coordinate_cubes[i].set_coordinates_with_pruning(self.urf_conjugated_cubie_cubes[i], 20)
            self.cc.perform_urf_conjugation()
            if i % 3 == 2:
                self.cc.invert_cubie_cube()

    @staticmethod
    def init():
        if not Search.inited:
            CubieCube.initialize_moves()
            CubieCube.initialize_symmetries()
        CoordCube.init()
        Search.inited = True
    
    def verify_facelet_string(self, facelets: str) -> int:
        count = 0x000000
        f = [0] * 54
        try:
            center = ''.join([
                facelets[CubeUtils.U5],
                facelets[CubeUtils.R5],
                facelets[CubeUtils.F5],
                facelets[CubeUtils.D5],
                facelets[CubeUtils.L5],
                facelets[CubeUtils.B5],
            ])
            for i in range(54):
                f[i] = center.find(facelets[i])
                if f[i] == -1:
                    return -1
                count += 1 << (f[i] << 2)
        except Exception:
            return -1

        if count != 0x999999:
            return -1

        CubeUtils.facelet_string_to_cubie_cube(f, self.cc)
        return self.cc.verify_facelet_string()
    
    def search_phase1_with_pre_moves(self, maxl: int, lm: int, cc: CubieCube, ssym: int) -> int:
        self.pre_move_sequence_length = self.max_pre_moves_to_try - maxl

        if (self.is_recursive_call and self.current_phase1_depth == self.phase1_length - self.pre_move_sequence_length) or \
        (not self.is_recursive_call and (self.pre_move_sequence_length == 0 or ((0x36FB7 >> lm) & 1) == 0)):

            self.current_phase1_depth = self.phase1_length - self.pre_move_sequence_length
            self.phase1_cubie_cubes[0] = cc
            self.allow_shorter_phase1 = (self.current_phase1_depth == self.MIN_PHASE1_LENGTH_AFTER_PREMOVES and self.pre_move_sequence_length != 0)

            if self.phase1_nodes[self.current_phase1_depth + 1].set_coordinates_with_pruning(cc, self.current_phase1_depth) and \
                self.phase1(self.phase1_nodes[self.current_phase1_depth + 1], ssym, self.current_phase1_depth, -1) == 0: #<- FIX
                return 0

        if maxl == 0 or self.pre_move_sequence_length + self.MIN_PHASE1_LENGTH_AFTER_PREMOVES >= self.phase1_length:
            return 1

        skipMoves = CubieCube.get_skippable_moves_for_symmetry(ssym)

        if maxl == 1 or self.pre_move_sequence_length + 1 + self.MIN_PHASE1_LENGTH_AFTER_PREMOVES >= self.phase1_length:
            skipMoves |= 0x36FB7

        lm = (lm // 3) * 3

        for m in range(18):
            if m == lm or m == lm - 9 or m == lm + 9:
                m += 2
                continue
            if (self.is_recursive_call and m != self.pre_move_sequence[self.max_pre_moves_to_try - maxl]) or \
            ((skipMoves & (1 << m)) != 0):
                continue

            CubieCube.multiply_corners(CubieCube.MOVE_CUBE_STATES[m], cc, self.pre_move_cubie_cubes[maxl])
            CubieCube.multiply_edges(CubieCube.MOVE_CUBE_STATES[m], cc, self.pre_move_cubie_cubes[maxl])
            self.pre_move_sequence[self.max_pre_moves_to_try - maxl] = m

            ret = self.search_phase1_with_pre_moves(
                maxl - 1,
                m,
                self.pre_move_cubie_cubes[maxl],
                ssym & CubieCube.MOVE_CUBE_SYMMETRIES[m]
            )
            if ret == 0:
                return 0

        return 1

    def search(self) -> str:
        self.phase1_length = self.phase1_length if self.is_recursive_call else 0

        while self.phase1_length < self.sol:
            self.max_phase2_depth_allowed = min(self.MAX_PHASE2_DEPTH, self.sol - self.phase1_length)

            self.urf_conjugate_index = self.urf_conjugate_index if self.is_recursive_call else 0
            while self.urf_conjugate_index < 6:
                if (self.conjugate_mask & (1 << self.urf_conjugate_index)) != 0:
                    self.urf_conjugate_index += 1
                    continue

                if self.search_phase1_with_pre_moves(self.max_pre_moves_to_try, -30, self.urf_conjugated_cubie_cubes[self.urf_conjugate_index], int(self.self_symmetries & 0xffff)) == 0:
                    return "Error 8" if self.solution is None else self.solution

                self.urf_conjugate_index += 1

            self.phase1_length += 1

        return "Error 7" if self.solution is None else self.solution

    def initialize_phase2_from_pre_moves(self) -> int:
        self.is_recursive_call = False
        if self.probe >= (self.max_probes if self.solution is None else self.min_probes):
            return 0

        self.probe += 1

        for i in range(self.valid_phase1_moves_count, self.current_phase1_depth):
            CubieCube.multiply_corners(self.phase1_cubie_cubes[i], CubieCube.MOVE_CUBE_STATES[self.move[i]], self.phase1_cubie_cubes[i + 1])
            CubieCube.multiply_edges(self.phase1_cubie_cubes[i], CubieCube.MOVE_CUBE_STATES[self.move[i]], self.phase1_cubie_cubes[i + 1])

        self.valid_phase1_moves_count = self.current_phase1_depth
        self.phase2_cubie_cube = self.phase1_cubie_cubes[self.current_phase1_depth]

        ret = self.initialize_phase2()
        if ret == 0 or self.pre_move_sequence_length == 0 or ret == 2:
            return ret

        m = (self.pre_move_sequence[self.pre_move_sequence_length - 1] // 3) * 3 + 1
        self.phase2_cubie_cube = CubieCube()
        CubieCube.multiply_corners(CubieCube.MOVE_CUBE_STATES[m], self.phase1_cubie_cubes[self.current_phase1_depth], self.phase2_cubie_cube)
        CubieCube.multiply_edges(CubieCube.MOVE_CUBE_STATES[m], self.phase1_cubie_cubes[self.current_phase1_depth], self.phase2_cubie_cube)

        self.pre_move_sequence[self.pre_move_sequence_length - 1] += 2 - (self.pre_move_sequence[self.pre_move_sequence_length - 1] % 3) * 2
        ret = self.initialize_phase2()
        self.pre_move_sequence[self.pre_move_sequence_length - 1] += 2 - (self.pre_move_sequence[self.pre_move_sequence_length - 1] % 3) * 2
        return ret

    def initialize_phase2(self) -> int:
        p2corn = self.phase2_cubie_cube.get_corner_permutation_symmetry()
        p2csym = p2corn & 0xf
        p2corn >>= 4

        p2edge = self.phase2_cubie_cube.get_edge_permutation_symmetry()
        p2esym = p2edge & 0xf
        p2edge >>= 4

        p2mid = self.phase2_cubie_cube.get_middle_permutation_index()

        prun = max(
            CoordCube.get_pruning_table_value(
                CoordCube.EDGE_PERMUTATION_CORNER_COMBINATION_PRUNING_TABLE,
                p2edge * CoordCube.N_COMB +
                CoordCube.CORNER_COMBINATION_PLUS_PARITY_CONJUGATION_TABLE[
                    CubieCube.PERMUTATION_TO_COMBINATION_PLUS_PARITY[p2corn] & 0xff
                ][CubieCube.SYMMETRY_MULTIPLICATION_INVERSE_TABLE[p2esym][p2csym]]
            ),
            CoordCube.get_pruning_table_value(
                CoordCube.MIDDLE_CORNER_PERMUTATION_PRUNING_TABLE,
                p2corn * CoordCube.N_MPERM +
                CoordCube.MIDDLE_PERMUTATION_CONJUGATION_TABLE[p2mid][p2csym]
            )
        )

        if prun >= self.max_phase2_depth_allowed:
            return 2 if prun > self.max_phase2_depth_allowed else 1

        for depth2 in range(self.max_phase2_depth_allowed - 1, prun - 1, -1):
            ret = self.phase2(p2edge, p2esym, p2corn, p2csym, p2mid, depth2, self.current_phase1_depth, 10) #<- FIX
            if ret < 0:
                break

            depth2 -= ret
            self.sol = 0

            for i in range(self.current_phase1_depth + depth2):
                self.append_move_to_solution(self.move[i])
            for i in range(self.pre_move_sequence_length - 1, -1, -1):
                self.append_move_to_solution(self.pre_move_sequence[i])

            self.solution = self.solution_to_string()

        if depth2 != self.max_phase2_depth_allowed - 1:
            self.max_phase2_depth_allowed = min(self.MAX_PHASE2_DEPTH, self.sol - self.phase1_length)
            return 0 if self.probe >= self.min_probes else 1
        else:
            return 1

    def phase1(self, node, ssym, maxl, lm):
        if node.prun == 0 and maxl < 5:
            if self.allow_shorter_phase1 or maxl == 0:
                self.current_phase1_depth -= maxl
                ret = self.initialize_phase2_from_pre_moves()
                self.current_phase1_depth += maxl
                return ret
            else:
                return 1

        skipMoves = CubieCube.get_skippable_moves_for_symmetry(ssym)

        for axis in range(0, 18, 3):
            if axis == lm or axis == lm - 9:
                continue
            for power in range(3):
                m = axis + power

                if (self.is_recursive_call and m != self.move[self.current_phase1_depth - maxl]) or \
                (skipMoves != 0 and (skipMoves & (1 << m)) != 0):
                    continue

                prun = self.phase1_nodes[maxl].move_and_get_pruning_table_value_value(node, m, True)
                if prun > maxl:
                    break
                elif prun == maxl:
                    continue

                if self.USE_CONJUGATE_PRUNING:
                    prun = self.phase1_nodes[maxl].conjugate_move_and_get_pruning_table_value_value(node, m)
                    if prun > maxl:
                        break
                    elif prun == maxl:
                        continue

                self.move[self.current_phase1_depth - maxl] = m
                self.valid_phase1_moves_count = min(self.valid_phase1_moves_count, self.current_phase1_depth - maxl)
                ret = self.phase1(self.phase1_nodes[maxl], ssym & CubieCube.MOVE_CUBE_SYMMETRIES[m], maxl - 1, axis)
                if ret == 0:
                    return 0
                elif ret == 2:
                    break
        return 1

    def append_move_to_solution(self, cur_move):
        if self.sol == 0:
            self.solution_move_sequence[self.sol] = cur_move
            self.sol += 1
            return

        axis_cur = cur_move // 3
        axis_last = self.solution_move_sequence[self.sol - 1] // 3

        if axis_cur == axis_last:
            pow_ = (cur_move % 3 + self.solution_move_sequence[self.sol - 1] % 3 + 1) % 4
            if pow_ == 3:
                self.sol -= 1
            else:
                self.solution_move_sequence[self.sol - 1] = axis_cur * 3 + pow_
            return

        if self.sol > 1 and axis_cur % 3 == axis_last % 3 and axis_cur == self.solution_move_sequence[self.sol - 2] // 3:
            pow_ = (cur_move % 3 + self.solution_move_sequence[self.sol - 2] % 3 + 1) % 4
            if pow_ == 3:
                self.solution_move_sequence[self.sol - 2] = self.solution_move_sequence[self.sol - 1]
                self.sol -= 1
            else:
                self.solution_move_sequence[self.sol - 2] = axis_cur * 3 + pow_
            return
            
        self.solution_move_sequence[self.sol] = cur_move
        self.sol += 1

    def phase2(self, edge, esym, corn, csym, mid, maxl, depth, lm):
        if edge == 0 and corn == 0 and mid == 0:
            return maxl

        move_mask = CubeUtils.CHECK_MOVE_TO_BIT_MAP[lm]
        m = 0
        while m < 10:
            if (move_mask >> m) & 1 != 0:
                m += (0x42 >> m) & 3  # Jump to the next valid axis.
                m += 1               # The for-loop's own increment.
                continue

            # --- Apply move and calculate next coordinates ---
            midx = CoordCube.MIDDLE_PERMUTATION_MOVE_TABLE[mid][m]
            cornx = CoordCube.CORNER_PERMUTATION_MOVE_TABLE[corn][CubieCube.SYMMETRY_UP_DOWN_MOVE_TABLE[csym][m]]
            csymx = CubieCube.SYMMETRY_MULTIPLICATION_TABLE[cornx & 0xf][csym]
            cornx >>= 4
            edgex = CoordCube.EDGE_PERMUTATION_MOVE_TABLE[edge][CubieCube.SYMMETRY_UP_DOWN_MOVE_TABLE[esym][m]]
            esymx = CubieCube.SYMMETRY_MULTIPLICATION_TABLE[edgex & 0xf][esym]
            edgex >>= 4

            edgei = CubieCube.get_inverse_permutation_symmetry(edgex, esymx, False)
            corni = CubieCube.get_inverse_permutation_symmetry(cornx, csymx, True)

            # --- Pruning Check 1 ---
            prun = CoordCube.get_pruning_table_value(
                CoordCube.EDGE_PERMUTATION_CORNER_COMBINATION_PRUNING_TABLE,
                (edgei >> 4) * CoordCube.N_COMB + CoordCube.CORNER_COMBINATION_PLUS_PARITY_CONJUGATION_TABLE[CubieCube.PERMUTATION_TO_COMBINATION_PLUS_PARITY[corni >> 4] & 0xff][CubieCube.SYMMETRY_MULTIPLICATION_INVERSE_TABLE[edgei & 0xf][corni & 0xf]]
            )
            if prun >= maxl:
                m += ((0x42 >> m) & 3) & (maxl - prun)  # Perform heuristic jump.
                m += 1                                # The for-loop's own increment.
                continue

            # --- Pruning Check 2 ---
            prun = max(
                CoordCube.get_pruning_table_value(CoordCube.MIDDLE_CORNER_PERMUTATION_PRUNING_TABLE, cornx * CoordCube.N_MPERM + CoordCube.MIDDLE_PERMUTATION_CONJUGATION_TABLE[midx][csymx]),
                CoordCube.get_pruning_table_value(CoordCube.EDGE_PERMUTATION_CORNER_COMBINATION_PRUNING_TABLE, edgex * CoordCube.N_COMB + CoordCube.CORNER_COMBINATION_PLUS_PARITY_CONJUGATION_TABLE[CubieCube.PERMUTATION_TO_COMBINATION_PLUS_PARITY[cornx] & 0xff][CubieCube.SYMMETRY_MULTIPLICATION_INVERSE_TABLE[esymx][csymx]])
            )
            if prun >= maxl:
                m += ((0x42 >> m) & 3) & (maxl - prun)  # Perform heuristic jump.
                m += 1                                # The for-loop's own increment.
                continue
                
            # --- Recursive Call ---
            ret = self.phase2(edgex, esymx, cornx, csymx, midx, maxl - 1, depth + 1, m)
            if ret >= 0:
                self.move[depth] = CubeUtils.UP_DOWN_TO_STANDARD_MOVE_MAP[m]
                return ret
            
            # --- Standard Increment ---
            m += 1
            
        return -1

    def solution_to_string(self):
        sb = []
        urf = (self.urf_conjugate_index + 3) % 6 if (self.verbosity_level & self.INVERSE_SOLUTION) != 0 else self.urf_conjugate_index

        if urf < 3:
            for s in range(self.sol):
                if (self.verbosity_level & self.USE_SEPARATOR) != 0 and s == self.current_phase1_depth:
                    sb.append(".  ")
                move_str = CubeUtils.MOVE_TO_STRING_MAP[CubieCube.URF_MOVE_MAP[urf][self.solution_move_sequence[s]]]
                sb.append(move_str + ' ')
        else:
            for s in range(self.sol - 1, -1, -1):
                move_str = CubeUtils.MOVE_TO_STRING_MAP[CubieCube.URF_MOVE_MAP[urf][self.solution_move_sequence[s]]]
                sb.append(move_str + ' ')
                if (self.verbosity_level & self.USE_SEPARATOR) != 0 and s == self.current_phase1_depth:
                    sb.append(".  ")
        
        # 4. Remove the trailing comma for neatness
        moves_str = ''.join(sb).strip()
        if moves_str.endswith(','):
            moves_str = moves_str[:-1]

        if (self.verbosity_level & self.APPEND_LENGTH) != 0:
            moves_str += f" ({self.sol}f)"

        return moves_str