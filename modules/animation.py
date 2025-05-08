"""
Animation module for handling object animations in the game.
Contains implementation for rotation and jump animations.
"""

import math
import time

class AnimationManager:
    """
    Manages animations for game objects including rotations and jumps.
    """
    
    def __init__(self):
        # Rotation animation properties
        self.is_rotating = False
        self.rotation_start_time = 0
        self.rotation_axis = None
        self.rotation_direction = 1
        self.rotation_duration = 0.5  # Duration of rotation animation in seconds
        self.total_rotation_angle = 2 * math.pi  # 360 degrees in radians
        self.original_matrix = None
        self.original_specular_strength = None
        self.original_shininess = None
        
        # Jump animation properties
        self.is_jumping = False
        self.jump_start_time = 0
        self.jump_direction = [0, 0, 0]
        self.jump_duration = 0.5  # Duration of jump animation in seconds
        self.jump_distance = 2.0  # Distance to jump (units)
        self.jump_height = 1.0    # Max height of jump (units)
        self.original_position = [0, 0, 0]  # Store original object position
        self.original_jump_matrix = None
        
        # Falling animation properties
        self.is_falling = False
        self.fall_start_time = 0
        self.fall_duration = 0.5  # Duration of falling animation in seconds
        self.max_fall_angle = math.pi/2  # 90 degrees in radians
        self.original_fall_matrix = None
        
        # Forced animation tracking
        self.next_animation_forced = False
        self.forced_animation = None
        self.last_animation = None
    
    def start_rotation_animation(self, active_object_rig, highlighted_index, object_meshes, axis, direction=1):
        """
        Start a 360° rotation animation around the specified axis.
        
        Parameters:
            active_object_rig: The object rig to animate
            highlighted_index: Index of the active object in object_meshes
            object_meshes: List of all object meshes
            axis (str): 'x', 'y', or 'z' - the axis to rotate around
            direction (int): 1 for clockwise, -1 for counter-clockwise
        """
        if not self.is_rotating:  # Only start if not already rotating
            self.is_rotating = True
            self.rotation_start_time = time.time()
            self.rotation_axis = axis
            self.rotation_direction = direction
            
            # Store original matrix and material properties
            if active_object_rig:
                self.original_matrix = active_object_rig._matrix.copy()
                # Get the correct mesh using the index
                if highlighted_index < len(object_meshes):
                    active_mesh = object_meshes[highlighted_index]
                    material = active_mesh.material 
                    # Store original specular properties and reduce them for animation
                    if hasattr(material, 'uniform_dict') and "specularStrength" in material.uniform_dict:
                        self.original_specular_strength = material.uniform_dict["specularStrength"].data
                        self.original_shininess = material.uniform_dict["shininess"].data
                        material.uniform_dict["specularStrength"].data = 0.1 # Reduce significantly
                        material.uniform_dict["shininess"].data = 10.0      # Reduce shininess
                    else:
                        self.original_specular_strength = None # Flag that we couldn't store/change it
                        self.original_shininess = None
                else:
                    # Handle case where index is out of bounds
                    print("Error: highlighted_index out of bounds for object_meshes")
                    self.original_specular_strength = None
                    self.original_shininess = None
    
    def update_rotation_animation(self, active_object_rig, highlighted_index, object_meshes):
        """
        Update the rotation animation based on elapsed time.
        Completes a 360° rotation and returns to original orientation.
        Uses sine-based easing for smooth acceleration and deceleration.
        
        Parameters:
            active_object_rig: The object rig being animated
            highlighted_index: Index of the active object in object_meshes
            object_meshes: List of all object meshes
        """
        if not active_object_rig:
            self.is_rotating = False
            return
            
        # Calculate elapsed time and progress
        current_time = time.time()
        elapsed_time = current_time - self.rotation_start_time
        
        # Normalize progress to [0, 1] range
        linear_progress = min(1.0, elapsed_time / self.rotation_duration)
        
        # Apply sine-based easing for smooth acceleration and deceleration
        # This transforms linear progress into a smooth curve that starts slow,
        # accelerates in the middle, and slows down at the end
        eased_progress = (1 - math.cos(linear_progress * math.pi)) / 2
        
        # Calculate current rotation angle (full 360°), applying direction and easing
        current_angle = eased_progress * self.total_rotation_angle * self.rotation_direction
        
        # Reset to the original matrix
        active_object_rig._matrix = self.original_matrix.copy()
        
        # Apply the animation rotation on top of the original position
        if self.rotation_axis == 'x':
            active_object_rig.rotate_x(current_angle)
        elif self.rotation_axis == 'y':
            active_object_rig.rotate_y(current_angle)
        elif self.rotation_axis == 'z':
            active_object_rig.rotate_z(current_angle)
            
        # Check if animation is complete
        if linear_progress >= 1.0:
            self.is_rotating = False
            # Reset the matrix to the original
            active_object_rig._matrix = self.original_matrix.copy()
            
            # Reset the material properties if we changed them
            if highlighted_index < len(object_meshes):
                active_mesh = object_meshes[highlighted_index]
                material = active_mesh.material
                if hasattr(material, 'uniform_dict') and self.original_specular_strength is not None:
                    material.uniform_dict["specularStrength"].data = self.original_specular_strength
                    material.uniform_dict["shininess"].data = self.original_shininess

    def start_jump_animation(self, active_object_rig, direction):
        """
        Start a jump animation in the specified direction.
        The object will permanently move to the new position.
        
        Parameters:
            active_object_rig: The object rig to animate
            direction (list): [x, y, z] direction vector for the jump
        """
        if not self.is_jumping and not self.is_rotating and not self.is_falling:  # Only start if no animation is running
            self.is_jumping = True
            self.jump_start_time = time.time()
            self.jump_direction = direction
            
            # Store original position for the animation
            if active_object_rig:
                self.original_position = active_object_rig.local_position.copy()
                # Store original matrix as well for the animation
                self.original_jump_matrix = active_object_rig._matrix.copy()
    
    def update_jump_animation(self, active_object_rig):
        """
        Update the jump animation based on elapsed time.
        Creates a parabolic arc motion to the target position.
        Uses sine-based easing for smooth acceleration.
        
        Parameters:
            active_object_rig: The object rig being animated
        """
        if not active_object_rig:
            self.is_jumping = False
            return
            
        # Calculate elapsed time and progress
        current_time = time.time()
        elapsed_time = current_time - self.jump_start_time
        
        # Normalize progress to [0, 1] range
        linear_progress = min(1.0, elapsed_time / self.jump_duration)
        
        # Apply sine-based easing for smooth acceleration
        eased_progress = (1 - math.cos(linear_progress * math.pi)) / 2
        
        # Calculate horizontal movement (linear from 0 to 1)
        # This moves the object to the target position permanently
        horizontal_factor = eased_progress  # Linear progress from 0 to 1
        
        # Calculate vertical movement (parabolic arc: up then down)
        # sin(t·π) gives a 0 to 1 to 0 pattern over the [0,1] domain
        vertical_factor = math.sin(linear_progress * math.pi)
        
        # Reset to original matrix first to ensure we start from the correct state
        active_object_rig._matrix = self.original_jump_matrix.copy()
        
        # Calculate new position
        new_position = [
            self.original_position[0] + self.jump_direction[0] * self.jump_distance * horizontal_factor,
            self.original_position[1] + self.jump_height * vertical_factor,
            self.original_position[2] + self.jump_direction[2] * self.jump_distance * horizontal_factor
        ]
        
        # Apply the new position
        active_object_rig.set_position(new_position)
        
        # Check if animation is complete
        if linear_progress >= 1.0:
            self.is_jumping = False
            # Keep the final position, no need to reset
            # Just make sure the matrix is preserved
            active_object_rig._matrix = self.original_jump_matrix.copy()
            # Apply the final position
            final_position = [
                self.original_position[0] + self.jump_direction[0] * self.jump_distance,
                self.original_position[1],  # Return to original Y height
                self.original_position[2] + self.jump_direction[2] * self.jump_distance
            ]
            active_object_rig.set_position(final_position)

    def start_falling_animation(self, active_object_rig, highlighted_index, object_meshes):
        """
        Start a falling animation where the object falls on its back and rises again.
        This animation has priority and will interrupt other animations.
        
        Parameters:
            active_object_rig: The object rig to animate
            highlighted_index: Index of the active object in object_meshes
            object_meshes: List of all object meshes
        """
        # Force stop any current animations to start the falling animation immediately
        if self.is_rotating or self.is_jumping:
            print("Interrupting current animation to start falling animation")
            self.is_rotating = False
            self.is_jumping = False
        
        # Only check if falling animation is already running to avoid duplicate starts
        if self.is_falling:
            return
            
        self.is_falling = True
        self.fall_start_time = time.time()
        
        # Store original matrix for the animation
        if active_object_rig:
            self.original_fall_matrix = active_object_rig._matrix.copy()
            
            # Store material properties similar to rotation animation
            if highlighted_index < len(object_meshes):
                active_mesh = object_meshes[highlighted_index]
                material = active_mesh.material 
                if hasattr(material, 'uniform_dict') and "specularStrength" in material.uniform_dict:
                    self.original_specular_strength = material.uniform_dict["specularStrength"].data
                    self.original_shininess = material.uniform_dict["shininess"].data
                    material.uniform_dict["specularStrength"].data = 0.1 # Reduce significantly
                    material.uniform_dict["shininess"].data = 10.0      # Reduce shininess
                else:
                    self.original_specular_strength = None
                    self.original_shininess = None
    
    def update_falling_animation(self, active_object_rig, highlighted_index, object_meshes):
        """
        Update the falling animation based on elapsed time.
        The object falls on its back (X-axis rotation) and then rises back up.
        Uses sine-based easing for smooth movement.
        
        Parameters:
            active_object_rig: The object rig being animated
            highlighted_index: Index of the active object in object_meshes
            object_meshes: List of all object meshes
        """
        if not active_object_rig:
            self.is_falling = False
            return
            
        # Calculate elapsed time and progress
        current_time = time.time()
        elapsed_time = current_time - self.fall_start_time
        
        # Normalize progress to [0, 1] range
        linear_progress = min(1.0, elapsed_time / self.fall_duration)
        
        # Create a parabolic motion pattern
        # For the first half, the object falls backwards
        # For the second half, it rises back up
        if linear_progress <= 0.5:
            # Fall phase (0 to 0.5 -> 0 to max_angle)
            # Normalize to [0, 1] for just this phase
            phase_progress = linear_progress * 2  # 0-0.5 -> 0-1
            
            # Apply easing for smooth acceleration/deceleration
            eased_progress = (1 - math.cos(phase_progress * math.pi)) / 2
            
            # Calculate rotation angle (0 to max_fall_angle)
            current_angle = eased_progress * self.max_fall_angle
            
            # Calculate vertical position offset (lower as it falls)
            # As the object rotates backward, it should move down
            y_offset = -0.5 * eased_progress  # Move down only a bit, enough to touch ground
            
            # Add a small forward movement as it falls (to make it more natural)
            z_offset = 0.3 * eased_progress  # Move forward slightly as it falls
        else:
            # Rise phase (0.5 to 1.0 -> max_angle to 0)
            # Normalize to [0, 1] for just this phase
            phase_progress = (linear_progress - 0.5) * 2  # 0.5-1.0 -> 0-1
            
            # Apply easing for smooth acceleration/deceleration
            eased_progress = (1 - math.cos(phase_progress * math.pi)) / 2
            
            # Calculate rotation angle (max_fall_angle to 0)
            current_angle = self.max_fall_angle * (1 - eased_progress)
            
            # Calculate vertical position offset (rise back up)
            y_offset = -0.5 * (1 - eased_progress)  # Move from -0.5 back to 0
            
            # Return from forward movement
            z_offset = 0.3 * (1 - eased_progress)  # Move backward to original position
        
        # Reset to original matrix
        active_object_rig._matrix = self.original_fall_matrix.copy()
        
        # Get original position
        original_position = active_object_rig.local_position.copy()
        
        # Apply the X-axis rotation to make the object fall backward
        active_object_rig.rotate_x(current_angle)
        
        # Apply position changes to simulate falling to ground with slight forward movement
        new_position = [
            original_position[0],
            original_position[1] + y_offset,  # Lower Y position just enough to touch ground
            original_position[2] + z_offset   # Slight forward movement for realism
        ]
        active_object_rig.set_position(new_position)
        
        # Check if animation is complete
        if linear_progress >= 1.0:
            self.is_falling = False
            # Reset to original position and orientation
            active_object_rig._matrix = self.original_fall_matrix.copy()
            
            # Reset material properties if we changed them
            if highlighted_index < len(object_meshes):
                active_mesh = object_meshes[highlighted_index]
                material = active_mesh.material
                if hasattr(material, 'uniform_dict') and self.original_specular_strength is not None:
                    material.uniform_dict["specularStrength"].data = self.original_specular_strength
                    material.uniform_dict["shininess"].data = self.original_shininess

    def trigger_random_animation(self, active_object_rig, highlighted_index, object_meshes):
        """
        Trigger a random animation from the available ones (Q,W,E,R,T,Y,U).
        
        Animation probabilities:
        - Rotation animations (Q,W,E,R): 20% each (80% total)
        - Jump animations (T,Y): 10% each (20% total)
        - If T is selected, the next one will be Y. If Y is selected, the next one will be T.
        - U animation (falling) is not randomly selected here but triggered only on complete misses.
        
        Parameters:
            active_object_rig: The object rig to animate
            highlighted_index: Index of the active object in object_meshes
            object_meshes: List of all object meshes
        """
        # Don't trigger animations if already animating
        if self.is_rotating or self.is_jumping or self.is_falling:
            return
            
        import random
        
        # Check if we need to enforce a specific animation this time
        if self.next_animation_forced and self.forced_animation:
            selected = self.forced_animation
            print(f"Animation: Enforced {selected.upper()} (alternating from previous jump)")
            
            # Reset forcing - next animation will be random again
            self.next_animation_forced = False
            self.forced_animation = None
        else:
            # Weighted random selection with reduced probability for T and Y
            # Rotations (Q,W,E,R): 20% each (80% total)
            # Jumps (T,Y): 10% each (20% total)
            # Note: U (falling) is not selected randomly but triggered on misses/partial hits
            random_value = random.random()  # 0.0 to 1.0
            
            if random_value < 0.2:
                selected = 'q'      # 0.0-0.2 = 20%
            elif random_value < 0.4:
                selected = 'w'      # 0.2-0.4 = 20%
            elif random_value < 0.6:
                selected = 'e'      # 0.4-0.6 = 20%
            elif random_value < 0.8:
                selected = 'r'      # 0.6-0.8 = 20%
            elif random_value < 0.9:
                selected = 't'      # 0.8-0.9 = 10%
            else:
                selected = 'y'      # 0.9-1.0 = 10%
            
            # If we randomly selected a jump, prepare to enforce alternation next time
            if selected in ['t', 'y']:
                self.next_animation_forced = True
                
                # Set the opposite jump for next time
                if selected == 't':
                    self.forced_animation = 'y'
                    print(f"Animation: Left jump (T) - will enforce Right jump next time")
                else:  # selected == 'y'
                    self.forced_animation = 't'
                    print(f"Animation: Left jump (Y) - will enforce Right jump next time")
            else:
                print(f"Animation: {selected.upper()} rotation")
        
        # Store the last animation
        self.last_animation = selected
        
        # Trigger the selected animation
        if selected == 'q':
            self.start_rotation_animation(active_object_rig, highlighted_index, object_meshes, 'x', 1)  # Positive X rotation
        elif selected == 'e':
            self.start_rotation_animation(active_object_rig, highlighted_index, object_meshes, 'x', -1)  # Negative X rotation
        elif selected == 'w':
            self.start_rotation_animation(active_object_rig, highlighted_index, object_meshes, 'y', 1)  # Positive Y rotation
        elif selected == 'r':
            self.start_rotation_animation(active_object_rig, highlighted_index, object_meshes, 'y', -1)  # Negative Y rotation
        elif selected == 't':
            self.start_jump_animation(active_object_rig, [-1, 0, 0])  # Jump left
        elif selected == 'y':
            self.start_jump_animation(active_object_rig, [1, 0, 0])   # Jump right
        elif selected == 'u':
            self.start_falling_animation(active_object_rig, highlighted_index, object_meshes)  # Fall and get up

    def is_animating(self):
        """Return whether any animation is currently active"""
        return self.is_rotating or self.is_jumping or self.is_falling 