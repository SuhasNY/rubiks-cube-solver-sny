# Python Rubik's Cube Solver

> **Deployed on Vercel:** [https://rubiks-cube-solver-sny.vercel.app/](https://rubiks-cube-solver-sny.vercel.app/)

This document describes a high-performance Rubik's Cube solver that uses Herbert Kociemba's two-phase algorithm. It is designed to find near-optimal solutions, typically in around **20 moves**, and is accessible via both a command-line interface and a web UI.

---

## Note for the Aero Hack 2025 Evaluators

Kindly follow these guidelines to observe the different components of this submission:

1.  It is suggested to run `main.py` to observe the core functionality of the solver.
2.  Running `TestCases.py` will demonstrate the solver's performance across a variety of pre-defined scrambles.
3.  To observe the time required to generate the pruning and move tables (`cache.bin`), kindly delete said file before running `main.py` or `TestCases.py`.
4.  The solver can be used with its UI by running the Flask app locally or by visiting the provided live webpage URL (deployed on Vercel).

## Two-Phase Algorithm

The solver's logic is based on an _IDA* (Iterative-Deepening A*) search_ built around **Herbert Kociemba's two-phase algorithm**. This method significantly reduces the search space by targeting an intermediate state before proceeding to the final solved state. The solution is obtained in at most **20 moves**.

* **Phase 1**: This phase aims to get the cube into a specific subgroup (G1). In this state, all edge orientations are correct, and all corner pieces are in their correct slice. This phase finds the shortest path to this intermediate G1 state.

* **Phase 2**: A cube in the G1 state can be solved using a limited set of moves (`U`, `D`, `R2`, `L2`, `F2`, `B2`). This phase finds the shortest path from a G1 state to the fully solved state, using only the restricted move set, so as to preserve the solved pieces from phase 1.

The algorithm's efficiency is enhanced by using pre-calculated **pruning tables** and leveraging cube **symmetries**. These tables enable the search to "prune" branches that are guaranteed to not lead to an optimal solution within a certain number of moves.

---
### Project Dependencies

The project relies on the following Python libraries:
1.  flask
2.  bisect
3.  random
4.  struct
5.  os
6.  time

### Solver Cache Generation
On its first run, the application generates a `cache.bin` file, which contains the necessary pruning tables. This process takes 6-8 seconds. On subsequent runs, the application loads this cache file, which allows for a much faster startup. If the `cache.bin` file is deleted, it will be automatically regenerated on the next run.

### Running the Application
There are three runnable files, to focus on different elements of the project:

1.  **Web Interface (Flask App):**
    The Flask server can be started by running the following command:
    ```bash
    python app.py
    ```
    The web interface will then be accessible at `http://127.0.0.1:5000`.

2.  **Interactive Command-Line Interface (CLI):**
    The interactive CLI is launched with:
    ```bash
    python main.py
    ```
    This interface provides a CLI menu for entering custom scrambles, inputting facelets, or solving randomly generated scrambles.

3.  **Run Predefined Test Cases:**
    A series of predefined test cases can be run to demonstrate performance using:
    ```bash
    python TestCases.py
    ```

---

## Codebase Overview

What follows is a brief description of each file and its role in the project:

#### Application Files
* `app.py`: Contains the **Flask web server** that provides the backend for the web UI, handling API requests to the `/solve` endpoint.
* `main.py`: Provides the **interactive command-line interface** (CLI) for using the solver.
* `TestCases.py`: Runs a set of predefined scramble tests, to verify performance as well as demonstrate a range of scrambles and solutions.
* `templates/index.html`: This file is the single-page **frontend application**, which provides a 3D cube visualization and user controls.

#### Core Solver Logic
* `solver.py`: Contains the core implementation of **Kociemba's two-phase search algorithm**.
* `cubie_cube.py`: Defines the cube at the "cubie" level, modeling the position and orientation of each of the 26 pieces.
* `coordinate_cube.py`: Maps the cubie-level representation to **coordinate representations**, which are used as indices for the pruning tables.
* `cube_io_and_display.py`: This module handles **I/O operations**, such as saving and loading the `cache.bin` file and formatting cube states for display.
* `cube_utils.py`: Contains **constants** (like move definitions and facelet names) and helper functions used across the project.

#### Configuration & Data
* `cache.bin`: Binary file that contains the **pre-computed pruning and move tables**. It is generated on the first run to speed up subsequent launches.
* `requirements.txt`: Lists the **Python package dependencies** required to run the project.
* `vercel.json`: The **configuration file** used for deploying the Flask application to the Vercel platform.


