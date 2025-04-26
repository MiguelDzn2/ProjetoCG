# Analysis of projeto.py

This document provides an analysis of the `projeto.py` script, detailing its features and control mechanisms based on the provided code.

## Overview

The script utilizes a custom graphics library (`core`, `core_ext`, `geometry`, `material`, `extras`) to render a 3D scene. The scene contains:
- A 3D model loaded from an OBJ file (`geometry/agogoFixedUV2.obj`).
- A textured material applied to the model (`images/txt2.jpg`).
- Helper objects: Axes and a Grid for spatial reference.
- A controllable camera.
- A controllable 3D object (the loaded model).

The application runs in a window with a resolution of 800x600 pixels.

## Features

1.  **Initialization (`initialize` method):**
    *   Sets up the `Renderer`, `Scene`, and `Camera`. The camera uses an aspect ratio of 800/600.
    *   Creates a `MovementRig` for the camera (`camera_rig`), sets its initial position to `[0.5, 1, 10]`, and adds it to the scene.
    *   Loads vertex positions and UV coordinates from `geometry/agogoFixedUV2.obj` using `my_obj_reader2`.
    *   Creates an `AgogoGeometry2` object using the loaded data.
    *   Loads a texture from `images/txt2.jpg` and creates a `TextureMaterial`.
    *   Creates a `Mesh` using the geometry and material.
    *   Creates a `MovementRig` for the object (`object_rig`), adds the mesh to it, sets its initial position to `[0, 0, 0]`, and adds it to the scene.
    *   Adds `AxesHelper` and `GridHelper` to the scene for visual reference. The grid is rotated to lie on the XZ plane.
    *   Prints control instructions to the console upon startup.

2.  **Update Loop (`update` method):**
    *   Handles camera movement based on user input via the `camera_rig`.
    *   Handles object movement (translation, rotation, tilt) based on user input via the `object_rig`.
    *   Calculates movement and rotation amounts based on `delta_time` to ensure frame-rate independence.
    *   Renders the scene using the `renderer`, `scene`, and `camera`.

3.  **Execution:**
    *   Instantiates the `Example` class with a screen size of `[800, 600]`.
    *   Calls the `run()` method (inherited from `Base`) to start the application loop.

## Controls

The control scheme allows independent manipulation of the camera and the loaded 3D object:

### Camera Controls

Managed by the `camera_rig` and its internal logic (likely responding to the specified keys):

*   **W:** Move Forward
*   **A:** Move Left
*   **S:** Move Backward
*   **D:** Move Right
*   **R:** Move Up
*   **F:** Move Down
*   **Q:** Turn Left (Yaw)
*   **E:** Turn Right (Yaw)
*   **T:** Look Up (Pitch)
*   **G:** Look Down (Pitch)

### Object Controls

Managed explicitly in the `update` method by checking key presses:

*   **Arrow Left:** Translate Left (negative X)
*   **Arrow Right:** Translate Right (positive X)
*   **Arrow Up:** Translate Forward (negative Z)
*   **Arrow Down:** Translate Backward (positive Z)
*   **U:** Rotate Left (positive Y rotation, yaw)
*   **O:** Rotate Right (negative Y rotation, yaw)
*   **K:** Tilt Up (positive X rotation, pitch)
*   **L:** Tilt Down (negative X rotation, pitch)

Movement speed is scaled by `2 * delta_time`, and rotation speed is scaled by `1 * delta_time`. 