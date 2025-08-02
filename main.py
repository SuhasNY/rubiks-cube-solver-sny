import os
import time
from solver import Search
from cube_io_and_display import Tools

def main():
    try:
        script_dir = os.path.dirname(os.path.abspath(__file__))
    except NameError:
        script_dir = os.getcwd()
    CACHE_FILE = os.path.join(script_dir, "cache.bin")

    if os.path.exists(CACHE_FILE):
        with open(CACHE_FILE, 'rb') as f:
            Tools.init_from(f)
    else:
        with open(CACHE_FILE, 'wb') as f:
            start_time = time.time()
            Tools.save_to(f)
            end_time = time.time()
            print(f"\nGenerated tables in {end_time - start_time :.4f} seconds\n")

    # Main application loop
    while True:
        print("\n----------------------------------------------------")
        choice = input("Enter 's' to input a scramble sequence,\n'f' to input facelets,\n'r' to generate a random scramble,\n'q' to quit: ").lower()

        if choice == 'q':
            print("\nThank you for using the solver!\n")
            break

        facelets = None
        scramble = None

        if choice == 's':
            while True:
                scramble = input("Enter scramble (e.g., F U' R2 ...): ")
                if Tools.input_sanitizer(scramble):
                    facelets = Tools.from_scramble_string(scramble)
                    break
                else:
                    print("Invalid input. Please use valid moves (U, D, L, R, F, B with ' or 2), separated by spaces.")
        
        elif choice == 'f':
            print("Enter the 54 facelets of the scrambled cube.")
            print("Use single chars: W(hite-U), R(ed-R), G(reen-F), Y(ellow-D), O(range-L), B(lue-B).")
            print("Faces order: Up, Right, Front, Down, Left, Back (9 chars per face).")
            
            while True:
                color_facelets = input("Enter 54 facelet characters: ").upper()
                if len(color_facelets) != 54:
                    print(f"Error: Expected 54 characters, but got {len(color_facelets)}. Please try again.")
                    continue

                # Color conversion logic
                color_map = {'W': 'U', 'R': 'R', 'G': 'F', 'Y': 'D', 'O': 'L', 'B': 'B'}
                try:
                    facelets = "".join([color_map[c] for c in color_facelets])
                    
                    temp_search = Search()
                    verify_facelet_string_code = temp_search.verify_facelet_string(facelets)
                    if verify_facelet_string_code != 0:
                        print(f"Error: The entered cube state is invalid")
                        facelets = None
                    break 
                except KeyError as e:
                    print(f"Error: Invalid character {e} found. Please use only W, R, G, Y, O, B.")

        elif choice == 'r':
            scramble = Tools.random_scramble_generator()
            print(f"\nGenerated Scramble: {scramble}")
            facelets = Tools.from_scramble_string(scramble)
                    
        else:
            print("Invalid choice. Please try again.")
            continue

        if facelets:
            Tools.print_facelets_2d(facelets)

            search = Search()
            
            start_time = time.time()
            soln = search.solution(facelets, 21, 100000, 0, 0)
            end_time = time.time()
            
            print("\nSolution:")
            print(soln)
            print(f"\nTime taken: {end_time - start_time:.4f} seconds")

if __name__ == "__main__":
    main()