class CubeUtils:
    USE_TWIST_FLIP_PRUNING = False
    USE_COMBINATION_PARITY_PRUNING = USE_TWIST_FLIP_PRUNING
    # Edges
    UR = 0
    UF = 1
    UL = 2
    UB = 3
    DR = 4
    DF = 5
    DL = 6
    DB = 7
    FR = 8
    FL = 9
    BL = 10
    BR = 11

    # Corners
    URF = 0
    UFL = 1
    ULB = 2
    UBR = 3
    DFR = 4
    DLF = 5
    DBL = 6
    DRB = 7

    # Moves
    Ux1 = 0
    Ux2 = 1
    Ux3 = 2
    Rx1 = 3
    Rx2 = 4
    Rx3 = 5
    Fx1 = 6
    Fx2 = 7
    Fx3 = 8
    Dx1 = 9
    Dx2 = 10
    Dx3 = 11
    Lx1 = 12
    Lx2 = 13
    Lx3 = 14
    Bx1 = 15
    Bx2 = 16
    Bx3 = 17

    # Facelets
    U1 = 0
    U2 = 1
    U3 = 2
    U4 = 3
    U5 = 4
    U6 = 5
    U7 = 6
    U8 = 7
    U9 = 8
    R1 = 9
    R2 = 10
    R3 = 11
    R4 = 12
    R5 = 13
    R6 = 14
    R7 = 15
    R8 = 16
    R9 = 17
    F1 = 18
    F2 = 19
    F3 = 20
    F4 = 21
    F5 = 22
    F6 = 23
    F7 = 24
    F8 = 25
    F9 = 26
    D1 = 27
    D2 = 28
    D3 = 29
    D4 = 30
    D5 = 31
    D6 = 32
    D7 = 33
    D8 = 34
    D9 = 35
    L1 = 36
    L2 = 37
    L3 = 38
    L4 = 39
    L5 = 40
    L6 = 41
    L7 = 42
    L8 = 43
    L9 = 44
    B1 = 45
    B2 = 46
    B3 = 47
    B4 = 48
    B5 = 49
    B6 = 50
    B7 = 51
    B8 = 52
    B9 = 53

    # Colors
    U = 0
    R = 1
    F = 2
    D = 3
    L = 4
    B = 5

    CORNER_FACELET_MAP = [[U9, R1, F3], [U7, F1, L3], [U1, L1, B3], [U3, B1, R3],
    [D3, F9, R7], [D1, L9, F7], [D7, B9, L7], [D9, R9, B7] ]

    EDGE_FACELET_MAP = [ [U6, R2], [U8, F2], [U4, L2], [U2, B2], [D6, R8], [D2, F8],
    [D4, L8], [D8, B8], [F6, R4], [F4, L6], [B6, L4], [B4, R6] ]

    COMBINATIONS_TABLE = [[0]*13 for _ in range(13)]

    MOVE_TO_STRING_MAP = [ "U,", "U2,", "U',", "R,", "R2,", "R',", "F,", "F2,", "F',",
    "D,", "D2,", "D',", "L,", "L2,", "L',", "B,", "B2,", "B',"]

    UP_DOWN_TO_STANDARD_MOVE_MAP = [ Ux1, Ux2, Ux3, Rx2, Fx2, Dx1, Dx2, Dx3, Lx2, Bx2,
    Rx1, Rx3, Fx1, Fx3, Lx1, Lx3, Bx1, Bx3 ]

    STANDARD_TO_UP_DOWN_MOVE_MAP = [0] * 18
    CHECK_MOVE_TO_BIT_MAP = [0] * 11

    def facelet_string_to_cubie_cube(f, cc_ret):
        # Invalidate corners and edges
        for i in range(8):
            cc_ret.corner_array[i] = 0
        for i in range(12):
            cc_ret.edge_array[i] = 0

        for i in range(8):
            # Find the orientation: the facelet with U or D color
            ori = 0
            while ori < 3 and f[CubeUtils.CORNER_FACELET_MAP[i][ori]] not in [CubeUtils.U, CubeUtils.D]:
                ori += 1

            col1 = f[CubeUtils.CORNER_FACELET_MAP[i][(ori + 1) % 3]]
            col2 = f[CubeUtils.CORNER_FACELET_MAP[i][(ori + 2) % 3]]

            for j in range(8):
                # Check if colors match CORNER_FACELET_MAP[j] (converted to face colors)
                if (col1 == CubeUtils.CORNER_FACELET_MAP[j][1] // 9 and
                    col2 == CubeUtils.CORNER_FACELET_MAP[j][2] // 9):
                    cc_ret.corner_array[i] = ((ori % 3) << 3) | j
                    break

        for i in range(12):
            for j in range(12):
                if (f[CubeUtils.EDGE_FACELET_MAP[i][0]] == CubeUtils.EDGE_FACELET_MAP[j][0] // 9 and
                    f[CubeUtils.EDGE_FACELET_MAP[i][1]] == CubeUtils.EDGE_FACELET_MAP[j][1] // 9):
                    cc_ret.edge_array[i] = j << 1
                    break
                if (f[CubeUtils.EDGE_FACELET_MAP[i][0]] == CubeUtils.EDGE_FACELET_MAP[j][1] // 9 and
                    f[CubeUtils.EDGE_FACELET_MAP[i][1]] == CubeUtils.EDGE_FACELET_MAP[j][0] // 9):
                    cc_ret.edge_array[i] = (j << 1) | 1
                    break
                
    def cubie_cube_to_facelet_string(cc):
        f = [''] * 54
        ts = ['U', 'R', 'F', 'D', 'L', 'B']
        
        # Initialize facelets to default face letters
        for i in range(54):
            f[i] = ts[i // 9]

        # Set corners
        for c in range(8):
            j = cc.corner_array[c] & 0x7  # corner index
            ori = cc.corner_array[c] >> 3  # orientation
            for n in range(3):
                f[CubeUtils.CORNER_FACELET_MAP[c][(n + ori) % 3]] = ts[CubeUtils.CORNER_FACELET_MAP[j][n] // 9]

        # Set edges
        for e in range(12):
            j = cc.edge_array[e] >> 1  # edge index
            ori = cc.edge_array[e] & 1  # orientation
            for n in range(2):
                f[CubeUtils.EDGE_FACELET_MAP[e][(n + ori) % 2]] = ts[CubeUtils.EDGE_FACELET_MAP[j][n] // 9]

        return ''.join(f)

    def get_permutation_parity(idx, n):
        p = 0
        for i in range(n - 2, -1, -1):
            p ^= idx % (n - i)
            idx //= (n - i)
        return p & 1

    def set_piece_value(val0, val, is_edge):
        return (val << 1 | val0 & 1) if is_edge else (val | val0 & 0xF8)

    def get_piece_value(val0, is_edge):
        return val0 >> 1 if is_edge else val0 & 7

    def set_permutation_from_index(arr, idx, n, is_edge):
        val = 0xFEDCBA9876543210
        extract = 0
        for p in range(2, n + 1):
            extract = (extract << 4) | (idx % p)
            idx //= p
        for i in range(n - 1):
            v = ((extract & 0xF) << 2)
            extract >>= 4
            arr[i] = CubeUtils.set_piece_value(arr[i], (val >> v) & 0xF, is_edge)
            m = (1 << v) - 1
            val = (val & m) | ((val >> 4) & ~m)
        arr[n - 1] = CubeUtils.set_piece_value(arr[n - 1], val & 0xF, is_edge)

    def get_index_from_permutation(arr, n, is_edge):
        idx = 0
        val = 0xFEDCBA9876543210
        for i in range(n - 1):
            v = CubeUtils.get_piece_value(arr[i], is_edge) << 2
            idx = (n - i) * idx + ((val >> v) & 0xF)
            val -= 0x1111111111111110 << v
        return idx
    
    def get_combination_from_index(arr, mask, is_edge):
        end = len(arr) - 1
        idx_c = 0
        r = 4
        for i in range(end, -1, -1):
            perm = CubeUtils.get_piece_value(arr[i], is_edge)
            if (perm & 0xC) == mask:
                idx_c += CubeUtils.COMBINATIONS_TABLE[i][r]
                r -= 1
        return idx_c

    def set_combination_from_index(arr, idx_c, mask, is_edge):
        end = len(arr) - 1
        r = 4
        fill = end
        for i in range(end, -1, -1):
            if r > 0 and idx_c >= CubeUtils.COMBINATIONS_TABLE[i][r]:
                idx_c -= CubeUtils.COMBINATIONS_TABLE[i][r]
                r -= 1
                arr[i] = CubeUtils.set_piece_value(arr[i], r | mask, is_edge)
            else:
                if (fill & 0xc) == mask:
                    fill -= 4
                arr[i] = CubeUtils.set_piece_value(arr[i], fill, is_edge)
                fill -= 1

    # Initialize STANDARD_TO_UP_DOWN_MOVE_MAP using UP_DOWN_TO_STANDARD_MOVE_MAP
    STANDARD_TO_UP_DOWN_MOVE_MAP = [0] * 18
    for i in range(18):
        STANDARD_TO_UP_DOWN_MOVE_MAP[UP_DOWN_TO_STANDARD_MOVE_MAP[i]] = i

    # Compute CHECK_MOVE_TO_BIT_MAP
    CHECK_MOVE_TO_BIT_MAP = [0] * 11
    for i in range(10):
        ix = UP_DOWN_TO_STANDARD_MOVE_MAP[i] // 3
        for j in range(10):
            jx = UP_DOWN_TO_STANDARD_MOVE_MAP[j] // 3
            if (ix == jx) or ((ix % 3 == jx % 3) and (ix >= jx)):
                CHECK_MOVE_TO_BIT_MAP[i] |= 1 << j
    CHECK_MOVE_TO_BIT_MAP[10] = 0

    # Compute COMBINATIONS_TABLE[n][k]
    COMBINATIONS_TABLE = [[0 for _ in range(13)] for _ in range(13)]
    for i in range(13):
        COMBINATIONS_TABLE[i][0] = COMBINATIONS_TABLE[i][i] = 1
        for j in range(1, i):
            COMBINATIONS_TABLE[i][j] = COMBINATIONS_TABLE[i - 1][j - 1] + COMBINATIONS_TABLE[i - 1][j]
