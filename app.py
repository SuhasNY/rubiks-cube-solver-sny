import os
import time
from flask import Flask, render_template, request, jsonify, send_from_directory

# Correct imports for the solver logic
from solver import Search
from cube_io_and_display import Tools

app = Flask(__name__)

# --- Vercel-Safe Solver Initialization ---
# Get the absolute path to the directory where this script is located.
# This ensures file paths work reliably on Vercel's read-only filesystem.
script_dir = os.path.dirname(os.path.abspath(__file__))
CACHE_FILE = os.path.join(script_dir, "cache.bin")

print("--- Initializing Solver ---")
print(f"Attempting to load cache from: {CACHE_FILE}")

# The cache.bin file MUST exist in the repository.
if not os.path.exists(CACHE_FILE):
    # If the file is not found, the deployment is incomplete.
    # This error message will be clear in the Vercel logs.
    print(f"FATAL: cache.bin not found at the specified path: {CACHE_FILE}")
    raise FileNotFoundError(
        "FATAL: cache.bin not found. "
        "Ensure the file is committed to your repository and the path is correct."
    )

try:
    init_start_time = time.time()
    print(f"Loading tables from '{CACHE_FILE}'...")
    with open(CACHE_FILE, 'rb') as f:
        # This line actually loads the solver data.
        Tools.init_from(f)
    init_duration = time.time() - init_start_time
    print(f"--- Initialization Complete ({init_duration:.2f}s) ---")
except Exception as e:
    # If loading fails, log the specific error.
    print(f"FATAL: Failed to load or parse cache.bin. Error: {e}")
    raise

# ---------------------------------------------

# Route to serve the favicon.ico file and prevent 404 errors in logs
@app.route('/favicon.ico')
def favicon():
    # This will gracefully fail if you don't have a static/favicon.ico file,
    # but it prevents a server crash if the file is requested.
    try:
        return send_from_directory(os.path.join(app.root_path, 'static'),
                                   'favicon.ico', mimetype='image/vnd.microsoft.icon')
    except FileNotFoundError:
        return ('', 204) # No Content response

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
    Accepts a JSON object with a "scramble" key.
    Returns a JSON object with the "solution" and "time" taken.
    """
    data = request.get_json()
    if not data or 'scramble' not in data:
        return jsonify({'error': 'Invalid request. Scramble not provided.'}), 400

    scramble_string = data['scramble']
    
    # Define search parameters for the solver
    max_depth = 21
    probe_max = 100000
    probe_min = 0
    verbose = 0

    try:
        # Create a new search instance for each request
        search_solver = Search() 
        
        # Convert the scramble string into a facelet representation of the cube
        facelets = Tools.from_scramble_string(scramble_string)
        
        # Start timing the solution process
        start_time = time.time()
        
        # Call the solver to find the solution
        solution = search_solver.solution(facelets, max_depth, probe_max, probe_min, verbose)
        
        # Calculate the time taken
        solve_duration = time.time() - start_time
        
        # Return the solution and the time taken
        return jsonify({'solution': solution, 'time': solve_duration})

    except Exception as e:
        # Log the error for easier debugging in Vercel
        print(f"Error during solving: {e}")
        return jsonify({'error': f'An error occurred: {str(e)}'}), 500


if __name__ == '__main__':
    app.run(debug=True, use_reloader=False)
