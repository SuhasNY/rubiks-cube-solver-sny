import bisect
from cube_utils import CubeUtils
from coordinate_cube import CoordCube


class CubieCube:

####################################################### Constants and Class variables #######################################################

    SYMMETRY_EDGE_TO_CORNER_MAGIC_NUMBER = 0x00DDDD00


    CubeSym = [None] * 16
    MOVE_CUBE_STATES = [None] * 18
    MOVE_CUBE_SYMMETRIES = [0] * 18
    FIRST_MOVE_SYMMETRIES = [0] * 48
    SYMMETRY_MULTIPLICATION_TABLE = [[0]*16 for _ in range(16)]
    SYMMETRY_MULTIPLICATION_INVERSE_TABLE = [[0]*16 for _ in range(16)]
    SYMMETRY_MOVE_TABLE = [[0]*18 for _ in range(16)]
    SYMMETRY_8_MOVE_TABLE = [0] * (8 * 18)
    SYMMETRY_UP_DOWN_MOVE_TABLE = [[0]*18 for _ in range(16)]

    FLIP_SYMMETRY_TO_RAW = [0] * CoordCube.N_FLIP_SYM
    TWIST_SYMMETRY_TO_RAW = [0] * CoordCube.N_TWIST_SYM
    EDGE_PERMUTATION_SYMMETRY_TO_RAW = [0] * CoordCube.N_PERM_SYM
    PERMUTATION_TO_COMBINATION_PLUS_PARITY = [0] * CoordCube.N_PERM_SYM
    PERMUTATION_INVERSE_EDGE_SYMMETRY = [0] * CoordCube.N_PERM_SYM

    FLIP_RAW_TO_SYMMETRY = bytearray(CoordCube.N_FLIP + CoordCube.N_FLIP_HALF)
    TWIST_RAW_TO_SYMMETRY = bytearray(CoordCube.N_TWIST + CoordCube.N_TWIST_HALF)
    EDGE_PERMUTATION_RAW_TO_SYMMETRY = bytearray(CoordCube.N_PERM_HALF)

    FLIP_SYMMETRY_TO_RAW_FLIPPED = None
    if CubeUtils.USE_TWIST_FLIP_PRUNING:
        FLIP_SYMMETRY_TO_RAW_FLIPPED = [0] * (CoordCube.N_FLIP_SYM * 8)

    SYMMETRY_STATE_TWIST = None
    SYMMETRY_STATE_FLIP = None
    SYMMETRY_STATE_PERMUTATION = None

    URF_CONJUGATE_CUBE = None
    URF_CONJUGATE_CUBE_INVERSE = None

    URF_MOVE_MAP = [
        [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17],
        [6, 7, 8, 0, 1, 2, 3, 4, 5, 15, 16, 17, 9, 10, 11, 12, 13, 14],
        [3, 4, 5, 6, 7, 8, 0, 1, 2, 12, 13, 14, 15, 16, 17, 9, 10, 11],
        [2, 1, 0, 5, 4, 3, 8, 7, 6, 11, 10, 9, 14, 13, 12, 17, 16, 15],
        [8, 7, 6, 2, 1, 0, 5, 4, 3, 17, 16, 15, 11, 10, 9, 14, 13, 12],
        [5, 4, 3, 8, 7, 6, 2, 1, 0, 14, 13, 12, 17, 16, 15, 11, 10, 9],
    ]
    temps = None

    def __init__(self, cperm=None, twist=None, eperm=None, flip=None):
        self.corner_array = list(range(8))  # 8 corner positions
        self.edge_array = [i * 2 for i in range(12)]  # 12 edge positions
        self.temps = None

        if cperm is not None and twist is not None and eperm is not None and flip is not None:
            self.set_corner_permutation_from_index(cperm)
            self.set_twist_from_index(twist)
            CubeUtils.set_permutation_from_index(self.edge_array, eperm, 12, True)
            self.set_flip_from_index(flip)

    @staticmethod
    def initialize_moves():
        CubieCube.MOVE_CUBE_STATES[0] = CubieCube(15120, 0, 119750400, 0)
        CubieCube.MOVE_CUBE_STATES[3] = CubieCube(21021, 1494, 323403417, 0)
        CubieCube.MOVE_CUBE_STATES[6] = CubieCube(8064, 1236, 29441808, 550)
        CubieCube.MOVE_CUBE_STATES[9] = CubieCube(9, 0, 5880, 0)
        CubieCube.MOVE_CUBE_STATES[12] = CubieCube(1230, 412, 2949660, 0)
        CubieCube.MOVE_CUBE_STATES[15] = CubieCube(224, 137, 328552, 137)

        for a in range(0, 18, 3):
            for p in range(2):
                CubieCube.MOVE_CUBE_STATES[a + p + 1] = CubieCube()
                CubieCube.multiply_edges(CubieCube.MOVE_CUBE_STATES[a + p], CubieCube.MOVE_CUBE_STATES[a], CubieCube.MOVE_CUBE_STATES[a + p + 1])
                CubieCube.multiply_corners(CubieCube.MOVE_CUBE_STATES[a + p], CubieCube.MOVE_CUBE_STATES[a], CubieCube.MOVE_CUBE_STATES[a + p + 1])

    @staticmethod
    def initialize_symmetries():
        # from cube_utils import CubeUtils
        c = CubieCube()
        d = CubieCube()

        f2 = CubieCube(cperm=28783, twist=0, eperm=259268407, flip=0)
        u4 = CubieCube(cperm=15138, twist=0, eperm=119765538, flip=7)
        lr2 = CubieCube(cperm=5167, twist=0, eperm=83473207, flip=0)
        for i in range(8):
            lr2.corner_array[i] |= 3 << 3

        for i in range(16):
            sym_cube = CubieCube()
            sym_cube.copy(c)
            CubieCube.CubeSym[i] = sym_cube
            
            CubieCube.multiply_corners(c, u4, d)
            CubieCube.multiply_edges(c, u4, d)
            c.copy(d)

            if i % 4 == 3:
                CubieCube.multiply_corners(c, lr2, d)
                CubieCube.multiply_edges(c, lr2, d)
                c.copy(d)
            if i % 8 == 7:
                CubieCube.multiply_corners(c, f2, d)
                CubieCube.multiply_edges(c, f2, d)
                c.copy(d)

        for i in range(16):
            for j in range(16):
                CubieCube.multiply_corners(CubieCube.CubeSym[i], CubieCube.CubeSym[j], c)
                for k in range(16):
                    if c.corner_array == CubieCube.CubeSym[k].corner_array:
                        CubieCube.SYMMETRY_MULTIPLICATION_TABLE[i][j] = k
                        CubieCube.SYMMETRY_MULTIPLICATION_INVERSE_TABLE[k][j] = i
                        break

        for j in range(18):
            for s in range(16):
                # THIS IS THE CORRECTED LINE
                CubieCube.conjugate_corners(CubieCube.MOVE_CUBE_STATES[j], CubieCube.SYMMETRY_MULTIPLICATION_INVERSE_TABLE[0][s], c)
                for m in range(18):
                    if c.corner_array == CubieCube.MOVE_CUBE_STATES[m].corner_array:
                        CubieCube.SYMMETRY_MOVE_TABLE[s][j] = m
                        CubieCube.SYMMETRY_UP_DOWN_MOVE_TABLE[s][CubeUtils.STANDARD_TO_UP_DOWN_MOVE_MAP[j]] = CubeUtils.STANDARD_TO_UP_DOWN_MOVE_MAP[m]
                        break
                if s % 2 == 0:
                    CubieCube.SYMMETRY_8_MOVE_TABLE[j << 3 | s >> 1] = CubieCube.SYMMETRY_MOVE_TABLE[s][j]

    def get_flip_symmetry(self) -> int:
        return self.flip_raw_to_symmetry(self.get_flip_index())

    def get_twist_symmetry(self) -> int:
        from coordinate_cube import CoordCube
        raw = self.get_twist_index()
        return (0xfff & (CubieCube.TWIST_RAW_TO_SYMMETRY[raw + CoordCube.N_TWIST_HALF] << 4)) | CoordCube.get_pruning_table_value_table_value_byte(CubieCube.TWIST_RAW_TO_SYMMETRY, raw)

    @staticmethod
    def flip_raw_to_symmetry(raw: int) -> int:
        from coordinate_cube import CoordCube
        return (0xfff & (CubieCube.FLIP_RAW_TO_SYMMETRY[raw + CoordCube.N_FLIP_HALF] << 4)) | CoordCube.get_pruning_table_value_table_value_byte(CubieCube.FLIP_RAW_TO_SYMMETRY, raw)

    @staticmethod
    def initialize_symmetry_to_raw_mapping(N_RAW, Sym2Raw, Raw2Sym, SymState, coord):
        N_RAW_HALF = (N_RAW + 1) // 2;
        from coordinate_cube import CoordCube
        c = CubieCube()
        d = CubieCube()

        count = 0
        sym_inc = 1 if coord >= 2 else 2
        is_edge = coord != 1

        for i in range(N_RAW):
            if CoordCube.get_pruning_table_value_table_value_byte(Raw2Sym, i) != 0:
                continue
            if coord == 0: c.set_flip_from_index(i)
            elif coord == 1: c.set_twist_from_index(i)
            elif coord == 2: c.set_edge_permutation_from_index(i)
            
            for s in range(0, 16, sym_inc):
                if is_edge:
                    CubieCube.conjugate_edges(c, s, d)
                else:
                    CubieCube.conjugate_corners(c, s, d)
                
                if coord == 0: idx = d.get_flip_index()
                elif coord == 1: idx = d.get_twist_index()
                elif coord == 2: idx = d.get_edge_permutation_index()

                if coord == 0 and CubeUtils.USE_TWIST_FLIP_PRUNING:
                    CubieCube.FLIP_SYMMETRY_TO_RAW_FLIPPED[(count << 3) | (s >> 1)] = idx
                
                if idx == i:
                    SymState[count] |= 1 << (s // sym_inc)
                
                if CoordCube.get_pruning_table_value_table_value_byte(Raw2Sym, idx) == 0:
                    sym_idx = (count << 4 | s) // sym_inc
                    value_to_set = sym_idx & 0xf
                    CoordCube.set_pruning_table_value_table_value_byte(Raw2Sym, idx, value_to_set)
                    if coord != 2:
                        Raw2Sym[idx + N_RAW_HALF] = sym_idx >> 4

            Sym2Raw[count] = i
            count += 1
        return count
    
    @staticmethod
    def initialize_flip_symmetry_to_raw():
        from coordinate_cube import CoordCube
        CubieCube.SYMMETRY_STATE_FLIP = [0] * CoordCube.N_FLIP_SYM
        CubieCube.initialize_symmetry_to_raw_mapping(CoordCube.N_FLIP, CubieCube.FLIP_SYMMETRY_TO_RAW, CubieCube.FLIP_RAW_TO_SYMMETRY, CubieCube.SYMMETRY_STATE_FLIP, 0)

    @staticmethod
    def initialize_twist_symmetry_to_raw():
        from coordinate_cube import CoordCube
        CubieCube.SYMMETRY_STATE_TWIST = [0] * CoordCube.N_TWIST_SYM
        CubieCube.initialize_symmetry_to_raw_mapping(CoordCube.N_TWIST, CubieCube.TWIST_SYMMETRY_TO_RAW, CubieCube.TWIST_RAW_TO_SYMMETRY, CubieCube.SYMMETRY_STATE_TWIST, 1)

    @staticmethod
    def initialize_permutatioin_symmetry_to_raw():
        from coordinate_cube import CoordCube
        # from cube_utils import CubeUtils
        from solver import Search
        CubieCube.SYMMETRY_STATE_PERMUTATION = [0] * CoordCube.N_PERM_SYM
        CubieCube.initialize_symmetry_to_raw_mapping(CoordCube.N_PERM, CubieCube.EDGE_PERMUTATION_SYMMETRY_TO_RAW, CubieCube.EDGE_PERMUTATION_RAW_TO_SYMMETRY, CubieCube.SYMMETRY_STATE_PERMUTATION, 2)
        cc = CubieCube()
        for i in range(CoordCube.N_PERM_SYM):
            cc.set_edge_permutation_from_index(CubieCube.EDGE_PERMUTATION_SYMMETRY_TO_RAW[i])
            
            comb_p = CubeUtils.get_combination_from_index(cc.edge_array, 0, True)
            if CubeUtils.USE_COMBINATION_PARITY_PRUNING:
                comb_p += CubeUtils.get_permutation_parity(CubieCube.EDGE_PERMUTATION_SYMMETRY_TO_RAW[i], 8) * 70
            CubieCube.PERMUTATION_TO_COMBINATION_PLUS_PARITY[i] = comb_p
            
            cc.invert_cubie_cube()
            CubieCube.PERMUTATION_INVERSE_EDGE_SYMMETRY[i] = cc.get_edge_permutation_symmetry()

    def copy(self, c):
        self.corner_array = c.corner_array[:]
        self.edge_array = c.edge_array[:]

    # ----- Corner permutation -----
    def get_corner_permutation_index(self):
        return CubeUtils.get_index_from_permutation(self.corner_array, 8, False)

    def set_corner_permutation_from_index(self, idx):
        CubeUtils.set_permutation_from_index(self.corner_array, idx, 8, False)

    # ----- Corner orientation -----
    def get_twist_index(self):
        idx = 0
        for i in range(7):
            idx = idx * 3 + (self.corner_array[i] >> 3)
        return idx

    def set_twist_from_index(self, idx):
        twst = 0
        for i in range(6, -1, -1):
            val = idx % 3
            idx //= 3
            self.corner_array[i] = (self.corner_array[i] & 0x7) | (val << 3)
            twst += val
        self.corner_array[7] = (self.corner_array[7] & 0x7) | (((3 - (twst % 3)) % 3) << 3)

    # ----- Edge orientation -----
    def get_flip_index(self):
        idx = 0
        for i in range(11):
            idx = (idx << 1) | (self.edge_array[i] & 1)
        return idx

    def set_flip_from_index(self, idx):
        parity = 0
        for i in range(10, -1, -1):
            val = idx & 1
            idx >>= 1
            parity ^= val
            self.edge_array[i] = (self.edge_array[i] & 0xFE) | val
        self.edge_array[11] = (self.edge_array[11] & 0xFE) | parity

    def get_up_down_slice_index(self):
        return 494 - CubeUtils.get_combination_from_index(self.edge_array, 8, True)

    def set_up_down_slice_from_index(self, idx):
        CubeUtils.set_combination_from_index(self.edge_array, 494 - idx, 8, True)

    # ----- Edge permutation -----
    def get_edge_permutation_index(self):
        return CubeUtils.get_index_from_permutation(self.edge_array, 8, True)

    def set_edge_permutation_from_index(self, idx):
        CubeUtils.set_permutation_from_index(self.edge_array, idx, 8, True)

    # ----- MPerm (middle slice edge permutation mod 24) -----
    def get_middle_permutation_index(self):
        return CubeUtils.get_index_from_permutation(self.edge_array, 12, True) % 24

    def set_middle_permutation_from_index(self, idx):
        CubeUtils.set_permutation_from_index(self.edge_array, idx, 12, True)

    # ----- CComb (combination of corners for certain pruning) -----
    def get_corner_combination_index(self):
        return CubeUtils.get_combination_from_index(self.corner_array, 0, False)

    def set_corner_combination_from_index(self, idx):
        CubeUtils.set_combination_from_index(self.corner_array, idx, 0, False)

    def get_corner_permutation_symmetry(self):
        from coordinate_cube import CoordCube # Local import to avoid circular dependency

        k = CubieCube.edge_symmetry_to_corner_symmetry(CoordCube.get_pruning_table_value_table_value_byte(CubieCube.EDGE_PERMUTATION_RAW_TO_SYMMETRY, self.get_corner_permutation_index())) & 0xF

        if CubieCube.temps is None:
            CubieCube.temps = CubieCube()

        CubieCube.conjugate_corners(self, CubieCube.SYMMETRY_MULTIPLICATION_INVERSE_TABLE[0][k], CubieCube.temps)
        idx = CubieCube.binary_search(CubieCube.EDGE_PERMUTATION_SYMMETRY_TO_RAW, CubieCube.temps.get_corner_permutation_index())
        assert idx >= 0, "Corner permutation coordinate not found in symmetry table"

        return (idx << 4) | k


    def get_edge_permutation_symmetry(self):
        from coordinate_cube import CoordCube # Local import to avoid circular dependency

        raw_coord = self.get_edge_permutation_index()
        k = CoordCube.get_pruning_table_value_table_value_byte(CubieCube.EDGE_PERMUTATION_RAW_TO_SYMMETRY, raw_coord)

        if CubieCube.temps is None:
            CubieCube.temps = CubieCube()

        CubieCube.conjugate_edges(self, CubieCube.SYMMETRY_MULTIPLICATION_INVERSE_TABLE[0][k], CubieCube.temps)
        idx = CubieCube.binary_search(CubieCube.EDGE_PERMUTATION_SYMMETRY_TO_RAW, CubieCube.temps.get_edge_permutation_index())
        assert idx >= 0, "Edge permutation coordinate not found in symmetry table"

        return (idx << 4) | k

    def invert_cubie_cube(self):
        if CubieCube.temps is None:
            CubieCube.temps = CubieCube()

        for edge in range(12):
            idx = self.edge_array[edge] >> 1
            CubieCube.temps.edge_array[idx] = (edge << 1) | (self.edge_array[edge] & 1)

        for corner in range(8):
            idx = self.corner_array[corner] & 0x7
            ori = self.corner_array[corner] >> 3
            ori = (3 - ori) % 3 if ori < 3 else ori
            CubieCube.temps.corner_array[idx] = (corner | (ori << 3))

        self.copy(CubieCube.temps)


    def binary_search(a, x):
            idx = bisect.bisect_left(a, x)
            if idx < len(a) and a[idx] == x:
                return idx
            else:
                return -(idx + 1)
    

    def edge_symmetry_to_corner_symmetry(idx: int) -> int:
        return idx ^ ((CubieCube.SYMMETRY_EDGE_TO_CORNER_MAGIC_NUMBER >> ((idx & 0xF) << 1)) & 3)

    @staticmethod
    def get_inverse_permutation_symmetry(idx: int, sym: int, is_corner: bool) -> int:
        idxi = CubieCube.PERMUTATION_INVERSE_EDGE_SYMMETRY[idx]
        if is_corner:
            idxi = CubieCube.edge_symmetry_to_corner_symmetry(idxi)
        return (idxi & 0xfff0) | CubieCube.SYMMETRY_MULTIPLICATION_TABLE[idxi & 0xf][sym]

    @staticmethod
    def get_skippable_moves_for_symmetry(ssym: int) -> int:
        ret = 0
        i = 1
        ssym >>= 1
        while ssym != 0:
            if ssym & 1 == 1:
                ret |= CubieCube.FIRST_MOVE_SYMMETRIES[i]
            ssym >>= 1
            i += 1
        return ret

    def calculate_self_symmetries(self) -> int:
        c = CubieCube()
        c.copy(self)
        d = CubieCube()
        sym = 0
        for i in range(96):
            CubieCube.conjugate_corners(c, CubieCube.SYMMETRY_MULTIPLICATION_INVERSE_TABLE[0][i % 16], d)
            if d.corner_array == self.corner_array:
                CubieCube.conjugate_edges(c, CubieCube.SYMMETRY_MULTIPLICATION_INVERSE_TABLE[0][i % 16], d)
                if d.edge_array == self.edge_array:
                    sym |= 1 << min(i, 48)
            if i % 16 == 15:
                c.perform_urf_conjugation()
            if i % 48 == 47:
                c.invert_cubie_cube()
        return sym

    @staticmethod
    def multiply_corners(a :"CubieCube", b :"CubieCube", prod :"CubieCube"):
        for corn in range(8):
            oriA = a.corner_array[b.corner_array[corn] & 7] >> 3
            oriB = b.corner_array[corn] >> 3
            ori = oriA + (oriB if oriA < 3 else 6 - oriB)
            ori = (ori % 3) + (0 if (oriA < 3) == (oriB < 3) else 3)
            prod.corner_array[corn] = (a.corner_array[b.corner_array[corn] & 7] & 7) | (ori << 3)

    @staticmethod
    def multiply_edges(a :"CubieCube", b :"CubieCube", prod :"CubieCube"):
        for ed in range(12):
            prod.edge_array[ed] = a.edge_array[b.edge_array[ed] >> 1] ^ (b.edge_array[ed] & 1)

    @staticmethod
    def conjugate_corners(a, idx, b):
        sinv = CubieCube.CubeSym[CubieCube.SYMMETRY_MULTIPLICATION_INVERSE_TABLE[0][idx]]
        s = CubieCube.CubeSym[idx]
        for corn in range(8):
            oriA = sinv.corner_array[a.corner_array[s.corner_array[corn] & 7] & 7] >> 3
            oriB = a.corner_array[s.corner_array[corn] & 7] >> 3
            ori = oriB if oriA < 3 else (3 - oriB) % 3
            final_ori = (oriA + ori) % 3
            b.corner_array[corn] = (sinv.corner_array[a.corner_array[s.corner_array[corn] & 7] & 7] & 7) | (final_ori << 3)

    @staticmethod
    def conjugate_edges(a, idx, b):
        sinv = CubieCube.CubeSym[CubieCube.SYMMETRY_MULTIPLICATION_INVERSE_TABLE[0][idx]]
        s = CubieCube.CubeSym[idx]
        for ed in range(12):
            b.edge_array[ed] = sinv.edge_array[a.edge_array[s.edge_array[ed] >> 1] >> 1] ^ (a.edge_array[s.edge_array[ed] >> 1] & 1) ^ (s.edge_array[ed] & 1)

    def perform_urf_conjugation(self):
        if CubieCube.temps is None:
            CubieCube.temps = CubieCube()

        CubieCube.multiply_corners(CubieCube.URF_CONJUGATE_CUBE_INVERSE, self, CubieCube.temps)
        CubieCube.multiply_corners(CubieCube.temps, CubieCube.URF_CONJUGATE_CUBE, self)
        CubieCube.multiply_edges(CubieCube.URF_CONJUGATE_CUBE_INVERSE, self, CubieCube.temps)
        CubieCube.multiply_edges(CubieCube.temps, CubieCube.URF_CONJUGATE_CUBE, self)


    def verify_facelet_string(self):
        edgeCount = [0] * 12
        cornerCount = [0] * 8
        edgeOri = 0
        cornerOri = 0

        for i in range(12):
            edgeCount[self.edge_array[i] >> 1] += 1
            edgeOri += self.edge_array[i] & 1

        for i in range(8):
            cornerCount[self.corner_array[i] & 7] += 1
            ori = self.corner_array[i] >> 3
            if ori > 2:
                return -2  # invalid orientation
            cornerOri += ori

        if any(x != 1 for x in edgeCount):
            return -1  # duplicate/missing edges
        if any(x != 1 for x in cornerCount):
            return -1  # duplicate/missing corners
        if edgeOri % 2 != 0:
            return -2  # edge orientation parity
        if cornerOri % 3 != 0:
            return -2  # corner orientation parity
        if CubeUtils.get_permutation_parity(CubeUtils.get_index_from_permutation(self.edge_array, 12, True), 12) != CubeUtils.get_permutation_parity(CubeUtils.get_index_from_permutation(self.corner_array, 8, False), 8):
            return -3  # permutation parity mismatch

        return 0  # valid cube

CubieCube.URF_CONJUGATE_CUBE = CubieCube(2531, 1373, 67026819, 1367)
CubieCube.URF_CONJUGATE_CUBE_INVERSE = CubieCube(2089, 1906, 322752913, 2040)