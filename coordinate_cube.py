from cube_utils import CubeUtils

class CoordCube:

####################################################### Constants #######################################################

    N_MOVES_PHASE_1 = 18
    N_MOVES_PHASE_2 = 10
    N_SLICE = 495
    N_TWIST = 2187
    N_TWIST_HALF = (N_TWIST + 1) // 2
    N_TWIST_SYM = 324
    N_FLIP = 2048
    N_FLIP_HALF = (N_FLIP + 1) // 2
    N_FLIP_SYM = 336
    N_PERM = 40320
    N_PERM_HALF = (N_PERM + 1) // 2
    N_PERM_SYM = 2768
    N_MPERM = 24

    
    N_COMB = 140 if CubeUtils.USE_COMBINATION_PARITY_PRUNING else 70
    PHASE_2_PARITY_MOVE_FLAG = 0xA5 if CubeUtils.USE_COMBINATION_PARITY_PRUNING else 0

    # Phase 1 Tables
    UD_SLICE_MOVE_TABLE = [[0] * 18 for _ in range(N_SLICE)]
    TWIST_MOVE_TABLE = [[0] * 18 for _ in range(N_TWIST_SYM)]
    FLIP_MOVE_TABLE = [[0] * 18 for _ in range(N_FLIP_SYM)]
    UD_SLICE_CONJUGATION_TABLE = [[0] * 8 for _ in range(N_SLICE)]
    UD_SLICE_TWIST_PRUNING_TABLE = [0] * ((N_SLICE * N_TWIST_SYM) // 8 + 1)
    UDSliceFlipPrun = [0] * ((N_SLICE * N_FLIP_SYM) // 8 + 1)
    TWIST_FLIP_PRUNING_TABLE = [0] * ((N_FLIP * N_TWIST_SYM) // 8 + 1) if CubeUtils.USE_TWIST_FLIP_PRUNING else None

    # Phase 2 Tables
    CORNER_PERMUTATION_MOVE_TABLE = [[0] * 10 for _ in range(N_PERM_SYM)]
    EDGE_PERMUTATION_MOVE_TABLE = [[0] * 10 for _ in range(N_PERM_SYM)]
    MIDDLE_PERMUTATION_MOVE_TABLE = [[0] * 10 for _ in range(N_MPERM)]
    MIDDLE_PERMUTATION_CONJUGATION_TABLE = [[0] * 16 for _ in range(N_MPERM)]
    CORNER_COMBINATION_PLUS_PARITY_MOVE_TABLE = None
    CORNER_COMBINATION_PLUS_PARITY_CONJUGATION_TABLE = [[0] * 16 for _ in range(N_COMB)]
    MIDDLE_CORNER_PERMUTATION_PRUNING_TABLE = [0] * ((N_MPERM * N_PERM_SYM) // 8 + 1)
    EDGE_PERMUTATION_CORNER_COMBINATION_PRUNING_TABLE = [0] * ((N_COMB * N_PERM_SYM) // 8 + 1)
    
    initialization_level = 0

####################################################### Pruning table access functions #######################################################

    @staticmethod
    def set_pruning_table_value(table, index, value):
        shift = (index & 7) << 2
        table[index >> 3] = (table[index >> 3] & ~(0xF << shift)) | (value << shift)
    
    @staticmethod
    def get_pruning_table_value(table, index):
        shift = (index & 7) << 2
        return (table[index >> 3] >> shift) & 0xF


    @staticmethod
    def set_pruning_table_value_table_value_byte(table: bytearray, index: int, value: int):
        shift = (index & 1) << 2
        # First, clear the 4 bits at the target location to zero
        table[index >> 1] &= ~(0xF << shift)
        # Then, set the new value in that cleared location
        table[index >> 1] |= (value << shift)

    @staticmethod
    def get_pruning_table_value_table_value_byte(table: bytearray, index: int) -> int:
        shift = (index & 1) << 2
        return (table[index >> 1] >> shift) & 0xF

####################################################### Initializations #######################################################

    def __init__(self):
        self.twist = 0
        self.twist_symmetry = 0
        self.flip = 0
        self.flip_symmetry = 0
        self.slice = 0
        self.prun = 0
        self.twist_conjugate= 0
        self.flip_conjugate= 0

    @classmethod
    def init(cls):
        from cubie_cube import CubieCube
        if cls.initialization_level == 2:
            return

        if cls.initialization_level == 0:
            # Move and conjugation tables
            CubieCube.initialize_permutatioin_symmetry_to_raw()
            cls.initialize_corner_permutation_move_table()
            cls.initialize_edge_permutation_move_table()
            cls.initialize_middle_permutation_move_and_conjugation_tables()
            cls.initialize_corner_combination_plus_parity_move_and_conjugation_tables()

            CubieCube.initialize_flip_symmetry_to_raw()
            CubieCube.initialize_twist_symmetry_to_raw()
            cls.initialize_flip_move_table()
            cls.initialize_twist_move_table()
            cls.initialize_ud_slice_move_and_conjugation_tables()

        # Pruning tables
        if cls.initialize_pruning_tables(cls.initialization_level == 0):
            cls.initialization_level = 2
        else:
            cls.initialization_level = 1

    @classmethod
    def initialize_pruning_tables(cls, is_first):
        from solver import Search
        inited_prun = True
        inited_prun = (inited_prun or is_first) and cls.initialize_middle_corner_permutation_pruning_table()
        inited_prun = (inited_prun or is_first) and cls.init_perm_comb_p_prun()
        inited_prun = (inited_prun or is_first) and cls.initialize_slice_twist_pruning_table()
        inited_prun = (inited_prun or is_first) and cls.initialize_slice_flip_pruning_table()
        if CubeUtils.USE_TWIST_FLIP_PRUNING:
            inited_prun = (inited_prun or is_first) and cls.initialize_twist_flip_pruning_table()
        return inited_prun
        
    @classmethod
    def initialize_raw_to_symmetry_pruning_table(cls, prun_table, raw_move, raw_conj, sym_move, sym_state, prun_flag):
        from cubie_cube import CubieCube
        
        SYM_SHIFT = prun_flag & 0xf
        SYM_E2C_MAGIC = CubieCube.SYMMETRY_EDGE_TO_CORNER_MAGIC_NUMBER if ((prun_flag >> 4) & 1) == 1 else 0
        IS_PHASE2 = ((prun_flag >> 5) & 1) == 1
        
        N_RAW = len(raw_conj)
        N_SYM = len(sym_move)
        N_SIZE = N_RAW * N_SYM
        N_MOVES_PHASE_1 = 10 if IS_PHASE2 else 18
        
        depth = 0
        done = 1
        
        for i in range((N_SIZE + 7) // 8):
            prun_table[i] = 0xFFFFFFFF
        
        cls.set_pruning_table_value(prun_table, 0, 0)
        
        while done < N_SIZE:
            for i in range(N_SIZE):
                if cls.get_pruning_table_value(prun_table, i) == depth:
                    raw = i % N_RAW
                    sym = i // N_RAW

                    for m in range(N_MOVES_PHASE_1):
                        sym_x = sym_move[sym][m]
                        raw_x = raw_conj[raw_move[raw][m]][sym_x & ((1 << SYM_SHIFT) - 1)]
                        sym_x >>= SYM_SHIFT
                        
                        idx2 = sym_x * N_RAW + raw_x
                        if cls.get_pruning_table_value(prun_table, idx2) == 15:
                            cls.set_pruning_table_value(prun_table, idx2, depth + 1)
                            done += 1
                            
                            sym_state_val = sym_state[sym_x]
                            if sym_state_val != 0:
                                for j in range(1, 16):
                                    if (sym_state_val >> j & 1) == 1:
                                        idxx = sym_x * N_RAW + raw_conj[raw_x][j ^ (SYM_E2C_MAGIC >> (j << 1) & 3)]
                                        if cls.get_pruning_table_value(prun_table, idxx) == 15:
                                            cls.set_pruning_table_value(prun_table, idxx, depth + 1)
                                            done += 1
            depth += 1
        return True

    @classmethod
    def initialize_twist_flip_pruning_table(cls):
        return True

    @classmethod
    def initialize_slice_twist_pruning_table(cls):
        from cubie_cube import CubieCube
        return cls.initialize_raw_to_symmetry_pruning_table(
            cls.UD_SLICE_TWIST_PRUNING_TABLE,
            cls.UD_SLICE_MOVE_TABLE, cls.UD_SLICE_CONJUGATION_TABLE,
            cls.TWIST_MOVE_TABLE, CubieCube.SYMMETRY_STATE_TWIST, 0x69603
        )

    @classmethod
    def initialize_slice_flip_pruning_table(cls):
        from cubie_cube import CubieCube
        return cls.initialize_raw_to_symmetry_pruning_table(
            cls.UDSliceFlipPrun,
            cls.UD_SLICE_MOVE_TABLE, cls.UD_SLICE_CONJUGATION_TABLE,
            cls.FLIP_MOVE_TABLE, CubieCube.SYMMETRY_STATE_FLIP, 0x69603
        )

    @classmethod
    def initialize_middle_corner_permutation_pruning_table(cls):
        from cubie_cube import CubieCube
        return cls.initialize_raw_to_symmetry_pruning_table(
            cls.MIDDLE_CORNER_PERMUTATION_PRUNING_TABLE,
            cls.MIDDLE_PERMUTATION_MOVE_TABLE, cls.MIDDLE_PERMUTATION_CONJUGATION_TABLE,
            cls.CORNER_PERMUTATION_MOVE_TABLE, CubieCube.SYMMETRY_STATE_PERMUTATION, 0x8ea34
        )

    @classmethod
    def init_perm_comb_p_prun(cls):
        from cubie_cube import CubieCube
        return cls.initialize_raw_to_symmetry_pruning_table(
            cls.EDGE_PERMUTATION_CORNER_COMBINATION_PRUNING_TABLE,
            cls.CORNER_COMBINATION_PLUS_PARITY_MOVE_TABLE, cls.CORNER_COMBINATION_PLUS_PARITY_CONJUGATION_TABLE,
            cls.EDGE_PERMUTATION_MOVE_TABLE, CubieCube.SYMMETRY_STATE_PERMUTATION, 0x7d824
        )

    @classmethod
    def initialize_ud_slice_move_and_conjugation_tables(cls):
        from cubie_cube import CubieCube
        c = CubieCube()
        d = CubieCube()
        for i in range(cls.N_SLICE):
            c.set_up_down_slice_from_index(i)
            for j in range(0, cls.N_MOVES_PHASE_1, 3):
                CubieCube.multiply_edges(c, CubieCube.MOVE_CUBE_STATES[j], d)
                cls.UD_SLICE_MOVE_TABLE[i][j] = d.get_up_down_slice_index()
            for j in range(0, 16, 2):
                CubieCube.conjugate_edges(c, CubieCube.SYMMETRY_MULTIPLICATION_INVERSE_TABLE[0][j], d)
                cls.UD_SLICE_CONJUGATION_TABLE[i][j >> 1] = d.get_up_down_slice_index()
        for i in range(cls.N_SLICE):
            for j in range(0, cls.N_MOVES_PHASE_1, 3):
                udslice = cls.UD_SLICE_MOVE_TABLE[i][j]
                for k in range(1, 3):
                    udslice = cls.UD_SLICE_MOVE_TABLE[udslice][j]
                    cls.UD_SLICE_MOVE_TABLE[i][j + k] = udslice

    @classmethod
    def initialize_flip_move_table(cls):
        from cubie_cube import CubieCube
        c = CubieCube()
        d = CubieCube()
        for i in range(cls.N_FLIP_SYM):
            c.set_flip_from_index(CubieCube.FLIP_SYMMETRY_TO_RAW[i])
            for j in range(cls.N_MOVES_PHASE_1):
                CubieCube.multiply_edges(c, CubieCube.MOVE_CUBE_STATES[j], d)
                cls.FLIP_MOVE_TABLE[i][j] = d.get_flip_symmetry()

    @classmethod
    def initialize_twist_move_table(cls):
        from cubie_cube import CubieCube
        c = CubieCube()
        d = CubieCube()
        for i in range(cls.N_TWIST_SYM):
            c.set_twist_from_index(CubieCube.TWIST_SYMMETRY_TO_RAW[i])
            for j in range(cls.N_MOVES_PHASE_1):
                CubieCube.multiply_corners(c, CubieCube.MOVE_CUBE_STATES[j], d)
                cls.TWIST_MOVE_TABLE[i][j] = d.get_twist_symmetry()

    @classmethod
    def initialize_corner_permutation_move_table(cls):
        from cubie_cube import CubieCube
        c = CubieCube()
        d = CubieCube()
        for i in range(cls.N_PERM_SYM):
            c.set_corner_permutation_from_index(CubieCube.EDGE_PERMUTATION_SYMMETRY_TO_RAW[i])
            for j in range(cls.N_MOVES_PHASE_2):
                CubieCube.multiply_corners(c, CubieCube.MOVE_CUBE_STATES[CubeUtils.UP_DOWN_TO_STANDARD_MOVE_MAP[j]], d)
                cls.CORNER_PERMUTATION_MOVE_TABLE[i][j] = d.get_corner_permutation_symmetry()

    @classmethod
    def initialize_edge_permutation_move_table(cls):
        from cubie_cube import CubieCube
        c = CubieCube()
        d = CubieCube()
        for i in range(cls.N_PERM_SYM):
            c.set_edge_permutation_from_index(CubieCube.EDGE_PERMUTATION_SYMMETRY_TO_RAW[i])
            for j in range(cls.N_MOVES_PHASE_2):
                CubieCube.multiply_edges(c, CubieCube.MOVE_CUBE_STATES[CubeUtils.UP_DOWN_TO_STANDARD_MOVE_MAP[j]], d)
                cls.EDGE_PERMUTATION_MOVE_TABLE[i][j] = d.get_edge_permutation_symmetry()

    @classmethod
    def initialize_middle_permutation_move_and_conjugation_tables(cls):
        from cubie_cube import CubieCube
        c = CubieCube()
        d = CubieCube()
        for i in range(cls.N_MPERM):
            c.set_middle_permutation_from_index(i)
            for j in range(cls.N_MOVES_PHASE_2):
                CubieCube.multiply_edges(c, CubieCube.MOVE_CUBE_STATES[CubeUtils.UP_DOWN_TO_STANDARD_MOVE_MAP[j]], d)
                cls.MIDDLE_PERMUTATION_MOVE_TABLE[i][j] = d.get_middle_permutation_index()
            for j in range(16):
                CubieCube.conjugate_edges(c, CubieCube.SYMMETRY_MULTIPLICATION_INVERSE_TABLE[0][j], d)
                cls.MIDDLE_PERMUTATION_CONJUGATION_TABLE[i][j] = d.get_middle_permutation_index()

    @classmethod
    def initialize_corner_combination_plus_parity_move_and_conjugation_tables(cls):
        from cubie_cube import CubieCube
        c = CubieCube()
        d = CubieCube()
        cls.CORNER_COMBINATION_PLUS_PARITY_MOVE_TABLE = [[0] * cls.N_MOVES_PHASE_2 for _ in range(cls.N_COMB)]
        for i in range(cls.N_COMB):
            c.set_corner_combination_from_index(i % 70)
            for j in range(cls.N_MOVES_PHASE_2):
                CubieCube.multiply_corners(c, CubieCube.MOVE_CUBE_STATES[CubeUtils.UP_DOWN_TO_STANDARD_MOVE_MAP[j]], d)
                parity = (cls.PHASE_2_PARITY_MOVE_FLAG >> j & 1) ^ (i // 70)
                cls.CORNER_COMBINATION_PLUS_PARITY_MOVE_TABLE[i][j] = d.get_corner_combination_index() + 70 * parity
            for j in range(16):
                CubieCube.conjugate_corners(c, CubieCube.SYMMETRY_MULTIPLICATION_INVERSE_TABLE[0][j], d)
                cls.CORNER_COMBINATION_PLUS_PARITY_CONJUGATION_TABLE[i][j] = d.get_corner_combination_index() + 70 * (i // 70)
                
    # ###################################### END: Initialization Logic #################################################
    

    def set_coordinates_with_pruning(self, cc, depth: int) -> bool:
        from cubie_cube import CubieCube
        from cube_utils import CubeUtils
        from solver import Search

        twist_sym = cc.get_twist_symmetry()
        flip_sym = cc.get_flip_symmetry()
        self.twist_symmetry = twist_sym & 7
        self.twist = twist_sym >> 3

        self.prun = self.get_pruning_table_value(
            self.TWIST_FLIP_PRUNING_TABLE, (self.twist << 11) | CubieCube.FLIP_SYMMETRY_TO_RAW_FLIPPED[flip_sym ^ self.twist_symmetry]
        ) if CubeUtils.USE_TWIST_FLIP_PRUNING else 0

        if self.prun > depth:
            return False

        self.flip_symmetry = flip_sym & 7
        self.flip = flip_sym >> 3

        self.slice = cc.get_up_down_slice_index()

        prun1 = self.get_pruning_table_value(
            self.UD_SLICE_TWIST_PRUNING_TABLE,
            self.twist * self.N_SLICE + self.UD_SLICE_CONJUGATION_TABLE[self.slice][self.twist_symmetry]
        )
        prun2 = self.get_pruning_table_value(
            self.UDSliceFlipPrun,
            self.flip * self.N_SLICE + self.UD_SLICE_CONJUGATION_TABLE[self.slice][self.flip_symmetry]
        )
        self.prun = max(self.prun, prun1, prun2)

        if self.prun > depth:
            return False

        if Search.USE_CONJUGATE_PRUNING:
            pc = CubieCube()
            CubieCube.conjugate_corners(cc, 1, pc)
            CubieCube.conjugate_edges(cc, 1, pc)
            
            self.twist_conjugate= pc.get_twist_symmetry()
            self.flip_conjugate= pc.get_flip_symmetry()
            
            prun3 = self.get_pruning_table_value(
                self.TWIST_FLIP_PRUNING_TABLE,
                ((self.twist_conjugate>> 3) << 11) | CubieCube.FLIP_SYMMETRY_TO_RAW_FLIPPED[self.flip_conjugate^ (self.twist_conjugate& 7)]
            )
            self.prun = max(self.prun, prun3)

        return self.prun <= depth

    def move_and_get_pruning_table_value_value(self, cc, m, is_phase1):
        from cubie_cube import CubieCube
        self.slice = self.UD_SLICE_MOVE_TABLE[cc.slice][m]
        flip = self.FLIP_MOVE_TABLE[cc.flip][CubieCube.SYMMETRY_8_MOVE_TABLE[(m << 3) | cc.flip_symmetry]]
        self.flip_symmetry = (flip & 7) ^ cc.flip_symmetry
        self.flip = flip >> 3
        twist = self.TWIST_MOVE_TABLE[cc.twist][CubieCube.SYMMETRY_8_MOVE_TABLE[(m << 3) | cc.twist_symmetry]]
        self.twist_symmetry = (twist & 7) ^ cc.twist_symmetry
        self.twist = twist >> 3
        p1 = self.get_pruning_table_value(self.UD_SLICE_TWIST_PRUNING_TABLE, self.twist * self.N_SLICE + self.UD_SLICE_CONJUGATION_TABLE[self.slice][self.twist_symmetry])
        p2 = self.get_pruning_table_value(self.UDSliceFlipPrun, self.flip * self.N_SLICE + self.UD_SLICE_CONJUGATION_TABLE[self.slice][self.flip_symmetry])
        if CubeUtils.USE_TWIST_FLIP_PRUNING:
            p3 = self.get_pruning_table_value(self.TWIST_FLIP_PRUNING_TABLE, (self.twist << 11) | CubieCube.FLIP_SYMMETRY_TO_RAW_FLIPPED[(self.flip << 3) | (self.flip_symmetry ^ self.twist_symmetry)])
        else:
            p3 = 0
        self.prun = max(p1, p2, p3)
        return self.prun

    def conjugate_move_and_get_pruning_table_value_value(self, cc, m):
        from cubie_cube import CubieCube
        m = CubieCube.SYMMETRY_MOVE_TABLE[3][m]
        flip_conjugate= self.FLIP_MOVE_TABLE[cc.flip_conjugate>> 3][CubieCube.SYMMETRY_8_MOVE_TABLE[(m << 3) | (cc.flip_conjugate& 7)]] ^ (cc.flip_conjugate& 7)
        twist_conjugate= self.TWIST_MOVE_TABLE[cc.twist_conjugate>> 3][CubieCube.SYMMETRY_8_MOVE_TABLE[(m << 3) | (cc.twist_conjugate& 7)]] ^ (cc.twist_conjugate& 7)
        return self.get_pruning_table_value(self.TWIST_FLIP_PRUNING_TABLE, ((twist_conjugate>> 3) << 11) | CubieCube.FLIP_SYMMETRY_TO_RAW_FLIPPED[flip_conjugate^ (twist_conjugate& 7)])