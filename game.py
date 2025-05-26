"""
Main game class for the rhythm instrument game.
Integrates all modules into a cohesive gameplay experience.
"""

import math
import time
import random
import os
import numpy as np
from datetime import datetime
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
from config import (
    ARROW_START_POSITION, ARROW_UNITS_PER_SECOND, ARROW_SPAWN_INTERVAL,
    CAMERA_INITIAL_POSITION, CAMERA_INITIAL_ROTATION, CAMERA_FINAL_POSITION, CAMERA_FINAL_ROTATION, CAMERA_TRANSITION_TIME,
    CAMERA_WAYPOINTS,
    RING_POSITION, RING_INNER_RADIUS, RING_OUTER_RADIUS, RING_SCALE,
    NIGHTCLUB_OBJECT_PATH, NIGHTCLUB_POSITION, NIGHTCLUB_SCALE_FACTOR,
    MOVE_AMOUNT_MULTIPLIER, ROTATE_AMOUNT_MULTIPLIER,
    SCREEN_SIZE, ARROW_RING_PIVOT_POSITION, ARROW_RING_PIVOT_ROTATION,
    ARROW_COLOR, ARROW_TYPE_UP, ARROW_TYPE_LEFT, ARROW_TYPE_DOWN, ARROW_TYPE_RIGHT, ARROW_TYPE_NAMES
)
from game_phases import GamePhase
from geometry.arrow import Arrow
from geometry.ring import RingGeometry
from material.surface import SurfaceMaterial
import geometry.nightClub as nightclub
from geometry.parametric import ParametricGeometry

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
    
    # Arrow Type Constants are now in config.py
    # ARROW_TYPE_UP = 0
    # ARROW_TYPE_LEFT = 90
    # ARROW_TYPE_DOWN = 180
    # ARROW_TYPE_RIGHT = 270
    # ARROW_TYPE_NAMES = {
    #     "up": ARROW_TYPE_UP,
    #     "left": ARROW_TYPE_LEFT,
    #     "down": ARROW_TYPE_DOWN,
    #     "right": ARROW_TYPE_RIGHT
    # }
    
    def __init__(self, screen_size=(512, 512), debug_mode=False, fullscreen=False, fullscreen_resolution=None):
        """
        Initialize the Game class.
        
        Parameters:
            screen_size: The size of the screen (width, height)
            debug_mode: Whether to run in debug mode
            fullscreen: Whether to run in fullscreen mode
            fullscreen_resolution: Specific resolution for fullscreen (None for native)
        """
        super().__init__(screen_size, fullscreen, fullscreen_resolution)
        
        # Store screen dimensions (use actual screen size in case of fullscreen)
        actual_size = self.actual_screen_size
        self.screen_width = actual_size[0]
        self.screen_height = actual_size[1]
        
        # Debug mode toggle
        self.debug_mode = debug_mode
        self.debug_camera_active = False
        self.debug_camera = None
        self.debug_paused = False
        self.debug_pause_timer = 0
        self.debug_pause_arrow = None
        self.debug_pause_duration = 2.0  # seconds to pause in debug mode
        
        # Add a message timer for empty miss message
        self.empty_miss_message_timer = 0
        self.empty_miss_message_duration = 0.5  # 1/2 second duration for empty miss message
        self.empty_miss_message_active = False
        
        # Camera animation state
        self.camera_animation_angle = 0
        
        # Initialize game state
        self.current_phase = GamePhase.SELECTION
        self.highlighted_index = 0
        self.processed_arrow_uuids = []
        self.current_waiting_arrow_id = None
        self.arrows = []
        self.gameplay_key_press_consumed_by_hit_this_frame = False
        
        # Flag to control arrow/ring visibility
        self.arrow_ring_visible = False
        
        # Set up core framework
        self.renderer = Renderer()
        self.scene = Scene()
        self.camera = Camera(aspect_ratio=self.screen_width/self.screen_height)
        
        # Set up camera rig for movement
        self.camera_rig = MovementRig()
        self.camera_rig.add(self.camera)
        self.scene.add(self.camera_rig)
        
        # Set up debug camera (positioned to view main camera and pivot)
        if debug_mode:
            self._setup_debug_camera()
        
        # Initialize UI manager
        self.ui_manager = UIManager(self.scene, self.camera)
        
        # Create the arrow-ring pivot (but don't make visible yet)
        self._setup_arrow_ring_pivot()
        
        # Calculate initial arrow travel time
        self.calculate_arrow_travel_time()

        # Setup target ring (invisible until gameplay phase)
        self._setup_target_ring()
        
        # Initialize visual indicators for debug camera view
        if debug_mode:
            self._setup_debug_visual_indicators()
        
        # Arrow Manager - needs the pivot
        self.arrow_manager = ArrowManager(
            scene=self.scene, 
            target_ring=self.target_ring, 
            arrow_ring_pivot=self.arrow_ring_pivot,  # Pass the pivot
            debug_mode=self.debug_mode
        )
        
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
        
        # Initialize music system after other components, passing self for travel time calculations
        self.music_system = MusicSystem(self.arrow_manager, self)
        self.music_system.set_arrow_travel_time(self.arrow_travel_time)
        
        # Initialize camera animation properties
        self.camera_animation_time = 0
        self.active_waypoint_index = -1
        self.waypoint_transition_start_time = 0
        self.waypoint_transition_duration = CAMERA_TRANSITION_TIME  # Initial transition uses config value
        self.start_position = list(CAMERA_FINAL_POSITION)
        self.start_rotation = list(CAMERA_FINAL_ROTATION)
        self.target_position = None
        self.target_rotation = None
        self.target_waypoint = None
        
        # Log the number of camera waypoints found
        print(f"Loaded camera waypoints for {len(CAMERA_WAYPOINTS)} instruments")
        for instrument, waypoints in CAMERA_WAYPOINTS.items():
            print(f"  - {instrument}: {len(waypoints)} waypoints")
        
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
        
    def toggle_fullscreen_mode(self):
        """Toggle fullscreen mode and update camera aspect ratio"""
        new_size = self.toggle_fullscreen()
        
        # Update stored screen dimensions
        self.screen_width = new_size[0]
        self.screen_height = new_size[1]
        
        # Update camera aspect ratio
        self.camera.aspect_ratio = self.screen_width / self.screen_height
        
        print(f"Screen mode changed to: {self.screen_width}x{self.screen_height}")
        return new_size
    
    def _print_instructions(self):
        """Print game instructions to console"""
        print("\nInstruções de Controlo:")
        print("Geral:")
        print("- F11: Alternar entre modo janela e ecrã completo")
        print("\nFase de Seleção:")
        print("- Setas Esquerda/Direita: Selecionar objeto")
        print("- Enter: Confirmar seleção e passar para fase de jogo")
        print("\nFase de Jogo:")
        print("Controlo dos Objectos:")
        print("- UO: Rodar o objecto para a esquerda/direita")
        print("- KL: Inclinar o objecto para cima/para baixo")
        print("- Setas: Interagir com as setas do jogo quando chegam ao anel")
        print("\n")
    
    def _setup_arrow_ring_pivot(self):
        """Creates and configures the pivot node for the arrow and ring system."""
        self.arrow_ring_pivot = MovementRig()
        self.arrow_ring_pivot.set_position(list(ARROW_RING_PIVOT_POSITION))
        self.arrow_ring_pivot.rotate_x(math.radians(ARROW_RING_PIVOT_ROTATION[0]))
        self.arrow_ring_pivot.rotate_y(math.radians(ARROW_RING_PIVOT_ROTATION[1]))
        self.arrow_ring_pivot.rotate_z(math.radians(ARROW_RING_PIVOT_ROTATION[2]))
        
        # Initialize but don't add to camera yet - will be added after selection phase
        # self.camera.add(self.arrow_ring_pivot)

    def _setup_target_ring(self):
        """Set up the target ring for gameplay as a child of the pivot."""
        ring_geometry = RingGeometry(inner_radius=RING_INNER_RADIUS, outer_radius=RING_OUTER_RADIUS, segments=32)
        ring_material = SurfaceMaterial(property_dict={"baseColor": [0, 1, 0], "doubleSide": True})  # Green color
        self.target_ring = Mesh(ring_geometry, ring_material)
        # Position the ring relative to pivot (rather than in world space)
        self.target_ring.set_position(list(RING_POSITION))
        self.target_ring.rotate_x(0)  # No rotation needed initially - already on XY plane
        self.target_ring.scale(RING_SCALE)
        
        # Add ring to pivot (but pivot is not in scene yet, so ring will not be visible)
        self.arrow_ring_pivot.add(self.target_ring)
        
        # Add debug visualization for ring if in debug mode
        if self.debug_mode:
            self._add_ring_debug_visualization()
    
    def _setup_nightclub(self):
        """Set up nightclub elements"""
        self.nightClub = nightclub.NightClub(
            self.scene, 
            NIGHTCLUB_OBJECT_PATH, 
            NIGHTCLUB_POSITION, 
            NIGHTCLUB_SCALE_FACTOR
        )
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
        
        # Initialize the debug info display
        self.update_camera_debug_text()
    
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
    
    def _setup_debug_camera(self):
        """Set up a secondary camera for debug purposes"""
        # Create debug camera
        self.debug_camera = Camera(aspect_ratio=1280/720)
        
        # Create debug camera rig
        self.debug_camera_rig = MovementRig()
        self.debug_camera_rig.add(self.debug_camera)
        self.scene.add(self.debug_camera_rig)
        
        # Position debug camera to see the main camera and pivot
        # Position is up and back from the scene
        self.debug_camera_rig.set_position([0, 15, 20])
        self.debug_camera_rig.rotate_x(math.radians(-30))  # Look down at the scene

    def _setup_debug_visual_indicators(self):
        """Add visual indicators for the main camera and pivot point"""
        # Create a visual indicator for the camera
        from geometry.rectangle import RectangleGeometry
        from material.surface import SurfaceMaterial
        
        # Camera visual indicator (blue box)
        camera_geo = RectangleGeometry(width=1, height=1)
        camera_mat = SurfaceMaterial(property_dict={"baseColor": [0, 0, 1], "doubleSide": True, "wireframe": True})
        self.camera_indicator = Mesh(camera_geo, camera_mat)
        
        # Position at the main camera's position
        self.camera_rig.add(self.camera_indicator)
        
        # Pivot visual indicator (red box)
        pivot_geo = RectangleGeometry(width=0.5, height=0.5)
        pivot_mat = SurfaceMaterial(property_dict={"baseColor": [1, 0, 0], "doubleSide": True, "wireframe": True})
        self.pivot_indicator = Mesh(pivot_geo, pivot_mat)
        
        # Add to arrow_ring_pivot to show its position
        self.arrow_ring_pivot.add(self.pivot_indicator)
        
        # Add text labels
        from extras.text_texture import TextTexture
        from material.texture import TextureMaterial
        
        # Camera label
        camera_label_texture = TextTexture(
            text="Main Camera",
            system_font_name="Arial",
            font_size=12,
            font_color=(0, 0, 255),
            background_color=(0, 0, 0, 128),
            transparent=True,
            image_width=200,
            image_height=30
        )
        camera_label_mat = TextureMaterial(texture=camera_label_texture, property_dict={"doubleSide": True})
        camera_label_geo = RectangleGeometry(width=2, height=0.3)
        self.camera_label = Mesh(camera_label_geo, camera_label_mat)
        self.camera_label.set_position([0, 1, 0])  # Position above the camera indicator
        self.camera_indicator.add(self.camera_label)
        
        # Pivot label
        pivot_label_texture = TextTexture(
            text="Arrow-Ring Pivot",
            system_font_name="Arial",
            font_size=12,
            font_color=(255, 0, 0),
            background_color=(0, 0, 0, 128),
            transparent=True,
            image_width=200,
            image_height=30
        )
        pivot_label_mat = TextureMaterial(texture=pivot_label_texture, property_dict={"doubleSide": True})
        pivot_label_geo = RectangleGeometry(width=2, height=0.3)
        self.pivot_label = Mesh(pivot_label_geo, pivot_label_mat)
        self.pivot_label.set_position([0, 1, 0])  # Position above the pivot indicator
        self.pivot_indicator.add(self.pivot_label)

    def _make_arrow_ring_visible(self):
        """Makes the arrow-ring pivot and its children visible by adding to camera"""
        if not self.arrow_ring_visible:
            self.camera.add(self.arrow_ring_pivot)
            self.arrow_ring_visible = True
            print("Arrow and ring system now visible")

    def update_camera_animation(self):
        """Update camera position based on animation time and waypoints"""
        # Get current music time from music system
        current_music_time = self.music_system.get_music_time()
        
        # Get the selected instrument name
        instrument_names = ["miguel", "ze", "ana", "brandon"]
        if hasattr(self, 'highlighted_index') and self.highlighted_index < len(instrument_names):
            selected_instrument = instrument_names[self.highlighted_index]
        else:
            selected_instrument = "miguel"  # Default fallback
            
        # Get the appropriate waypoints for the selected instrument
        if selected_instrument in CAMERA_WAYPOINTS:
            waypoints = CAMERA_WAYPOINTS[selected_instrument]
        else:
            # If no waypoints for this instrument, do nothing
            print(f"No camera waypoints defined for {selected_instrument}")
            return
            
        # If no waypoints, do nothing
        if len(waypoints) == 0:
            return
            
        # Find the current target waypoint based on music time
        current_target_index = 0
        for i, waypoint in enumerate(waypoints):
            if current_music_time <= waypoint["time"]:
                current_target_index = i
                break
            if i == len(waypoints) - 1:  # Last waypoint
                current_target_index = i
        
        # If we're at or past the last waypoint, stay at the final position
        if current_target_index == len(waypoints) - 1 and current_music_time >= waypoints[-1]["time"]:
            final_waypoint = waypoints[-1]
            self.camera_rig._matrix = Matrix.make_identity()
            self.camera_rig.set_position(final_waypoint["position"])
            self.camera_rig.rotate_x(math.radians(final_waypoint["rotation"][0]))
            self.camera_rig.rotate_y(math.radians(final_waypoint["rotation"][1]))
            self.camera_rig.rotate_z(math.radians(final_waypoint["rotation"][2]))
            return
            
        # Get the current target waypoint and the previous waypoint
        target_waypoint = waypoints[current_target_index]
        if current_target_index == 0:
            # For the first waypoint, use its own position as the start
            start_waypoint = {
                "time": 0,
                "position": target_waypoint["position"],
                "rotation": target_waypoint["rotation"]
            }
        else:
            start_waypoint = waypoints[current_target_index - 1]
        
        # Calculate interpolation factor (0 to 1)
        start_time = start_waypoint["time"]
        end_time = target_waypoint["time"]
        if end_time == start_time:  # Handle case where times are the same
            t = 1.0
        else:
            t = (current_music_time - start_time) / (end_time - start_time)
            t = max(0.0, min(1.0, t))  # Clamp between 0 and 1
        
        # Interpolate position
        new_position = [
            start_waypoint["position"][0] + (target_waypoint["position"][0] - start_waypoint["position"][0]) * t,
            start_waypoint["position"][1] + (target_waypoint["position"][1] - start_waypoint["position"][1]) * t,
            start_waypoint["position"][2] + (target_waypoint["position"][2] - start_waypoint["position"][2]) * t
        ]
        
        # Interpolate rotation
        new_rotation = [
            start_waypoint["rotation"][0] + (target_waypoint["rotation"][0] - start_waypoint["rotation"][0]) * t,
            start_waypoint["rotation"][1] + (target_waypoint["rotation"][1] - start_waypoint["rotation"][1]) * t,
            start_waypoint["rotation"][2] + (target_waypoint["rotation"][2] - start_waypoint["rotation"][2]) * t
        ]
        
        # Apply the interpolated transforms
        self.camera_rig._matrix = Matrix.make_identity()
        self.camera_rig.set_position(new_position)
        self.camera_rig.rotate_x(math.radians(new_rotation[0]))
        self.camera_rig.rotate_y(math.radians(new_rotation[1]))
        self.camera_rig.rotate_z(math.radians(new_rotation[2]))
        
        # Debug output when reaching a waypoint
        if not hasattr(self, '_last_target_index') or self._last_target_index != current_target_index:
            self._last_target_index = current_target_index
            print(f"Moving towards waypoint {current_target_index} for {selected_instrument} (target time: {target_waypoint['time']:.2f}s)")
            print(f"Target position: {target_waypoint['position']}, rotation: {target_waypoint['rotation']}")
    
    def calculate_arrow_travel_time(self):
        """Calculate how long it takes an arrow to travel from spawn to target ring, considering world coordinates"""
        if ARROW_START_POSITION is None or RING_POSITION is None or ARROW_UNITS_PER_SECOND is None:
            print("Error: Arrow positioning or speed constants not defined. Cannot calculate travel time.")
            self.arrow_travel_time = -1  # Indicate error
            return -1

        if ARROW_UNITS_PER_SECOND == 0:
            print("Error: ARROW_UNITS_PER_SECOND is zero. Cannot calculate travel time (division by zero).")
            self.arrow_travel_time = float('inf')
            return float('inf')

        # Since we're using the pivot relative to the camera, the arrows will always travel 
        # the same distance in local space, regardless of camera position/rotation
        # Just use the local x-positions as in the original implementation
        arrow_start_x = ARROW_START_POSITION[0]
        ring_x = RING_POSITION[0]
        
        distance = abs(ring_x - arrow_start_x)
        
        self.arrow_travel_time = distance / ARROW_UNITS_PER_SECOND
        
        print(f"Arrow travel time calculated: {self.arrow_travel_time:.2f} seconds")
        print(f"  Arrow local position: {ARROW_START_POSITION}")
        print(f"  Ring local position: {RING_POSITION}")
        print(f"  Distance: {distance}, Speed: {ARROW_UNITS_PER_SECOND} units/sec")
        
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
            if arrow_type_str_lower in ARROW_TYPE_NAMES:
                angle = ARROW_TYPE_NAMES[arrow_type_str_lower]
            else:
                print(f"Warning: Unknown arrow_type_str '{arrow_type_str}'. Defaulting to UP (0 degrees).")
                angle = ARROW_TYPE_UP
        else:
            # If no type specified, choose a random one
            possible_angles = [ARROW_TYPE_UP, ARROW_TYPE_LEFT, ARROW_TYPE_DOWN, ARROW_TYPE_RIGHT]
            angle = random.choice(possible_angles)
            print(f"Warning: create_single_arrow called without arrow_type_str. Spawning random arrow (angle: {angle}).")
        
        # Create arrow object using config values
        arrow = Arrow(color=ARROW_COLOR, offset=[0, 0, 0], debug_mode=self.debug_mode, speed=ARROW_UNITS_PER_SECOND)
        
        # Add arrow to the pivot node
        self.arrow_ring_pivot.add(arrow.rig)
        arrow.rotate(math.radians(angle), 'z')  # Rotate based on the determined angle
        
        # ARROW_START_POSITION is imported from config.py
        arrow.set_position(list(ARROW_START_POSITION))
        
        # Generate a unique ID for the arrow
        import uuid
        arrow.unique_id = str(uuid.uuid4())
        
        # Add to arrows list
        self.arrows.append(arrow)
        
        return arrow
    
    def check_arrow_ring_collision(self, arrow, current_music_time):
        """
        Check for collision between an arrow and the target ring.
        
        Parameters:
            arrow: The arrow to check for collision
            current_music_time: The current time in the music track for logging
            
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
        ring_pos = self.target_ring.local_position
        
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
        previous_potential_collision_value = getattr(arrow, 'potential_collision_value', 0)

        if all_corners_in_inner:
            # Arrow is completely inside the inner ring (full interception)
            if hasattr(arrow, 'potential_collision_value') and arrow.potential_collision_value != 1:
                print(f"Arrow[{arrow.unique_id}]: Now fully inside ring (value: 1.0)")
                # Log timing if this is the first frame it's considered colliding and it has a target time
                if previous_potential_collision_value == 0 and hasattr(arrow, 'keyframe_target_time'):
                    time_diff = current_music_time - arrow.keyframe_target_time
                    print(f"TIMING LOG: Arrow[{arrow.unique_id}] in ring at music_time: {current_music_time:.2f}s. Target: {arrow.keyframe_target_time:.2f}s. Diff: {time_diff:.2f}s")

            arrow.potential_collision_value = 1
        elif any_corner_in_outer:
            # Arrow is at least partially inside the ring (partial interception)
            if hasattr(arrow, 'potential_collision_value') and arrow.potential_collision_value != 0.5:
                if hasattr(arrow, 'potential_collision_value') and arrow.potential_collision_value == 1:
                    print(f"Arrow[{arrow.unique_id}]: Now touching outer ring (value: 0.5)")
                else:
                    print(f"Arrow[{arrow.unique_id}]: Now partially inside ring (value: 0.5)")
                 # Log timing if this is the first frame it's considered colliding and it has a target time
                if previous_potential_collision_value == 0 and hasattr(arrow, 'keyframe_target_time'):
                    time_diff = current_music_time - arrow.keyframe_target_time
                    print(f"TIMING LOG: Arrow[{arrow.unique_id}] in ring at music_time: {current_music_time:.2f}s. Target: {arrow.keyframe_target_time:.2f}s. Diff: {time_diff:.2f}s")                   
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
                    
                    # Apply penalty if not scored and not already penalized for being a miss
                    if (not hasattr(arrow, 'scored') or not arrow.scored) and \
                       (not hasattr(arrow, 'penalized_as_miss') or not arrow.penalized_as_miss):
                        print(f"Arrow[{arrow.unique_id if hasattr(arrow, 'unique_id') else 'N/A'}]: Penalizing -25 for MISS (exited ring).")
                        self.ui_manager.update_score(-25, is_perfect=False)
                        self._update_collision_text("MISS!")
                        arrow.penalized_as_miss = True
                    
                    print(f"Arrow[{arrow.unique_id if hasattr(arrow, 'unique_id') else 'N/A'}]: Triggering miss animation after completely exiting ring")
                    self.animation_manager.start_falling_animation(self.active_object_rig, self.highlighted_index, self.object_meshes)
                    arrow.miss_animation_played = True
                    
                    # Mark the arrow as processed if it has a unique_id
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
            
            self.gameplay_key_press_consumed_by_hit_this_frame = True

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
                self._update_collision_text("PERFECT!")
                
                # Trigger random animation only on perfect hit
                self.animation_manager.trigger_random_animation(self.active_object_rig, self.highlighted_index, self.object_meshes)
            else:
                # Partial hit - update score, don't trigger falling animation
                print(f"DEBUG: Partial hit score. Arrow ID: {arrow.unique_id if hasattr(arrow, 'unique_id') else 'N/A'}, collision_value: {arrow.collision_value:.2f}, score_value: {score_value}")
                self.ui_manager.update_score(score_value, is_perfect=False)
                self._update_collision_text("HIT!")
                
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
                self._update_collision_text(pause_message)
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
    
    def handle_arrows(self, delta_time, current_music_time):
        """Handle arrow movement, collision detection, and removal"""
        # Check for any arrow key press this frame
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
                
                # If this was a missed arrow, not scored and not already penalized, apply penalty
                if (not hasattr(arrow, 'scored') or not arrow.scored) and \
                   (not hasattr(arrow, 'penalized_as_miss') or not arrow.penalized_as_miss):
                    print(f"Arrow[{arrow.unique_id if hasattr(arrow, 'unique_id') else 'N/A'}]: Penalizing -25 for MISS (off-screen).")
                    self.ui_manager.update_score(-25, is_perfect=False) # Apply -25 penalty
                    arrow.penalized_as_miss = True
                    # Ensure it's added to processed_arrow_uuids if it has an ID, as it's now fully handled
                    if hasattr(arrow, 'unique_id') and arrow.unique_id not in self.processed_arrow_uuids:
                        self.processed_arrow_uuids.append(arrow.unique_id)
                    
                    # Only show MISS message for unscored arrows that we're penalizing
                    if not self.debug_mode:
                        self._update_collision_text("MISS!")
                # If it wasn't scored (even if already penalized), still update UI text and reset streak if applicable
                elif not hasattr(arrow, 'scored') or not arrow.scored:
                    self.ui_manager.update_score(0, is_perfect=False) # Reset streak (no points change if already penalized)
        
        # Process all arrows for collision
        for arrow in self.arrows:
            # Skip arrows that have been marked as ineligible for detection
            if hasattr(arrow, 'ineligible_for_detection') and arrow.ineligible_for_detection:
                continue
                
            # Check for collision with ring
            self.check_arrow_ring_collision(arrow, current_music_time)
        
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
            # Toggle debug camera view with N key
            if self.input.is_key_down('n'):
                self.debug_camera_active = not self.debug_camera_active
                print(f"Debug camera {'activated' if self.debug_camera_active else 'deactivated'}")
                
            # Debug camera controls with Shift + navigation keys
            if self.debug_camera_active and self.input.is_key_pressed('left_shift'):
                # Debug camera rotation with I, J, K, L keys
                if self.input.is_key_pressed('i'):
                    self.debug_camera_rig.rotate_x(rotate_amount)
                if self.input.is_key_pressed('k'):
                    self.debug_camera_rig.rotate_x(-rotate_amount)
                if self.input.is_key_pressed('j'):
                    self.debug_camera_rig.rotate_y(rotate_amount)
                if self.input.is_key_pressed('l'):
                    self.debug_camera_rig.rotate_y(-rotate_amount)
                if self.input.is_key_pressed('o'):
                    self.debug_camera_rig.rotate_z(rotate_amount)
                if self.input.is_key_pressed('p'):
                    self.debug_camera_rig.rotate_z(-rotate_amount)
                
                # Debug camera position movement with W, A, S, D keys
                if self.input.is_key_pressed('w'):
                    self.debug_camera_rig.translate(0, 0, -move_amount)
                if self.input.is_key_pressed('s'):
                    self.debug_camera_rig.translate(0, 0, move_amount)
                if self.input.is_key_pressed('a'):
                    self.debug_camera_rig.translate(-move_amount, 0, 0)
                if self.input.is_key_pressed('d'):
                    self.debug_camera_rig.translate(move_amount, 0, 0)
                
                # Additional movement for up/down
                if self.input.is_key_pressed('e'):
                    self.debug_camera_rig.translate(0, move_amount, 0)  # Move up
                if self.input.is_key_pressed('q'):
                    self.debug_camera_rig.translate(0, -move_amount, 0)  # Move down
                
                # Update position text
                debug_pos = self.debug_camera_rig.global_position
                print(f"Debug camera position: {debug_pos[0]:.1f}, {debug_pos[1]:.1f}, {debug_pos[2]:.1f}")
            
            # Main camera controls continue as before (only when debug camera is not active or shift not pressed)
            if not self.debug_camera_active or not self.input.is_key_pressed('left_shift'):
                # Camera rotation with I, J, K, L keys
                if self.input.is_key_pressed('i'):
                    self.camera_rig.rotate_x(rotate_amount)  # Look up
                    # Update rotation tracking
                    if hasattr(self.camera_rig, 'x_rotation'):
                        self.camera_rig.x_rotation += rotate_amount * (180/math.pi)
                if self.input.is_key_pressed('k'):
                    self.camera_rig.rotate_x(-rotate_amount) # Look down
                    # Update rotation tracking
                    if hasattr(self.camera_rig, 'x_rotation'):
                        self.camera_rig.x_rotation -= rotate_amount * (180/math.pi)
                if self.input.is_key_pressed('j'):
                    self.camera_rig.rotate_y(rotate_amount)  # Turn left
                    # y rotation is tracked in the rotate_y method
                if self.input.is_key_pressed('l'):
                    self.camera_rig.rotate_y(-rotate_amount) # Turn right
                    # y rotation is tracked in the rotate_y method
                    
                # Add Z rotation controls with O and P keys
                if self.input.is_key_pressed('o'):
                    self.camera_rig.rotate_z(rotate_amount)  # Roll left
                    # z rotation is tracked in the rotate_z method
                if self.input.is_key_pressed('p'):
                    self.camera_rig.rotate_z(-rotate_amount) # Roll right
                    # z rotation is tracked in the rotate_z method
                
                # Camera position movement with W, A, S, D keys
                if self.input.is_key_pressed('w'):
                    self.camera_rig.translate(0, 0, -move_amount)  # Move forward
                if self.input.is_key_pressed('s'):
                    self.camera_rig.translate(0, 0, move_amount)   # Move backward
                if self.input.is_key_pressed('a'):
                    self.camera_rig.translate(-move_amount, 0, 0)  # Move left
                if self.input.is_key_pressed('d'):
                    self.camera_rig.translate(move_amount, 0, 0)   # Move right
            
            # Allow immediate resume from pause with spacebar
            if self.debug_paused and self.input.is_key_down('space'):
                self.debug_paused = False
                self.debug_pause_arrow = None
                self._update_collision_text(" ")
                print("Debug pause canceled by user")
            
            # Update camera position and rotation text
            self.update_camera_debug_text()
        
        # Create a general animation state check
        is_animating = self.animation_manager.is_animating()
        
        # Check for U key (falling animation) first - it has priority and will interrupt other animations
        if self.input.is_key_down('u'):
            # Always trigger falling animation immediately, even if another animation is running
            self.animation_manager.start_falling_animation(self.active_object_rig, self.highlighted_index, self.object_meshes)
        # For other animations (Q, W, E, R, T, Y), only start if nothing is currently animating
        elif not is_animating:
            # Keep the original animation controls but only if shift is not pressed or debug camera not active
            if not self.debug_mode or not self.debug_camera_active or not self.input.is_key_pressed('left_shift'):
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
    
    def update_camera_debug_text(self):
        """Display camera position and rotation text in debug mode"""
        if self.debug_mode:
            # Get camera position
            pos = self.camera_rig.global_position
            
            # Get camera rotation using the new tracking method
            rotation = {'x': 0, 'y': 0, 'z': 0}
            if hasattr(self.camera_rig, 'get_rotation_values'):
                try:
                    rotation = self.camera_rig.get_rotation_values()
                    # Normalize rotation values to -360 to 360 degrees range
                    for axis in ['x', 'y', 'z']:
                        # Use modulo to wrap the value, then handle the -360 to 0 range
                        rotation[axis] %= 360
                        # If value is greater than 180, convert to negative equivalent
                        if rotation[axis] > 180:
                            rotation[axis] -= 360
                except Exception as e:
                    print(f"Warning: Could not get camera rotation values: {e}")
            
            # Format the debug text - very compact format with all three rotation values
            debug_text = f"Pos: ({pos[0]:.1f},{pos[1]:.1f},{pos[2]:.1f}), Rot: ({rotation['x']:.1f},{rotation['y']:.1f},{rotation['z']:.1f})"
            
            # Update the dedicated debug info display
            self.ui_manager.update_debug_info(debug_text)
    
    def _update_collision_text(self, text):
        """
        Helper method to update collision text and manage timers.
        Messages like "EMPTY MISS!" or "MISS!" will be cleared after 0.5 seconds.
        """
        # First update the actual text
        self.ui_manager.update_collision_text(text)
        
        # Check if this is a miss message that should use the timer
        if text.strip() == "EMPTY MISS!" or text.strip() == "MISS!":
            # Start the timer for this message
            self.empty_miss_message_active = True
            self.empty_miss_message_timer = 0
        elif text.strip() != "":
            # Any other non-empty message should cancel the timer
            self.empty_miss_message_active = False
            self.empty_miss_message_timer = 0
        # For empty/space messages, don't change the timer state
    
    def update(self):
        """Update game logic (called every frame)"""
        # Handle fullscreen toggle (F11 key) - works in all phases
        if self.input.is_key_down('f11'):
            self.toggle_fullscreen_mode()
        
        if self.current_phase == GamePhase.SELECTION:
            # Handle input for selection phase
            phase_changed, selected_index = self.phase_manager.handle_selection_input(self.input)
            
            if phase_changed:
                self.current_phase = GamePhase.GAMEPLAY
                self.highlighted_index = selected_index
                # Synchronize active object with PhaseManager
                self.active_object_rig = self.phase_manager.active_object_rig
                
                # Make the arrow and ring visible now that we're in gameplay phase
                self._make_arrow_ring_visible()
                
                # Load and play music for the selected instrument
                self.music_system.load_track_for_instrument(selected_index)
                self.music_system.play_music()
                
            # Render scene with current camera
            self.renderer.render(self.scene, self.camera)
            
        elif self.current_phase == GamePhase.GAMEPLAY:
            self.gameplay_key_press_consumed_by_hit_this_frame = False
            # Handle input for gameplay phase
            self.handle_gameplay_input()
            
            # Only use automatic camera animation when not in debug mode
            if not self.debug_mode:
                self.update_camera_animation()
            
            # Check for empty miss message timer
            if self.empty_miss_message_active:
                self.empty_miss_message_timer += self.delta_time
                if self.empty_miss_message_timer >= self.empty_miss_message_duration:
                    self.empty_miss_message_active = False
                    self.empty_miss_message_timer = 0
                    self._update_collision_text(" ")
            
            # Check for debug pause state
            if self.debug_mode and self.debug_paused:
                self.debug_pause_timer += self.delta_time
                
                # Display pause info
                pause_text = f"GAME PAUSED - Resume in {max(0, self.debug_pause_duration - self.debug_pause_timer):.1f}s"
                self._update_collision_text(pause_text)
                
                # Resume after pause duration or if space is pressed
                if self.debug_pause_timer >= self.debug_pause_duration or self.input.is_key_down('space'):
                    self.debug_paused = False
                    self.debug_pause_arrow = None
                    # In debug mode, restore camera debug info
                    if self.debug_mode:
                        self.update_camera_debug_text()
                    # Always clear the collision text
                    self._update_collision_text(" ")
                    print("Debug pause ended - game resumed")
            else:
                # Only process game updates if not paused and arrow-ring system is visible
                if self.music_system.music_playing and self.arrow_ring_visible:
                    # Dynamically update the arrow travel time based on current camera and pivot position
                    self.music_system.update_arrow_travel_time()
                    
                    # Use callback function to create arrows at the right time
                    self.music_system.update_keyframe_arrows(self.create_single_arrow)
                
                # Continue handling movement and removal of existing arrows
                current_music_time = self.music_system.get_music_time()
                self.handle_arrows(self.delta_time, current_music_time)

                # --- BEGIN PENALTY LOGIC FOR PRESSING KEY WHEN NO ARROW IN RING ---
                # Check if any gameplay arrow key was pressed down this frame
                up_key_down = self.input.is_key_down('up')
                down_key_down = self.input.is_key_down('down')
                left_key_down = self.input.is_key_down('left')
                right_key_down = self.input.is_key_down('right')

                any_gameplay_arrow_key_down_this_frame = up_key_down or down_key_down or left_key_down or right_key_down

                if any_gameplay_arrow_key_down_this_frame and not self.gameplay_key_press_consumed_by_hit_this_frame and self.arrow_ring_visible:
                    # Check if any active, scorable arrow is currently inside the ring.
                    # This is still needed to differentiate between a key press that *could* have hit something
                    # (but was the wrong key) vs. a key press when nothing was hittable.
                    an_arrow_is_hittable_in_ring = False
                    for arrow_candidate in self.arrows:
                        if not (hasattr(arrow_candidate, 'ineligible_for_detection') and arrow_candidate.ineligible_for_detection) and \
                           (hasattr(arrow_candidate, 'unique_id') and arrow_candidate.unique_id not in self.processed_arrow_uuids) and \
                           (hasattr(arrow_candidate, 'potential_collision_value') and arrow_candidate.potential_collision_value > 0):
                            an_arrow_is_hittable_in_ring = True
                            break
                    
                    if not an_arrow_is_hittable_in_ring:
                        # Apply penalty: An arrow key was pressed, it did not result in a hit, 
                        # and no arrow was in a hittable position.
                        self.ui_manager.update_score(-50, is_perfect=False)
                        # Show penalty message (only in non-debug mode)
                        if not self.debug_mode:
                            self._update_collision_text("EMPTY MISS!")
                # --- END PENALTY LOGIC ---
                
                # Check if music has finished and transition to end screen
                if not self.debug_mode and self.music_system.is_music_finished():
                    print("Music has finished - transitioning to end screen")
                    self._transition_to_end_screen()
            
            # Render scene with active camera (main or debug)
            if self.debug_mode and self.debug_camera_active:
                self.renderer.render(self.scene, self.debug_camera)
            else:
                self.renderer.render(self.scene, self.camera)
                
        elif self.current_phase == GamePhase.END_SCREEN:
            # Handle input for end screen
            self.handle_end_screen_input()
            
            # Render scene with current camera
            self.renderer.render(self.scene, self.camera)
    
    def _transition_to_end_screen(self):
        """Transition from gameplay to end screen phase"""
        self.current_phase = GamePhase.END_SCREEN
        
        # Get the final score
        final_score = self.ui_manager.score
        
        # Hide the arrow ring
        self._hide_arrow_ring()
        
        # Clear any existing arrows
        for arrow in self.arrows[:]:
            if arrow.rig in self.arrow_ring_pivot.descendant_list:
                self.arrow_ring_pivot.remove(arrow.rig)
        self.arrows = []
        self.processed_arrow_uuids = []
        
        # Show the end screen
        self.ui_manager.show_ui_for_end_screen(final_score)
        
    def _hide_arrow_ring(self):
        """Hide the arrow ring and target ring"""
        if hasattr(self, 'arrow_ring_visible') and self.arrow_ring_visible:
            self.arrow_ring_visible = False
            
            # Hide arrow ring pivot and all its children (including arrows)
            if hasattr(self, 'arrow_ring_pivot') and self.arrow_ring_pivot in self.camera.descendant_list:
                self.camera.remove(self.arrow_ring_pivot)
            
            # Since the target ring is already a child of arrow_ring_pivot, we don't need to remove it separately
    
    def handle_end_screen_input(self):
        """Handle user input on the end screen"""
        # Handle 'R' key to replay with the same character
        if self.input.is_key_down('r'):
            print("Replaying with the same character")
            self._replay_with_same_character()
            
        # Handle 'C' key to return to character selection
        elif self.input.is_key_down('c'):
            print("Returning to character selection")
            self._return_to_character_selection()
    
    def _replay_with_same_character(self):
        """Restart gameplay with the same character"""
        # Hide the end screen
        self.ui_manager.hide_end_screen()
        
        # Reset gameplay phase
        self.current_phase = GamePhase.GAMEPLAY
        
        # Make the arrow and ring visible again
        self._make_arrow_ring_visible()
        
        # Load and play music for the selected instrument
        self.music_system.load_track_for_instrument(self.highlighted_index)
        self.music_system.play_music()
        
        # Reset score
        self.ui_manager.show_ui_for_gameplay_phase()
    
    def _return_to_character_selection(self):
        """Return to character selection phase"""
        # Hide the end screen
        self.ui_manager.hide_end_screen()
        
        # Reset to selection phase
        self.current_phase = GamePhase.SELECTION
        
        # Set up selection phase
        self.phase_manager.setup_selection_phase()
        
        # Reset highlighted index and active object rig
        self.highlighted_index = 0
        self.active_object_rig = self.phase_manager.active_object_rig
        
        # Hide arrow ring
        self._hide_arrow_ring()
        
        # Load and play selection music
        self.music_system.load_selection_music()
        self.music_system.play_selection_music() 