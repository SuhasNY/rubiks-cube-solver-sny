# TestCases.py

import os
import time
from solver import Search
from cube_io_and_display import Tools

def run_tests():
    """
    Initializes the solver, handles caching, and runs a series of predefined 
    scrambles to test correctness and performance.
    """
    CACHE_FILE = "cache.bin"
    print("--- Initializing Solver Tables ---")

    init_start_time = time.time()
    if os.path.exists(CACHE_FILE):
        print(f"Loading tables from '{CACHE_FILE}'...")
        with open(CACHE_FILE, 'rb') as f:
            Tools.init_from(f)
    else:
        print(f"Cache file '{CACHE_FILE}' not found.")
        with open(CACHE_FILE, 'wb') as f:
            Tools.save_to(f)
            
    init_duration = time.time() - init_start_time
    print(f"--- Initialization Complete ({init_duration:.2f}s) ---\n")

    scrambles = [
        # --- 12 Single Moves ---
        "F", "F'", "U", "U'", "R", "R'",
        "B", "B'", "L", "L'", "D", "D'",

        # --- 4 Short Scrambles ---
        "F U R",
        "U' L2 B",
        "R' D B2",
        "F B L R",

        # --- 4 Long Scrambles ---
        "R U R' U' R' F R2 U' R' U' R U R' F'",
        "F U' F2 D' B U R' F' L D' R'",
        "L' U2 L U2 L F' L' F L' U' L U F",
        "D B2 U' R' D B L2 F' D R2 B L U2",
        "F B U R' L B' D D L R L R F F B D' U R U L R' L' B D D B' F L L' F"
    ]
    
    max_depth = 21
    probe_max = 100000
    probe_min = 0
    verbose = 0

    for i, scramble in enumerate(scrambles):
        print(f"--- Test Case {i+1}: Scramble `{scramble}` ---")
        
        facelets = Tools.from_scramble_string(scramble)
        print(f"Facelets: {facelets}")

        solve_start_time = time.time()
        
        search = Search()
        solution = search.solution(facelets, max_depth, probe_max, probe_min, verbose)
        
        solve_duration = time.time() - solve_start_time
        
        print(f"Solution: {solution} (found in {solve_duration:.4f}s)\n")


if __name__ == "__main__":
    print(f"\n\n------------------ To observe time taken to generate tables, please delete `cache.bin` ------------------\n\n")
    run_tests()
    print(f"\n\n------------------ To enter custom scramble through CLI, please run `main.py` ------------------\n\n")