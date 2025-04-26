# Project Phases

This document details the different phases implemented in the Computer Graphics project and their functionality.

## Phase Overview

The project implements a state machine with two distinct phases:
1. **Selection Phase**: Allows the user to select one of four 3D instrument models
2. **Gameplay Phase**: Provides an interactive environment to control the selected instrument

Each phase has its own:
- Camera positioning and orientation
- Object arrangement and highlighting
- Input handling logic
- Visual setup

## Phase Implementation

The phases are implemented using an `Enum` class called `GamePhase` with two states:
```python
class GamePhase(Enum):
    SELECTION = auto()
    GAMEPLAY = auto()
```

The current phase is tracked using the `self.current_phase` variable, which is initialized to `GamePhase.SELECTION`.

## Selection Phase

### Purpose
The Selection Phase presents all four instrument models in a lineup, allowing the user to highlight and select one.

### Visual Setup
- **Camera Position**: High up (`y=50`) and facing backwards to view all objects
- **Objects Arrangement**: Four instruments positioned in a horizontal row with increased spacing
- **Highlighting**: Selected object is visually highlighted by scaling (1.2x)

### Controls
- **Left/Right Arrow Keys**: Navigate between the four instruments
- **Enter Key**: Confirm selection and transition to Gameplay Phase

### Implementation Details
- Function `setup_selection_phase()` configures the scene for this phase
- Function `handle_selection_input()` processes input during this phase
- Function `highlight_selected_object()` provides visual feedback

## Gameplay Phase

### Purpose
The Gameplay Phase allows the user to control the selected instrument model and move it around the scene.

### Visual Setup
- **Camera Position**: Reset to ground level (`y=1`) facing forward
- **Objects Arrangement**: 
  - Selected object positioned at the center (`[0, 0, 0]`)
  - Other objects positioned behind at `z=-5` with different x-coordinates

### Controls
- **Camera Controls**:
  - WASD: Move camera forward/left/backward/right
  - RF: Move camera up/down
  - QE: Turn camera left/right
  - TG: Look up/down
- **Object Controls**:
  - Arrow Keys: Move object forward/left/backward/right
  - UO: Rotate object left/right
  - KL: Tilt object up/down

### Implementation Details
- Function `setup_gameplay_phase()` configures the scene for this phase
- Function `handle_gameplay_input()` processes input during this phase
- Camera movement is handled by the `camera_rig.update()` method
- Object movement is applied directly to the `active_object_rig`

## Phase Transition

The transition from Selection to Gameplay Phase occurs when:
1. User presses Enter key during Selection Phase
2. The highlighted object becomes the active object: `self.active_object_rig = self.object_rigs[self.highlighted_index]`
3. `setup_gameplay_phase()` is called to reconfigure the scene
4. Phase state is updated: `self.current_phase = GamePhase.GAMEPLAY`

There is no implemented transition from Gameplay back to Selection Phase.

## Future Phase Considerations

Potential improvements to the phase system:
1. Add a reset option to return to Selection Phase
2. Implement additional phases (e.g., tutorial, settings)
3. Add transition animations between phases
4. Introduce additional interactions within each phase 