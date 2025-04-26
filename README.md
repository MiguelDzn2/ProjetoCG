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

*(Instructions on how to install dependencies and run the project would go here. You might need to specify Python version and required libraries.)*

```python
# Example placeholder
pip install -r requirements.txt
python projeto.py
```

## Dependencies

*   Python 3.x
*   *(List other specific libraries like Pyglet, NumPy, PyOpenGL if known)* 