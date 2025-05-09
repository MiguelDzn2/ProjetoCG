"""
Main game class for the rhythm instrument game.
Integrates all modules into a cohesive gameplay experience.
"""

import math
import time
import random
from enum import Enum, auto

# Core framework
from core.base import Base
from core_ext.camera import Camera
from core_ext.mesh import Mesh
from core_ext.renderer import Renderer
from core_ext.scene import Scene
from core.matrix import Matrix

# Project modules
from arrow_manager import ArrowManager
from config import *
from game_phases import GamePhase
from geometry.arrow import Arrow
from geometry.ring import RingGeometry
from material.surface import SurfaceMaterial
import geometry.nightClub as nightclub
from geometry.parametric import ParametricGeometry
import numpy as np

# Custom modules
from modules.animation import AnimationManager
from modules.instrument_loader import InstrumentLoader
from modules.music_system import MusicSystem
from modules.phase_manager import PhaseManager
from modules.ui_manager import UIManager

# Debug helpers
from extras.axes import AxesHelper
from extras.grid import GridHelper
from extras.movement_rig import MovementRig

class Game(Base):
    """
    Main game class that integrates all game modules and manages the game loop.
    """
    
    # Arrow Type Constants
    ARROW_TYPE_UP = 0
    ARROW_TYPE_LEFT = 90
    ARROW_TYPE_DOWN = 180
    ARROW_TYPE_RIGHT = 270
    ARROW_TYPE_NAMES = {
        "up": ARROW_TYPE_UP,
        "left": ARROW_TYPE_LEFT,
        "down": ARROW_TYPE_DOWN,
        "right": ARROW_TYPE_RIGHT
    }
    
    def __init__(self, screen_size=(512, 512), debug_mode=False):
        """Initialize the game with optional debug mode"""
        super().__init__(screen_size=screen_size)
        self.debug_mode = debug_mode
        print(f"\n==== Game initialized with debug_mode = {self.debug_mode} ====\n")
        
        # Initialize game state
        self.current_phase = GamePhase.SELECTION
        self.highlighted_index = 0
        self.processed_arrow_uuids = []
        self.current_waiting_arrow_id = None
        self.arrows = []
        
        # Initialize debug pause state
        self.debug_paused = False
        self.debug_pause_duration = 3.0  # Pause for 3 seconds
        self.debug_pause_timer = 0
        self.debug_pause_arrow = None
        
        # Set up core framework
        self.renderer = Renderer()
        self.scene = Scene()
        self.camera = Camera(aspect_ratio=1280/720)
        
        # Set up camera rig for movement
        self.camera_rig = MovementRig()
        self.camera_rig.add(self.camera)
        self.scene.add(self.camera_rig)
        
        # Initialize UI manager
        self.ui_manager = UIManager(self.scene, self.camera)
        
        # Initialize target ring
        self._setup_target_ring()
        
        # Initialize arrow manager
        self.arrow_manager = ArrowManager(self.scene, self.target_ring, debug_mode=self.debug_mode)
        
        # Load instruments
        self.instrument_loader = InstrumentLoader(self.scene)
        self.object_rigs, self.object_meshes = self.instrument_loader.load_instruments(debug_mode=self.debug_mode)
        
        # Initialize phase manager
        self.phase_manager = PhaseManager(self.scene, self.camera_rig, self.ui_manager)
        self.phase_manager.set_object_rigs(self.object_rigs)
        
        # Initialize active object from phase manager
        self.active_object_rig = self.phase_manager.active_object_rig
        
        # Initialize animation manager
        self.animation_manager = AnimationManager()
        
        # Initialize nightclub elements
        self._setup_nightclub()
        
        # Initialize music system after other components
        self.music_system = MusicSystem(self.arrow_manager)
        self.calculate_arrow_travel_time()
        self.music_system.set_arrow_travel_time(self.arrow_travel_time)
        
        # Initialize camera animation properties
        self.camera_animation_time = 0
        
        # Set up debug visualization if in debug mode
        if self.debug_mode:
            self._setup_debug_visualization()
            
        # Set up the selection phase initially
        self.phase_manager.setup_selection_phase()
        
        # Load and play selection music
        self.music_system.load_selection_music()
        self.music_system.play_selection_music()
    
    def initialize(self):
        """Initialize the game"""
        # Just print instructions - all initialization is already done in __init__
        self._print_instructions()
    
    def _print_instructions(self):
        """Print game instructions to console"""
        print("\nInstruções de Controlo:")
        print("Fase de Seleção:")
        print("- Setas Esquerda/Direita: Selecionar objeto")
        print("- Enter: Confirmar seleção e passar para fase de jogo")
        print("\nFase de Jogo:")
        print("Controlo dos Objectos:")
        print("- UO: Rodar o objecto para a esquerda/direita")
        print("- KL: Inclinar o objecto para cima/para baixo")
        print("- Setas: Interagir com as setas do jogo quando chegam ao anel")
        print("\n")
    
    def _setup_target_ring(self):
        """Set up the target ring for gameplay"""
        # Ring configuration from config.py: RING_INNER_RADIUS, RING_OUTER_RADIUS, RING_SCALE, RING_POSITION
        ring_geometry = RingGeometry(inner_radius=RING_INNER_RADIUS, outer_radius=RING_OUTER_RADIUS, segments=32)
        ring_material = SurfaceMaterial(property_dict={"baseColor": [0, 1, 0], "doubleSide": True})  # Green color
        self.target_ring = Mesh(ring_geometry, ring_material)
        self.target_ring.set_position(RING_POSITION)
        self.target_ring.rotate_x(0)  # Rotated to be vertical
        self.target_ring.scale(RING_SCALE)
        self.scene.add(self.target_ring)
        
        # Add debug visualization for ring if in debug mode
        if self.debug_mode:
            self._add_ring_debug_visualization()
    
    def _setup_nightclub(self):
        """Set up nightclub elements"""
        self.nightClub = nightclub.NightClub(self.scene, "geometry/nightClub.obj", [0, -2.5, 10], 3)
        self.nightClub_rig = self.nightClub.get_rig()
        self.scene.add(self.nightClub_rig)
    
    def _setup_debug_visualization(self):
        """Set up debug visualization elements"""
        # Add axes helper
        axes = AxesHelper(axis_length=2)
        self.scene.add(axes)
        
        # Add grid helper
        grid = GridHelper(
            size=20,
            grid_color=[1, 1, 1],
            center_color=[1, 1, 0]
        )
        grid.rotate_x(-math.pi / 2)
        self.scene.add(grid)
    
    def _add_ring_debug_visualization(self):
        """Add visual indicators for the inner and outer ring boundaries"""
        def circle_function(u, v):
            # v parameter is not used for a simple circle
            x = RING_INNER_RADIUS * np.cos(u * 2 * np.pi)
            y = RING_INNER_RADIUS * np.sin(u * 2 * np.pi)  # Keep in XY plane (same as actual ring)
            z = 0  # Flat in the XY plane
            return [x, y, z]
            
        inner_circle_geometry = ParametricGeometry(0, 1, 32, 0, 1, 1, circle_function)
        inner_circle_material = SurfaceMaterial(
            property_dict={
                "baseColor": [1, 0, 0, 0.7],  # Semi-transparent red
                "wireframe": False,  # Solid fill makes it more visible
                "doubleSide": True  # Visible from both sides
            }
        )
        self.inner_circle_mesh = Mesh(inner_circle_geometry, inner_circle_material)
        
        # Position the inner circle at the same position as the ring
        self.inner_circle_mesh.set_position(RING_POSITION)
        self.inner_circle_mesh.scale(RING_SCALE)  # Apply the same scale as the ring
        
        # Add inner circle to the scene
        self.scene.add(self.inner_circle_mesh)
        
        # Add an explanation text for debug mode
        from extras.text_texture import TextTexture
        from material.texture import TextureMaterial
        from geometry.rectangle import RectangleGeometry
        
        debug_text = TextTexture(
            text="Debug Mode: Red circle shows perfect hit zone | Ring is in XY plane (appears vertical due to camera)",
            system_font_name="Arial",
            font_size=18,
            font_color=(255, 255, 255),  # White text
            background_color=(0, 0, 0, 128),  # Semi-transparent black background
            transparent=True,
            image_width=800,
            image_height=50,
            align_horizontal=0.5,  # Centered
            align_vertical=0.5,    # Vertically centered
            image_border_width=0
        )
        debug_material = TextureMaterial(texture=debug_text, property_dict={"doubleSide": True})
        debug_geometry = RectangleGeometry(width=6, height=0.5)
        self.debug_text_mesh = Mesh(debug_geometry, debug_material)
        self.debug_text_mesh.set_position([0, 2, -3])  # Position at top of screen
        self.camera.add(self.debug_text_mesh)  # Add to camera so it's always visible
    
    def update_camera_animation(self):
        """Update camera position based on animation time"""
        # During the first 0.1 seconds, use initial position without interpolation
        if self.camera_animation_time < 0.1:
            self.camera_rig._matrix = Matrix.make_identity()
            self.camera_rig.set_position(CAMERA_INITIAL_POSITION)
            if CAMERA_INITIAL_ROTATION[0] != 0: self.camera_rig.rotate_x(CAMERA_INITIAL_ROTATION[0])
            if CAMERA_INITIAL_ROTATION[1] != 0: self.camera_rig.rotate_y(CAMERA_INITIAL_ROTATION[1])
            if CAMERA_INITIAL_ROTATION[2] != 0: self.camera_rig.rotate_z(CAMERA_INITIAL_ROTATION[2])
            return
        
        # If animation time is beyond transition time, use final position
        if self.camera_animation_time >= CAMERA_TRANSITION_TIME + 0.1:
            self.camera_rig._matrix = Matrix.make_identity()
            self.camera_rig.set_position(CAMERA_FINAL_POSITION)
            if CAMERA_FINAL_ROTATION[0] != 0: self.camera_rig.rotate_x(CAMERA_FINAL_ROTATION[0])
            if CAMERA_FINAL_ROTATION[1] != 0: self.camera_rig.rotate_y(CAMERA_FINAL_ROTATION[1])
            if CAMERA_FINAL_ROTATION[2] != 0: self.camera_rig.rotate_z(CAMERA_FINAL_ROTATION[2])
            return
        
        # During transition, interpolate between initial and final positions
        t = (self.camera_animation_time - 0.1) / CAMERA_TRANSITION_TIME  # Normalized time (0 to 1)
        
        # Linear interpolation for position and rotation
        new_position = [
            CAMERA_INITIAL_POSITION[0] + (CAMERA_FINAL_POSITION[0] - CAMERA_INITIAL_POSITION[0]) * t,
            CAMERA_INITIAL_POSITION[1] + (CAMERA_FINAL_POSITION[1] - CAMERA_INITIAL_POSITION[1]) * t,
            CAMERA_INITIAL_POSITION[2] + (CAMERA_FINAL_POSITION[2] - CAMERA_INITIAL_POSITION[2]) * t
        ]
        
        new_rotation = [
            CAMERA_INITIAL_ROTATION[0] + (CAMERA_FINAL_ROTATION[0] - CAMERA_INITIAL_ROTATION[0]) * t,
            CAMERA_INITIAL_ROTATION[1] + (CAMERA_FINAL_ROTATION[1] - CAMERA_INITIAL_ROTATION[1]) * t,
            CAMERA_INITIAL_ROTATION[2] + (CAMERA_FINAL_ROTATION[2] - CAMERA_INITIAL_ROTATION[2]) * t
        ]
        
        # Apply new transforms
        self.camera_rig._matrix = Matrix.make_identity()
        self.camera_rig.set_position(new_position)
        
        # Apply rotations
        if new_rotation[0] != 0: self.camera_rig.rotate_x(new_rotation[0])
        if new_rotation[1] != 0: self.camera_rig.rotate_y(new_rotation[1])
        if new_rotation[2] != 0: self.camera_rig.rotate_z(new_rotation[2])
    
    def calculate_arrow_travel_time(self):
        """Calculate how long it takes an arrow to travel from spawn to target ring"""
        if ARROW_START_POSITION is None or RING_POSITION is None or ARROW_UNITS_PER_SECOND is None:
            print("Error: Arrow positioning or speed constants not defined. Cannot calculate travel time.")
            self.arrow_travel_time = -1  # Indicate error
            return -1

        if ARROW_UNITS_PER_SECOND == 0:
            print("Error: ARROW_UNITS_PER_SECOND is zero. Cannot calculate travel time (division by zero).")
            self.arrow_travel_time = float('inf')
            return float('inf')

        arrow_start_x = ARROW_START_POSITION[0]
        ring_x = RING_POSITION[0]
        
        distance = abs(ring_x - arrow_start_x)
        
        self.arrow_travel_time = distance / ARROW_UNITS_PER_SECOND
        
        print(f"Arrow travel time calculated: {self.arrow_travel_time:.2f} seconds (Distance: {distance}, Speed: {ARROW_UNITS_PER_SECOND} units/sec)")
        return self.arrow_travel_time
    
    def create_single_arrow(self, arrow_type_str=None):
        """
        Create a single arrow with specified orientation.
        
        Parameters:
            arrow_type_str: String identifier for arrow type ("up", "down", "left", "right")
            
        Returns:
            Arrow object
        """
        angle = 0  # Default angle
        
        if arrow_type_str:
            arrow_type_str_lower = arrow_type_str.lower()
            if arrow_type_str_lower in self.ARROW_TYPE_NAMES:
                angle = self.ARROW_TYPE_NAMES[arrow_type_str_lower]
            else:
                print(f"Warning: Unknown arrow_type_str '{arrow_type_str}'. Defaulting to UP (0 degrees).")
                angle = self.ARROW_TYPE_UP
        else:
            # If no type specified, choose a random one
            possible_angles = [self.ARROW_TYPE_UP, self.ARROW_TYPE_LEFT, self.ARROW_TYPE_DOWN, self.ARROW_TYPE_RIGHT]
            angle = random.choice(possible_angles)
            print(f"Warning: create_single_arrow called without arrow_type_str. Spawning random arrow (angle: {angle}).")
        
        # Create arrow object
        arrow = Arrow(color=[1.0, 0.0, 0.0], offset=[0, 0, 0], debug_mode=self.debug_mode)
        arrow.add_to_scene(self.scene)
        arrow.rotate(math.radians(angle), 'z')  # Rotate based on the determined angle
        
        # ARROW_START_POSITION is imported from config.py
        arrow.set_position(ARROW_START_POSITION)
        
        # Generate a unique ID for the arrow
        import uuid
        arrow.unique_id = str(uuid.uuid4())
        
        # Add to arrows list
        self.arrows.append(arrow)
        
        return arrow
    
    def check_arrow_ring_collision(self, arrow):
        """
        Check for collision between an arrow and the target ring.
        
        Parameters:
            arrow: The arrow to check for collision
            
        Returns:
            Collision value (0 = no collision, 0.5 = partial, 1 = perfect)
        """
        # If arrow has been marked as ineligible for detection, immediately return 0
        if hasattr(arrow, 'ineligible_for_detection') and arrow.ineligible_for_detection:
            return 0
            
        # If this arrow has already been processed, return its saved collision value
        if hasattr(arrow, 'unique_id') and arrow.unique_id in self.processed_arrow_uuids:
            return arrow.collision_value if hasattr(arrow, 'collision_value') else 0
            
        # Get positions of ring
        ring_pos = self.target_ring.global_position
        
        # Get the inner and outer radius of the ring, adjusted by the scale factor
        inner_radius = RING_INNER_RADIUS * RING_SCALE
        outer_radius = RING_OUTER_RADIUS * RING_SCALE
        
        # Get arrow's bounding rectangle
        min_x, min_z, max_x, max_z = arrow.get_bounding_rect()
        
        # Get arrow position
        arrow_pos = arrow.rig.local_position
        
        # Calculate distance between arrow center and ring center (for a vertical ring in the XZ plane)
        dx = arrow_pos[0] - ring_pos[0]
        dz = arrow_pos[2] - ring_pos[2]
        center_distance = math.sqrt(dx*dx + dz*dz)
        
        # For a vertical ring, we use the corners in the XZ plane
        corner_points = [
            (min_x, min_z),  # Bottom-left
            (max_x, min_z),  # Bottom-right
            (max_x, max_z),  # Top-right
            (min_x, max_z)   # Top-left
        ]
        
        # Calculate distances from each corner of the bounding box to the ring center
        corner_distances = []
        for corner_x, corner_z in corner_points:
            # Use XZ distance for vertical ring
            dist = math.sqrt((corner_x - ring_pos[0])**2 + (corner_z - ring_pos[2])**2)
            corner_distances.append(dist)
        
        # The arrow is considered to have passed the ring if it's center is beyond the ring center
        has_passed_center = arrow_pos[0] > ring_pos[0]
        
        # Check if arrow has passed the ring completely (beyond outer radius)
        has_passed_ring = min_x > ring_pos[0] + outer_radius
        
        # Determine collision status
        # Perfect hit: all corners of the bounding box are inside the inner ring
        all_corners_in_inner = all(dist < inner_radius for dist in corner_distances)
        
        # Partial hit: at least one corner is inside the outer ring
        any_corner_in_outer = any(dist < outer_radius for dist in corner_distances)
        
        # Mark arrow as missed when it passes the center without hitting,
        # but don't trigger the animation immediately
        if has_passed_center:
            # If arrow is marked as scored, it collided at some point
            if hasattr(arrow, 'scored') and arrow.scored:
                # Return the previously determined score
                return arrow.collision_value if hasattr(arrow, 'collision_value') else 0
            else:
                # Just mark the arrow as missed, but don't trigger animation yet
                if not hasattr(arrow, 'marked_as_miss'):
                    print(f"Arrow[{arrow.unique_id}]: Marked as miss")
                    arrow.marked_as_miss = True
                
                # Don't return here - let the arrow continue to be tracked as it leaves the ring
        
        # Calculate potential collision value
        if all_corners_in_inner:
            # Arrow is completely inside the inner ring (full interception)
            if hasattr(arrow, 'potential_collision_value') and arrow.potential_collision_value != 1:
                print(f"Arrow[{arrow.unique_id}]: Now fully inside ring (value: 1.0)")
                # No longer trigger animation automatically when arrow is inside the ring
                # Only trigger animations on successful key presses (below)
            arrow.potential_collision_value = 1
        elif any_corner_in_outer:
            # Arrow is at least partially inside the ring (partial interception)
            if hasattr(arrow, 'potential_collision_value') and arrow.potential_collision_value != 0.5:
                if hasattr(arrow, 'potential_collision_value') and arrow.potential_collision_value == 1:
                    print(f"Arrow[{arrow.unique_id}]: Now touching outer ring (value: 0.5)")
                else:
                    print(f"Arrow[{arrow.unique_id}]: Now partially inside ring (value: 0.5)")
            arrow.potential_collision_value = 0.5
        else:
            # Arrow is completely outside the ring
            # Check if the arrow was previously inside the ring but now outside
            if hasattr(arrow, 'potential_collision_value') and arrow.potential_collision_value > 0:
                print(f"Arrow[{arrow.unique_id}]: Now outside ring (value: 0)")
                
                # Only now stop waiting for keypress when the arrow completely exits the ring
                if hasattr(arrow, 'waiting_for_keypress') and arrow.waiting_for_keypress:
                    arrow.waiting_for_keypress = False
                    print(f"Arrow[{arrow.unique_id}]: Stopped waiting - completely exited ring")
                
                # If the arrow was marked as a miss and now it's completely outside the ring,
                # trigger the falling animation for complete misses
                if (hasattr(arrow, 'marked_as_miss') and arrow.marked_as_miss and 
                   (not hasattr(arrow, 'miss_animation_played') or not arrow.miss_animation_played)):
                    print(f"Arrow[{arrow.unique_id}]: Triggering miss animation after completely exiting ring")
                    self.animation_manager.start_falling_animation(self.active_object_rig, self.highlighted_index, self.object_meshes)
                    arrow.miss_animation_played = True
                    
                    # Mark the arrow as processed
                    if hasattr(arrow, 'unique_id') and arrow.unique_id not in self.processed_arrow_uuids:
                        self.processed_arrow_uuids.append(arrow.unique_id)
                        
            arrow.potential_collision_value = 0
        
        # Check if any arrow key is pressed
        is_arrow_key_pressed = (self.input.is_key_pressed('up') or 
                               self.input.is_key_pressed('down') or 
                               self.input.is_key_pressed('left') or 
                               self.input.is_key_pressed('right'))
        
        # Get the arrow's rotation angle
        arrow_angle = arrow.get_rotation_angle()
        
        # Check if the correct arrow key is pressed based on the arrow's angle
        correct_key_pressed = False
        if arrow_angle == 0 and self.input.is_key_pressed('up'):
            correct_key_pressed = True
        elif arrow_angle == 90 and self.input.is_key_pressed('left'):
            correct_key_pressed = True
        elif arrow_angle == 180 and self.input.is_key_pressed('down'):
            correct_key_pressed = True
        elif arrow_angle == 270 and self.input.is_key_pressed('right'):
            correct_key_pressed = True
        
        # Initialize collision checked flag if it doesn't exist
        if not hasattr(arrow, 'collision_checked'):
            arrow.collision_checked = False
            
        # Only register a collision if all conditions are met
        if (arrow.potential_collision_value > 0 and 
            correct_key_pressed and 
            not arrow.collision_checked and
            not (hasattr(arrow, 'ineligible_for_detection') and arrow.ineligible_for_detection)):
            
            # Debug print collision information
            collision_type = "PERFECT" if arrow.potential_collision_value == 1 else "PARTIAL"
            print(f"COLLISION DETECTED - Arrow[{arrow.unique_id}]: {collision_type} (Value {arrow.potential_collision_value})")
            
            # Mark that collision has been checked while key is pressed
            arrow.collision_checked = True
            # Store the collision value for scoring
            arrow.collision_value = arrow.potential_collision_value
            
            # Add this arrow to the processed list to prevent future changes
            if hasattr(arrow, 'unique_id') and arrow.unique_id not in self.processed_arrow_uuids:
                self.processed_arrow_uuids.append(arrow.unique_id)
                print(f"Arrow[{arrow.unique_id}]: Added to processed arrows list")
            
            # Handle scoring and streak in the UI
            score_value = arrow.collision_value * 100
            if arrow.collision_value == 1.0:
                # Perfect hit - apply multiplier and update streak
                multiplier = self.ui_manager.get_score_multiplier()
                score_value *= multiplier
                self.ui_manager.update_score(score_value, is_perfect=True)
                self.ui_manager.add_arrow_to_streak(arrow.unique_id)
                self.ui_manager.update_collision_text("PERFECT!")
                
                # Trigger random animation only on perfect hit
                self.animation_manager.trigger_random_animation(self.active_object_rig, self.highlighted_index, self.object_meshes)
            else:
                # Partial hit - update score, don't trigger falling animation
                self.ui_manager.update_score(score_value, is_perfect=False)
                self.ui_manager.update_collision_text("HIT!")
                
                # For partial hits, trigger a random animation similar to perfect hits
                self.animation_manager.trigger_random_animation(self.active_object_rig, self.highlighted_index, self.object_meshes)
            
            # Mark arrow as scored
            arrow.scored = True
            
            # Change arrow color based on collision result
            if arrow.collision_value == 1.0:
                arrow.change_color([0.0, 1.0, 0.0])  # Green for perfect hit
            else:
                arrow.change_color([1.0, 1.0, 0.0])  # Yellow for partial hit
            
            # Debug mode: Pause the game to inspect collision    
            if self.debug_mode and not self.debug_paused:
                self.debug_paused = True
                self.debug_pause_timer = 0
                self.debug_pause_arrow = arrow
                pause_message = f"PAUSED: {collision_type} Hit (Press SPACE to resume)"
                self.ui_manager.update_collision_text(pause_message)
                print(f"Game paused for {self.debug_pause_duration} seconds to inspect collision")
                
            return arrow.collision_value
        else:
            # Only print if potential collision exists and arrow is eligible
            if (hasattr(arrow, 'potential_collision_value') and 
                arrow.potential_collision_value > 0 and 
                not (hasattr(arrow, 'ineligible_for_detection') and arrow.ineligible_for_detection)):
                
                # Initialize waiting_for_keypress flag if it doesn't exist
                if not hasattr(arrow, 'waiting_for_keypress'):
                    arrow.waiting_for_keypress = False
                    arrow.last_collision_value = 0
                
                # Handle waiting state changes
                if is_arrow_key_pressed and arrow.collision_checked:
                    if hasattr(arrow, 'waiting_for_keypress') and arrow.waiting_for_keypress:
                        arrow.waiting_for_keypress = False
                        print(f"Arrow[{arrow.unique_id}]: No longer waiting - already checked")
                elif arrow.potential_collision_value > 0 and not correct_key_pressed:
                    # Only log when state changes from not waiting to waiting
                    # or when collision value changes while waiting
                    if not arrow.waiting_for_keypress:
                        arrow.waiting_for_keypress = True
                        position_desc = "fully inside ring" if arrow.potential_collision_value == 1 else "touching outer ring"
                        print(f"Arrow[{arrow.unique_id}]: Started waiting for key press ({position_desc}, value: {arrow.potential_collision_value})")
                        arrow.last_collision_value = arrow.potential_collision_value
                    elif hasattr(arrow, 'last_collision_value') and arrow.last_collision_value != arrow.potential_collision_value:
                        position_desc = "fully inside ring" if arrow.potential_collision_value == 1 else "touching outer ring"
                        print(f"Arrow[{arrow.unique_id}]: Still waiting, now {position_desc} (value: {arrow.potential_collision_value})")
                        arrow.last_collision_value = arrow.potential_collision_value
            
            # No collision registered
            return 0
    
    def handle_arrows(self, delta_time):
        """
        Update all arrows and handle their collisions.
        
        Parameters:
            delta_time: Time elapsed since last frame
        """
        # If we're paused in debug mode, don't update arrows
        if self.debug_mode and self.debug_paused:
            return
        
        # Check if any arrow key is pressed
        is_arrow_key_pressed = (self.input.is_key_pressed('up') or 
                               self.input.is_key_pressed('down') or 
                               self.input.is_key_pressed('left') or 
                               self.input.is_key_pressed('right'))
        
        # Track arrows to remove
        arrows_to_remove = []
        
        # Update all arrows
        for i, arrow in enumerate(self.arrows):
            # Update arrow position
            arrow.update(delta_time)
            
            # Reset collision_checked flag when no arrow keys are pressed
            if not is_arrow_key_pressed and hasattr(arrow, 'collision_checked'):
                arrow.collision_checked = False
            
            # Check if arrow should be removed
            if not arrow.isVisible():
                arrows_to_remove.append(i)
                
                # If this was a missed arrow, reset streak but DON'T trigger the falling animation here
                # since that will now be handled in check_arrow_ring_collision when arrow exits the ring
                if not hasattr(arrow, 'scored') or not arrow.scored:
                    self.ui_manager.update_score(0, is_perfect=False)  # Reset streak
                    self.ui_manager.update_collision_text("MISS!")
        
        # Process all arrows for collision
        for arrow in self.arrows:
            # Skip arrows that have been marked as ineligible for detection
            if hasattr(arrow, 'ineligible_for_detection') and arrow.ineligible_for_detection:
                continue
                
            # Check for collision with ring
            self.check_arrow_ring_collision(arrow)
        
        # Remove arrows that are no longer visible
        for i in sorted(arrows_to_remove, reverse=True):
            if i < len(self.arrows):
                arrow = self.arrows[i]
                # Log if arrow was in waiting state when removed
                if hasattr(arrow, 'waiting_for_keypress') and arrow.waiting_for_keypress:
                    print(f"Arrow[{arrow.unique_id}]: Stopped waiting (removed from scene)")
                # If this was the current waiting arrow, reset the ID
                if hasattr(arrow, 'unique_id') and self.current_waiting_arrow_id == arrow.unique_id:
                    self.current_waiting_arrow_id = None
                    
                print(f"Removing Arrow[{arrow.unique_id}] from scene")
                self.arrows.pop(i)  # Remove from list
                arrow.rig.parent.remove(arrow.rig)  # Remove from scene
    
    def handle_gameplay_input(self):
        """Handle input during gameplay phase"""
        # Update camera animation time
        self.camera_animation_time += self.delta_time
        
        move_amount = MOVE_AMOUNT_MULTIPLIER * self.delta_time
        rotate_amount = ROTATE_AMOUNT_MULTIPLIER * self.delta_time
        
        # Camera controls only available in debug mode
        if self.debug_mode:
            # Camera rotation with I and P keys
            if self.input.is_key_pressed('i'):
                self.camera_rig.rotate_y(rotate_amount)
            if self.input.is_key_pressed('p'):
                self.camera_rig.rotate_y(-rotate_amount)
            
            # Camera position movement with J, K, L keys
            if self.input.is_key_pressed('j'):
                self.camera_rig.translate(-move_amount, 0, 0)  # Move left
            if self.input.is_key_pressed('k'):
                self.camera_rig.translate(0, 0, move_amount)   # Move backward
            if self.input.is_key_pressed('l'):
                self.camera_rig.translate(move_amount, 0, 0)   # Move right
                
            # Allow immediate resume from pause with spacebar
            if self.debug_paused and self.input.is_key_down('space'):
                self.debug_paused = False
                self.debug_pause_arrow = None
                self.ui_manager.update_collision_text(" ")
                print("Debug pause canceled by user")
        
        # Create a general animation state check
        is_animating = self.animation_manager.is_animating()
        
        # Check for U key (falling animation) first - it has priority and will interrupt other animations
        if self.input.is_key_down('u'):
            # Always trigger falling animation immediately, even if another animation is running
            self.animation_manager.start_falling_animation(self.active_object_rig, self.highlighted_index, self.object_meshes)
        # For other animations (Q, W, E, R, T, Y), only start if nothing is currently animating
        elif not is_animating:
            if self.input.is_key_down('q'):
                self.animation_manager.start_rotation_animation(self.active_object_rig, self.highlighted_index, self.object_meshes, 'x', 1)
            elif self.input.is_key_down('e'):
                self.animation_manager.start_rotation_animation(self.active_object_rig, self.highlighted_index, self.object_meshes, 'x', -1)
            elif self.input.is_key_down('w'):
                self.animation_manager.start_rotation_animation(self.active_object_rig, self.highlighted_index, self.object_meshes, 'y', 1)
            elif self.input.is_key_down('r'):
                self.animation_manager.start_rotation_animation(self.active_object_rig, self.highlighted_index, self.object_meshes, 'y', -1)
            elif self.input.is_key_down('t'):
                self.animation_manager.start_jump_animation(self.active_object_rig, [-1, 0, 0])
            elif self.input.is_key_down('y'):
                self.animation_manager.start_jump_animation(self.active_object_rig, [1, 0, 0])

        # Update animations if active
        if self.animation_manager.is_rotating:
            self.animation_manager.update_rotation_animation(self.active_object_rig, self.highlighted_index, self.object_meshes)
        if self.animation_manager.is_jumping:
            self.animation_manager.update_jump_animation(self.active_object_rig)
        if self.animation_manager.is_falling:
            self.animation_manager.update_falling_animation(self.active_object_rig, self.highlighted_index, self.object_meshes)
    
    def update(self):
        """Update game logic (called every frame)"""
        if self.current_phase == GamePhase.SELECTION:
            # Handle input for selection phase
            phase_changed, selected_index = self.phase_manager.handle_selection_input(self.input)
            
            if phase_changed:
                self.current_phase = GamePhase.GAMEPLAY
                self.highlighted_index = selected_index
                # Synchronize active object with PhaseManager
                self.active_object_rig = self.phase_manager.active_object_rig
                
                # Load and play music for the selected instrument
                self.music_system.load_track_for_instrument(selected_index)
                self.music_system.play_music()
                
            # Render scene with current camera
            self.renderer.render(self.scene, self.camera)
            
        elif self.current_phase == GamePhase.GAMEPLAY:
            # Handle input for gameplay phase
            self.handle_gameplay_input()
            
            # Only use automatic camera animation when not in debug mode
            if not self.debug_mode:
                self.update_camera_animation()
            
            # Check for debug pause state
            if self.debug_mode and self.debug_paused:
                self.debug_pause_timer += self.delta_time
                
                # Display pause info
                pause_text = f"GAME PAUSED - Resume in {max(0, self.debug_pause_duration - self.debug_pause_timer):.1f}s"
                self.ui_manager.update_collision_text(pause_text)
                
                # Resume after pause duration or if space is pressed
                if self.debug_pause_timer >= self.debug_pause_duration or self.input.is_key_down('space'):
                    self.debug_paused = False
                    self.debug_pause_arrow = None
                    self.ui_manager.update_collision_text(" ")
                    print("Debug pause ended - game resumed")
            else:
                # Only process game updates if not paused
                if self.music_system.music_playing:
                    # Use callback function to create arrows at the right time
                    self.music_system.update_keyframe_arrows(self.create_single_arrow)
                
                # Continue handling movement and removal of existing arrows
                self.handle_arrows(self.delta_time)
            
            # Render scene with current camera
            self.renderer.render(self.scene, self.camera) 