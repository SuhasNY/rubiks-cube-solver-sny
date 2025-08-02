import os
import time
from flask import Flask, render_template, request, jsonify
from solver import Search
from cube_io_and_display import Tools
from cubie_cube import CubieCube

app = Flask(__name__)

# --- Server-side Initialization ---

CACHE_FILE = "cache.bin"
print("--- Initializing Solver ---")
init_start_time = time.time()
if os.path.exists(CACHE_FILE):
    print(f"Loading tables from '{CACHE_FILE}'...")
    with open(CACHE_FILE, 'rb') as f:
        Tools.init_from(f)
else:
    print(f"Cache file not found. Generating new tables...")
    with open(CACHE_FILE, 'wb') as f:
        Tools.save_to(f)
init_duration = time.time() - init_start_time
print(f"--- Initialization Complete ({init_duration:.2f}s) ---")
# -----------------------------

@app.route('/')
def index():
    """
    Renders the main HTML page for the user interface.
    """
    return render_template('index.html')

@app.route('/solve', methods=['POST'])
def solve():
    """
    API endpoint to solve a given scramble.
    Accepts a JSON object with a scramble key.
    Returns a JSON object containing the solution and the time taken to find it.
    """
    data = request.get_json()
    if not data or 'scramble' not in data:
        return jsonify({'error': 'Invalid request. Scramble not provided.'}), 400

    scramble_string = data['scramble']

    max_depth = 21
    probe_max = 100000
    probe_min = 0
    verbose = 0

    try:
        search_solver = Search() 
        facelets = Tools.from_scramble_string(scramble_string)
        start_time = time.time()
        solution = search_solver.solution(facelets, max_depth, probe_max, probe_min, verbose)
        solve_duration = time.time() - start_time
        return jsonify({'solution': solution, 'time': solve_duration})

    except Exception as e:
        return jsonify({'error': f'An error occurred: {str(e)}'}), 500

if __name__ == '__main__':
    app.run(debug=True, use_reloader=False)
