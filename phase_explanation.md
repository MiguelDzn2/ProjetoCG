# Project Phase Management Explanation

This document explains the structure implemented in `projeto.py` to handle distinct application phases: Selection and Gameplay.

## 1. State Management

-   A `GamePhase` enumeration (`Enum`) is defined with two states:
    -   `GamePhase.SELECTION`
    -   `GamePhase.GAMEPLAY`
-   An instance variable `self.current_phase` in the `Example` class tracks the active phase, initialized to `GamePhase.SELECTION` in the `initialize` method.
-   An instance variable `self.highlighted_index` keeps track of which object is currently selected in the `SELECTION` phase (0-indexed).
-   A list `self.object_rigs` stores the `MovementRig` instances for all four objects for easy access.
-   `self.active_object_rig` stores the `MovementRig` of the object currently being controlled (initially the first one, updated upon selection).

## 2. Phase-Specific Setup

Two methods handle the setup for each phase:

### `setup_selection_phase()`

Called during `initialize` and responsible for setting up the initial selection screen:

-   **Camera:**
    -   Resets the camera rig's transformation matrix.
    -   Positions the camera rig at `[0.5, 50, -12]` (high Y-coordinate, looking towards the origin from Z=-12).
    -   Rotates the camera rig 180 degrees around the Y-axis (`math.pi`) to face the objects.
-   **Objects:**
    -   Defines initial positions for the four objects with increased spacing at `[-4.5, 50, 0]`, `[-1.5, 50, 0]`, `[1.5, 50, 0]`, and `[4.5, 50, 0]`. Note the high Y-coordinate (`50`) placing them far above the origin.
    -   Iterates through `self.object_rigs`, resets each rig's transformation matrix, sets its position according to the defined list, and ensures its scale is reset to 1.
-   **Highlighting:** Calls `highlight_selected_object()` to apply the initial visual cue.

### `setup_gameplay_phase()`

Called once when the user confirms their selection in the `SELECTION` phase:

-   **Camera:**
    -   Resets the camera rig's transformation matrix.
    -   Positions the camera rig back near the origin at `[0.5, 1, 10]`, facing forward.
-   **Highlighting:** Calls `remove_highlighting()` to reset the scale of all objects.
-   **Objects:**
    -   Resets the transformation matrix of the `self.active_object_rig` (the selected one) and moves it to the center `[0, 0, 0]`.
    -   Defines positions behind the center (`z = -5`) for the other objects: `[[-3, 0, -5], [-1, 0, -5], [1, 0, -5], [3, 0, -5]]`.
    -   Iterates through the remaining objects in `self.object_rigs`, resets their transformation matrices, and places them in the calculated "behind" positions.

## 3. Conditional Logic in `update()`

The main `update()` method acts as a dispatcher based on the `self.current_phase`:

-   If `self.current_phase == GamePhase.SELECTION`:
    -   Calls `handle_selection_input()` to process input specific to this phase.
-   If `self.current_phase == GamePhase.GAMEPLAY`:
    -   Calls `handle_gameplay_input()` to process input for the main gameplay.
-   Finally, calls `self.renderer.render(self.scene, self.camera)` to draw the current state.

## 4. Input Handling

Input is managed differently depending on the phase, handled by separate methods:

### `handle_selection_input()`

-   Checks for `left` arrow key press (`is_key_down`) to decrease `self.highlighted_index` (with wrap-around).
-   Checks for `right` arrow key press (`is_key_down`) to increase `self.highlighted_index` (with wrap-around).
-   If the index changes, calls `highlight_selected_object()`.
-   Checks for `return` key press (`is_key_down`) to:
    -   Set `self.active_object_rig` to the `self.object_rigs[self.highlighted_index]`.
    -   Call `self.setup_gameplay_phase()` to transition the scene setup.
    -   Change `self.current_phase` to `GamePhase.GAMEPLAY`.

### `handle_gameplay_input()`

-   Calls `self.camera_rig.update(self.input, self.delta_time)` to process standard camera movement controls (WASDRF, QE, TG).
-   Processes object movement controls (Arrow keys, UO, KL) by directly translating/rotating the `self.active_object_rig`.

## 5. Highlighting

-   The `highlight_selected_object()` method provides a visual cue for selection.
    -   It iterates through all `self.object_rigs`.
    -   For each rig, it resets its transformation matrix (preserving position) to ensure scale doesn't accumulate incorrectly.
    -   If the rig's index matches `self.highlighted_index`, it scales the rig up (`rig.scale(1.2)`).
-   The `remove_highlighting()` method resets the scale of all objects back to 1, again by resetting the matrix, reapplying position, and scaling to 1.

## Summary

This phase management system uses a state variable (`self.current_phase`), dedicated setup functions (`setup_selection_phase`, `setup_gameplay_phase`), and conditional input handling (`handle_selection_input`, `handle_gameplay_input`) within the `update` loop to create distinct stages in the application with different layouts and controls. 