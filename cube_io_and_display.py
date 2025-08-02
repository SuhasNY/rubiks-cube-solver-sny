import random
import struct
from cubie_cube import CubieCube
from coordinate_cube import CoordCube
from solver import Search
from cube_utils import CubeUtils


class InputReader:
    def __init__(self, data: bytes):
        self.buffer = memoryview(data)
        self.offset = 0

    def read_char(self):
        val = struct.unpack('>H', self.buffer[self.offset:self.offset+2])[0]
        self.offset += 2
        return val

    def read_int(self):
        val = struct.unpack('>I', self.buffer[self.offset:self.offset+4])[0]
        self.offset += 4
        return val

    def read_fully(self, arr):
        n = len(arr)
        arr[:] = self.buffer[self.offset:self.offset + n]
        self.offset += n

class OutputWriter:
    def __init__(self, file):
        self.file = file

    def write_char(self, val):
        self.file.write(struct.pack('>H', val))

    def write_int(self, val):
        self.file.write(struct.pack('>I', val))

    def write(self, data):
        self.file.write(data)

class Tools:

    @staticmethod
    def read_char_array(arr, data_input):
        for i in range(len(arr)):
            arr[i] = data_input.read(2).decode('utf-16-be')

    @staticmethod
    def read_int_array(arr, data_input):
        for i in range(len(arr)):
            arr[i] = int.from_bytes(data_input.read(4), byteorder='big')

    @staticmethod
    def read_char_matrix(arr, data_input):
        for i in range(len(arr)):
            Tools.read_char_array(arr[i], data_input)

    @staticmethod
    def read_int_matrix(arr, data_input):
        for i in range(len(arr)):
            Tools.read_int_array(arr[i], data_input)
    
    @staticmethod
    def write_char_array(arr, out):
        for ch in arr:
            out.write_char(ch)

    @staticmethod
    def write_int_array(arr, out):
        for num in arr:
            out.write_int(num)

    @staticmethod
    def write_char_2d_array(arr, out):
        for row in arr:
            Tools.write_char_array(row, out)

    @staticmethod
    def write_int_2d_array(arr, out):
        for row in arr:
            Tools.write_int_array(row, out)
    
    def __init__(self):
        raise TypeError("Tools class should not be instantiated.")
        
    @staticmethod
    def input_sanitizer(scramble_str: str) -> bool:
        if not scramble_str:
            return False
        VALID_MOVES = {
            "U", "D", "L", "R", "F", "B",
            "U'", "D'", "L'", "R'", "F'", "B'",
            "U2", "D2", "L2", "R2", "F2", "B2",
            "U'2", "D'2", "L'2", "R'2", "F'2", "B'2"  # <-- Added moves
        }
        moves = scramble_str.strip().split()
        return all(move in VALID_MOVES for move in moves)

    @staticmethod
    def read_char_array(arr, inp):
        for i in range(len(arr)):
            arr[i] = inp.read_char()

    @staticmethod
    def read_int_array(arr, inp):
        for i in range(len(arr)):
            arr[i] = inp.read_int()

    @staticmethod
    def read_char_2d_array(arr, inp):
        for row in arr:
            Tools.read_char_array(row, inp)

    @staticmethod
    def read_int_2d_array(arr, inp):
        for row in arr:
            Tools.read_int_array(row, inp)

    @staticmethod
    def init_from(file_handle):
        """Initializes all tables from a cached file."""
        from solver import Search
        if Search.inited and CoordCube.initialization_level == 2:
            return
        
        print("Loading tables from cache...")
        CubieCube.initialize_moves()
        CubieCube.initialize_symmetries()

        file_content = file_handle.read()
        inp = InputReader(file_content)

        Tools.read_char_array(CubieCube.FLIP_SYMMETRY_TO_RAW, inp)
        Tools.read_char_array(CubieCube.TWIST_SYMMETRY_TO_RAW, inp)
        Tools.read_char_array(CubieCube.EDGE_PERMUTATION_SYMMETRY_TO_RAW, inp)
        inp.read_fully(CubieCube.FLIP_RAW_TO_SYMMETRY)
        inp.read_fully(CubieCube.TWIST_RAW_TO_SYMMETRY)
        inp.read_fully(CubieCube.EDGE_PERMUTATION_RAW_TO_SYMMETRY)
        Tools.read_char_array(CubieCube.PERMUTATION_TO_COMBINATION_PLUS_PARITY, inp) # Ensures PERMUTATION_TO_COMBINATION_PLUS_PARITY is read
        Tools.read_char_array(CubieCube.PERMUTATION_INVERSE_EDGE_SYMMETRY, inp) # Ensures this is read as a char array

        # CoordCube tables
        Tools.read_char_2d_array(CoordCube.UD_SLICE_MOVE_TABLE, inp)
        Tools.read_char_2d_array(CoordCube.TWIST_MOVE_TABLE, inp)
        Tools.read_char_2d_array(CoordCube.FLIP_MOVE_TABLE, inp)
        Tools.read_char_2d_array(CoordCube.UD_SLICE_CONJUGATION_TABLE, inp)
        Tools.read_int_array(CoordCube.UD_SLICE_TWIST_PRUNING_TABLE, inp)
        Tools.read_int_array(CoordCube.UDSliceFlipPrun, inp)
        Tools.read_char_2d_array(CoordCube.CORNER_PERMUTATION_MOVE_TABLE, inp)
        Tools.read_char_2d_array(CoordCube.EDGE_PERMUTATION_MOVE_TABLE, inp)
        Tools.read_char_2d_array(CoordCube.MIDDLE_PERMUTATION_MOVE_TABLE, inp)
        Tools.read_char_2d_array(CoordCube.MIDDLE_PERMUTATION_CONJUGATION_TABLE, inp)
        Tools.read_char_2d_array(CoordCube.CORNER_COMBINATION_PLUS_PARITY_CONJUGATION_TABLE, inp)
        Tools.read_int_array(CoordCube.MIDDLE_CORNER_PERMUTATION_PRUNING_TABLE, inp)
        Tools.read_int_array(CoordCube.EDGE_PERMUTATION_CORNER_COMBINATION_PRUNING_TABLE, inp)

        if CubeUtils.USE_TWIST_FLIP_PRUNING:
            Tools.read_char_array(CubieCube.FLIP_SYMMETRY_TO_RAW_FLIPPED, inp)
            Tools.read_int_array(CoordCube.TWIST_FLIP_PRUNING_TABLE, inp)

        Search.inited = True
        CoordCube.initialization_level = 2
        print("Loading complete.")


    @staticmethod
    def save_to(file_handle):
        """Generates and saves all tables to a cache file."""
        print("Generating and caching tables...")
        
        Search.init() 
        out = OutputWriter(file_handle)

        # Write CubieCube tables
        Tools.write_char_array(CubieCube.FLIP_SYMMETRY_TO_RAW, out)
        Tools.write_char_array(CubieCube.TWIST_SYMMETRY_TO_RAW, out)
        Tools.write_char_array(CubieCube.EDGE_PERMUTATION_SYMMETRY_TO_RAW, out)
        out.write(CubieCube.FLIP_RAW_TO_SYMMETRY)
        out.write(CubieCube.TWIST_RAW_TO_SYMMETRY)
        out.write(CubieCube.EDGE_PERMUTATION_RAW_TO_SYMMETRY)
        Tools.write_char_array(CubieCube.PERMUTATION_TO_COMBINATION_PLUS_PARITY, out)
        Tools.write_char_array(CubieCube.PERMUTATION_INVERSE_EDGE_SYMMETRY, out)
        
        # Write CoordCube tables
        Tools.write_char_2d_array(CoordCube.UD_SLICE_MOVE_TABLE, out)
        Tools.write_char_2d_array(CoordCube.TWIST_MOVE_TABLE, out)
        Tools.write_char_2d_array(CoordCube.FLIP_MOVE_TABLE, out)
        Tools.write_char_2d_array(CoordCube.UD_SLICE_CONJUGATION_TABLE, out)
        Tools.write_int_array(CoordCube.UD_SLICE_TWIST_PRUNING_TABLE, out)
        Tools.write_int_array(CoordCube.UDSliceFlipPrun, out)
        Tools.write_char_2d_array(CoordCube.CORNER_PERMUTATION_MOVE_TABLE, out)
        Tools.write_char_2d_array(CoordCube.EDGE_PERMUTATION_MOVE_TABLE, out)
        Tools.write_char_2d_array(CoordCube.MIDDLE_PERMUTATION_MOVE_TABLE, out)
        Tools.write_char_2d_array(CoordCube.MIDDLE_PERMUTATION_CONJUGATION_TABLE, out)
        Tools.write_char_2d_array(CoordCube.CORNER_COMBINATION_PLUS_PARITY_CONJUGATION_TABLE, out)
        Tools.write_int_array(CoordCube.MIDDLE_CORNER_PERMUTATION_PRUNING_TABLE, out)
        Tools.write_int_array(CoordCube.EDGE_PERMUTATION_CORNER_COMBINATION_PRUNING_TABLE, out)

        if CubeUtils.USE_TWIST_FLIP_PRUNING:
            Tools.write_char_array(CubieCube.FLIP_SYMMETRY_TO_RAW_FLIPPED, out)
            Tools.write_int_array(CoordCube.TWIST_FLIP_PRUNING_TABLE, out)
        
        print("Tables saved to cache.")

    @staticmethod
    def from_scramble_array(scramble :list[int]):
        c1 = CubieCube()
        c2 = CubieCube()

        for i in range(len(scramble)):
            # Apply move
            CubieCube.multiply_corners(c1, CubieCube.MOVE_CUBE_STATES[scramble[i]], c2)
            CubieCube.multiply_edges(c1, CubieCube.MOVE_CUBE_STATES[scramble[i]], c2)

            # Copy result back to c1
            c1.copy(c2)

        return CubeUtils.cubie_cube_to_facelet_string(c1)


    @staticmethod
    def from_scramble_string(s):
        s = s.replace("'2", "2")

        arr = [0] * len(s)
        j = 0
        axis = -1
        for i in range(len(s)):
            c = s[i]
            if c == 'U':
                axis = 0
            elif c == 'R':
                axis = 3
            elif c == 'F':
                axis = 6
            elif c == 'D':
                axis = 9
            elif c == 'L':
                axis = 12
            elif c == 'B':
                axis = 15
            elif c == ' ':
                if axis != -1:
                    arr[j] = axis
                    j += 1
                axis = -1
            elif c == '2':
                axis += 1
            elif c == '\'':
                axis += 2
            else:
                continue
        if axis != -1:
            arr[j] = axis
            j += 1
        ret = [arr[i] for i in range(j)]
        return Tools.from_scramble_array(ret)
    
    @staticmethod
    def random_scramble_generator(length=20):
        """Generates a random scramble of a given length."""
        moves = ["U", "D", "L", "R", "F", "B"]
        modifiers = ["", "'", "2"]
        
        scramble = []
        last_move_axis = None
        
        for _ in range(length):
            while True:
                # Choose a random move axis (U, D, L, R, F, B)
                move_axis = random.choice(moves)
                # Ensure the new move is not on the same axis as the last one
                if move_axis != last_move_axis:
                    # Also check for opposite faces to avoid redundant sequences (e.g., U D)
                    if not (last_move_axis and moves.index(move_axis) // 2 == moves.index(last_move_axis) // 2):
                        last_move_axis = move_axis
                        break
            
            modifier = random.choice(modifiers)
            scramble.append(move_axis + modifier)
            
        return " ".join(scramble)
    
    @staticmethod
    def print_facelets_2d(facelets):
        """Prints the cube's facelet string in a 2D net format with colors."""
        color_map = {'U': 'W', 'R': 'R', 'F': 'G', 'D': 'Y', 'L': 'O', 'B': 'B'}
        
        colored_facelets = "".join([color_map.get(c, c) for c in facelets])

        U = colored_facelets[0:9]
        R = colored_facelets[9:18]
        F = colored_facelets[18:27]
        D = colored_facelets[27:36]
        L = colored_facelets[36:45]
        B = colored_facelets[45:54]

        print("\nScrambled Cube State:\n")
        
        for i in range(0, 9, 3):
            print(f"      {' '.join(list(U[i:i+3]))}")
            
        print("---------------------")

        for i in range(0, 9, 3):
            l_row = ' '.join(list(L[i:i+3]))
            f_row = ' '.join(list(F[i:i+3]))
            r_row = ' '.join(list(R[i:i+3]))
            b_row = ' '.join(list(B[i:i+3]))
            print(f"{l_row} | {f_row} | {r_row} | {b_row}")
            
        print("---------------------")

        for i in range(0, 9, 3):
            print(f"      {' '.join(list(D[i:i+3]))}")