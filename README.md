# Projeto CG - Computer Graphics Final Project

This project is a computer graphics application developed in Python. It features a two-phase system allowing users to select and interact with 3D instrument models.

## Features

*   **Two-Phase System:**
    *   **Selection Phase:** Choose from four unique 3D instrument models.
    *   **Gameplay Phase:** Control the selected instrument and navigate the 3D scene.
*   **3D Models:** Includes custom instrument models for each team member (Miguel, Ze, Ana, Brandon).
*   **Interactive Controls:**
    *   Camera movement (WASD, RF, QE, TG).
    *   Object movement and rotation (Arrow Keys, UO, KL).
*   **Scene Management:** Utilizes a scene graph for object organization and hierarchy.
*   **Movement Rig:** Provides a structured way to control camera and object movement.

## Project Structure

The project is organized into several key directories:

*   `core/`: Core framework components (Base application, Matrix operations, etc.).
*   `core_ext/`: Extended core functionality (Camera, Renderer, Scene management).
*   `geometry/`: Geometric primitives and custom instrument models (including `.obj` files).
*   `material/`: Material and texture definitions.
*   `extras/`: Additional utilities (Axes/Grid helpers, MovementRig).
*   `images/`: Texture images and visual assets.
*   `projeto.py`: Main application entry point.

## Phases

1.  **Selection Phase:**
    *   View all four instrument models lined up.
    *   Use Left/Right Arrow keys to highlight an instrument.
    *   Press Enter to select the highlighted instrument and proceed to the Gameplay Phase.
2.  **Gameplay Phase:**
    *   The selected instrument is placed at the center.
    *   Control the camera and the selected instrument using dedicated keys.

## Controls

### Selection Phase
*   **Left/Right Arrows:** Navigate between instruments.
*   **Enter:** Confirm selection.

### Gameplay Phase
*   **Camera:**
    *   `WASD`: Move camera forward/left/backward/right.
    *   `RF`: Move camera up/down.
    *   `QE`: Turn camera left/right.
    *   `TG`: Look up/down.
*   **Object:**
    *   **Arrow Keys:** Move object forward/left/backward/right.
    *   `UO`: Rotate object left/right.
    *   `KL`: Tilt object up/down.

## How to Run

Here are a few ways to set up and run the project:

**1. Using Poetry:**

   If you have [Poetry](https://python-poetry.org/) installed:

   ```bash
   # Navigate to the project directory
   cd path/to/ProjetoCG

   # Install dependencies
   poetry install

   # Run the application
   poetry run python projeto.py
   ```

**2. Using an IDE (like PyCharm, VS Code):**

   *   Open the project folder (`ProjetoCG`) in your IDE.
   *   Ensure you have a Python 3.x interpreter configured for the project.
   *   Install the required dependencies. You might need a `requirements.txt` file for this, or use the IDE's package management tools. If using `pip`:

     ```bash
     pip install -r requirements.txt
     ```

   *   Run the `projeto.py` file directly from your IDE.

**3. Using Standard Pip:**

   Assuming you have Python 3.x and pip installed:

   ```bash
   # Navigate to the project directory
   cd path/to/ProjetoCG

   # (Optional but recommended) Create and activate a virtual environment
   python -m venv venv
   # On Windows: .\venv\Scripts\activate
   # On macOS/Linux: source venv/bin/activate

   # Install dependencies (assuming requirements.txt exists)
   pip install -r requirements.txt

   # Run the application
   python projeto.py
   ```

*(Note: You may need to create a `requirements.txt` file listing the necessary packages like Pyglet, NumPy, PyOpenGL if one doesn't already exist.)*

## Dependencies

*   Python 3.x
*   *(List other specific libraries like Pyglet, NumPy, PyOpenGL if known)* 