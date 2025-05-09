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

The phases are defined in the `game_phases.py` file using an `Enum` class called `GamePhase` with two states:
```python
class GamePhase(Enum):
    SELECTION = auto()
    GAMEPLAY = auto()
```

The phase management is now handled by the `PhaseManager` class in `modules/phase_manager.py`, which:
- Tracks the current phase
- Manages phase transitions
- Sets up phase-specific scene configurations
- Handles phase-specific input

## Selection Phase

### Purpose
The Selection Phase presents all four instrument models in a lineup, allowing the user to highlight and select one.

### Visual Setup
- **Camera Position**: High up (`y=100`) and facing backwards to view all objects
- **Objects Arrangement**: Four instruments positioned in a horizontal row with increased spacing
- **Highlighting**: Selected object is visually highlighted by scaling (1.2x)
- **Title Image**: A game title image is displayed via the UIManager
- **Spotlights**: Each instrument has a colored spotlight above it, with the highlighted instrument's spotlight being brighter

### Controls
- **Left/Right Arrow Keys**: Navigate between the four instruments
- **Enter Key**: Confirm selection and transition to Gameplay Phase

### Implementation Details
- `PhaseManager.setup_selection_phase()`: Configures the scene for this phase
- `PhaseManager.handle_selection_input()`: Processes input during this phase
- `PhaseManager.highlight_selected_object()`: Provides visual feedback
- `UIManager.show_ui_for_selection_phase()`: Shows title and hides score displays

## Gameplay Phase

### Purpose
The Gameplay Phase allows the user to control the selected instrument model and interact with arrows moving toward a target ring.

### Visual Setup
- **Camera Position**: Follows a predefined path/position with smooth transitions
- **Objects Arrangement**:
  - Selected instrument positioned at the center (`[0, 0, 0]`) and controlled by the player
  - Other instruments positioned around the scene for visual interest
- **UI Elements**: 
  - Score display shown via UIManager
  - Streak counter shown via UIManager
  - Collision status display ("HIT", "MISS", "PERFECT") shown via UIManager
- **Target Ring**: A green ring is placed in the scene for gameplay interaction
- **Arrows**: Arrows spawn periodically based on music keyframes and move towards the target ring
- **Nightclub Elements**: Visual elements for nightclub scene are added

### Controls
- **Camera Controls**:
  - Camera movement is automatic with animation
  - Debug mode allows manual camera control
- **Object Controls**:
  - Q, W, E, R: Rotate object along X and Y axes
  - T, Y: Jump left/right
  - Arrow Keys: Interact with gameplay arrows during collisions

### Implementation Details
- `PhaseManager.setup_gameplay_phase()`: Configures the scene for this phase
- `Game.handle_gameplay_input()`: Processes input during gameplay
- `Game.update_camera_animation()`: Handles camera movement animation
- `AnimationManager`: Manages object rotation and jump animations
- `MusicSystem`: Handles music playback and keyframe processing for arrow spawning
- `ArrowManager`: Manages arrow creation, movement, and lifecycle
- `UIManager.show_ui_for_gameplay_phase()`: Sets up score, streak, and collision displays

## Phase Transition

The transition from Selection to Gameplay Phase occurs when:
1. User presses Enter key during Selection Phase
2. `PhaseManager.handle_selection_input()` detects this input and returns phase_changed=True
3. `Game.update()` then:
   - Updates current_phase to GamePhase.GAMEPLAY
   - Uses MusicSystem to load and play music for the selected instrument
4. The PhaseManager handles:
   - Setting the active_object_rig to the selected instrument
   - Calling setup_gameplay_phase() to reconfigure the scene
   - Repositioning and rotating the other instruments
   - Updating the current_phase variable
   - Setting up UI elements through the UIManager

There is no implemented transition from Gameplay back to Selection Phase.

## Collaboration Between Components

The phase system interacts with other components:
1. **UIManager**: Controls which UI elements are visible in each phase
2. **MusicSystem**: Activated during transition to Gameplay phase
3. **AnimationManager**: Controls instrument animations in Gameplay phase
4. **ArrowManager**: Manages arrows in Gameplay phase
5. **InstrumentLoader**: Provides the instrument objects that are positioned by the PhaseManager

## Future Phase Considerations

Potential improvements to the phase system:
1. Add a reset option to return to Selection Phase
2. Implement additional phases (e.g., tutorial, settings)
3. Add transition animations between phases
4. Introduce additional interactions within each phase
5. Implement more complex Nightclub scene elements
6. Refine arrow spawning logic and collision detection
7. Add pause and game over phases 