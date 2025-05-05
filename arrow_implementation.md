# Arrow Implementation in the Computer Graphics Project

## Overview

The arrow system in this project is designed to create randomly rotated arrows that appear during the Gameplay Phase. These arrows move across the screen from left to right and are continuously spawned at defined intervals. This document explains the implementation and flow of the arrow system.

## Arrow Class Structure

The Arrow class is defined in `geometry/arrow.py` and is responsible for:

1. Creating the arrow geometry (a combination of a rectangle body and a triangle tip)
2. Managing arrow movement and visibility
3. Handling transformations like position and rotation

### Key Components of the Arrow Class

```python
class Arrow:
    SPEED = 0.01
    RESET_POSITION = 10
    
    def __init__(self, color=[1.0, 0.0, 0.0], offset=[0, 0, 0], size=0.8, angle=0.0, axis='z'):
        # Initialize attributes and create the arrow geometry
        # ...
```

The Arrow class includes several key methods:

- `__init__`: Creates the arrow by combining a rectangle (body) and a triangle (tip)
- `add_to_scene`: Adds the arrow to the scene graph
- `set_position`: Sets the position of the arrow in the 3D space
- `rotate`: Rotates the arrow around a specified axis
- `update`: Updates the arrow's position during gameplay
- `isVisible`: Checks if the arrow is still visible in the scene

## Arrow Spawning System

The arrow spawning system is implemented in the main `Example` class in `projeto.py`. It uses a timer-based approach to spawn new arrows at regular intervals.

### Key Components of the Arrow Spawning System

1. **Initialization**: In the `setup_arrow_spawning` method:
   ```python
   def setup_arrow_spawning(self, interval=2.0):
       """Configura o spawn automático de setas a cada intervalo"""
       self.arrows = []
       self.arrow_spawn_timer = 0
       self.arrow_spawn_interval = interval
   ```

2. **Timer Update**: In the `update_arrow_spawning` method:
   ```python
   def update_arrow_spawning(self, delta_time):
       """Atualiza o timer e cria novas setas quando necessário"""
       self.arrow_spawn_timer += delta_time
       if self.arrow_spawn_timer >= self.arrow_spawn_interval:
           self.arrow_spawn_timer = 0
           self.arrows.append(self.create_single_arrow())
   ```

3. **Arrow Creation**: In the `create_single_arrow` method:
   ```python
   def create_single_arrow(self):
       """Cria uma única seta com orientação aleatória, considerando offset de origem"""
       import random
       possible_angles = [0, 90, 180, 270, 360, 90, 270]
       angle = random.choice(possible_angles)
       
       arrow = Arrow(color=[1.0, 0.0, 0.0], offset=[-0.5, 0, 0])
       arrow.add_to_scene(self.scene)
       arrow.rotate(math.radians(angle), 'z')
       
       # Hardcoded position for arrows
       arrow_x = -3  # Starting X position (left side)
       arrow_y = 2   # Fixed Y position
       arrow_z = 5   # Fixed Z position
       
       # Set arrow at hardcoded position
       arrow.set_position([arrow_x, arrow_y, arrow_z])
       
       return arrow
   ```

## Arrow Movement Path Calculation

When an arrow spawns, it follows a simple linear path from left to right. The path calculation is deliberately straightforward:

1. **Initial Positioning**: When an arrow is created in `create_single_arrow()`, it's positioned at fixed hardcoded coordinates:
   ```python
   # Hardcoded position for arrows
   arrow_x = -3  # Starting X position (left side)
   arrow_y = 2   # Fixed Y position
   arrow_z = 5   # Fixed Z position
   
   # Set arrow at hardcoded position
   arrow.set_position([arrow_x, arrow_y, arrow_z])
   ```

2. **Movement Calculation**: In the Arrow class's `update()` method, the arrow moves along a straight horizontal line by incrementing only its X position:
   ```python
   def update(self):
       current_pos = self.rig.local_position
       new_x = current_pos[0] + self.SPEED * self.direction  # Only X changes
       
       # Y and Z remain constant - only X is updated
       self.rig.set_position([new_x, current_pos[1], current_pos[2]])
   ```

3. **Direction Control**: The arrow's direction is controlled by the `direction` property (initially set to 1 for rightward movement):
   ```python
   # In __init__
   self.direction = 1  # Movement direction (1 for right, -1 for left)
   ```

The path is deliberately simple - a straight line along the X-axis at constant speed with no curve or acceleration. The arrows maintain their fixed Y and Z coordinates from their spawn position, only changing their X position over time.

## Arrow Management Flow

The arrows are managed in a continuous flow during the Gameplay Phase:

1. **Initialization**: When the Gameplay Phase starts, the arrow spawning system is initialized with a default interval of 2 seconds.

2. **Continuous Spawning**: During gameplay, new arrows are spawned at regular intervals based on the configured spawn rate.

3. **Random Rotation**: Each arrow is created with a random rotation angle chosen from predefined angles (0°, 90°, 180°, 270°, 360°).

4. **Movement**: Arrows move from their spawn position (left side of the screen) towards the right at a constant speed defined by the `SPEED` property.

5. **Cleanup**: Arrows that are no longer visible (moved off-screen) are removed from the scene to conserve resources.

## Arrow Update Cycle

The arrow update cycle occurs in the `handle_arrows` method, which:

1. Updates the arrow spawning timer
2. Updates the position of each existing arrow
3. Removes arrows that are no longer visible

```python
def handle_arrows(self, delta_time):
    # Update arrow spawning
    self.update_arrow_spawning(self.delta_time)

    # Update all arrows
    arrows_to_remove = []
    
    for i, arrow in enumerate(self.arrows):
        # Update arrow position
        arrow.update()
        
        # Check if arrow should be removed
        if not arrow.isVisible():
            arrows_to_remove.append(i)

    # Remove marked arrows in reverse order
    for i in sorted(arrows_to_remove, reverse=True):
        if i < len(self.arrows):  # Verificação adicional de segurança
            arrow = self.arrows.pop(i)  # Remove da lista
            arrow.rig.parent.remove(arrow.rig)  # Remove da cena
            del arrow  # Remove da memória
```

## Technical Implementation Details

### Arrow Construction

Each arrow is constructed with:
- A rectangular body (using `RectangleGeometry`)
- A triangular tip (using `PolygonGeometry`)
- Both parts are combined in a `MovementRig` to allow unified transformations

### Movement Logic

Arrows move horizontally from left to right:
```python
def update(self):
    """Atualiza o movimento da seta"""
    current_pos = self.rig.local_position
    new_x = current_pos[0] + self.SPEED * self.direction

    # Check if arrow is out of view
    relative_reset_position = self.RESET_POSITION
    if new_x > current_pos[0] + relative_reset_position:
        self.is_visible = False
    # ...

    # Update position
    self.rig.set_position([new_x, current_pos[1], current_pos[2]])
```

### Hardcoded Position Approach

The current implementation uses fixed hardcoded positions for arrows:
```python
# Hardcoded position for arrows
arrow_x = -3  # Starting X position (left side)
arrow_y = 2   # Fixed Y position
arrow_z = 5   # Fixed Z position
```

This approach ensures arrows always spawn at the same consistent location in the scene, regardless of camera movement or position.

## Future Enhancements

Potential improvements to the arrow system could include:
1. More varied arrow appearances and animations
2. Interactive mechanics where the user needs to hit keys when arrows reach specific positions
3. Dynamic spawning based on gameplay events or music beats
4. Collision detection with the player's instrument
5. Visual effects when arrows are hit or missed 