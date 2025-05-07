import math
from nt import remove
import pathlib
import sys
import pygame
import json
import time
from enum import Enum, auto
# Add parent directory to sys.path
sys.path.append(str(pathlib.Path(__file__).resolve().parents[1]))
from core.base import Base
from core_ext.camera import Camera
from core_ext.mesh import Mesh
from core_ext.renderer import Renderer
from core_ext.scene import Scene
from geometry.miguelinstrument import MiguelGeometry
from geometry.zeinstrument import ZeGeometry
from geometry.anainstrument import AnaGeometry
from geometry.brandoninstrument import BrandonGeometry
from extras.axes import AxesHelper
from extras.grid import GridHelper
from extras.movement_rig import MovementRig
from material.surface import SurfaceMaterial
from core_ext.texture import Texture
from material.texture import TextureMaterial
from core.obj_reader2 import my_obj_reader2
from core.matrix import Matrix
from geometry.rectangle import RectangleGeometry
from geometry.arrow import Arrow
from core.obj_reader2 import my_obj_reader2 # <--- ALTERADO AQUI
from geometry.geometry import Geometry
import os 
import geometry.nightClub as nightclub # <--- ALTERADO AQUI
from geometry.ring import RingGeometry
from extras.text_texture import TextTexture
from game_phases import GamePhase
from arrow_manager import ArrowManager
from config import *
from geometry.parametric import ParametricGeometry
import numpy as np

class Example(Base):
    """
    Render the axes and the rotated xy-grid.
    Features both camera and object movement controls.
    
    Phase 1 (Selection):
    - Camera faces backward showing all 4 objects
    - Left/right arrows select object
    - Enter confirms selection and switches to gameplay phase
    
    Phase 2 (Gameplay):
    - Camera faces forward 
    - Selected object is centered
    - Camera: WASDRF(move), QE(turn), TG(look)
    - Object: Arrow keys(move), UO(turn), KL(tilt)
    - Q/W/E keys: Perform 360° flip animation
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

    # Music and keyframe configurations for each instrument
    INSTRUMENT_TRACKS = {
        0: {  # Miguel's instrument
            "music": "music/fitnessgram.mp3",
            "keyframes": "keyframes/keyframes_1.json"
        },
        1: {  # Ze's instrument
            "music": "music/track2.mp3",
            "keyframes": "keyframes/keyframes_2.json"
        },
        2: {  # Ana's instrument
            "music": "music/track3.mp3",
            "keyframes": "keyframes/keyframes_3.json"
        },
        3: {  # Brandon's instrument
            "music": "music/track4.mp3",
            "keyframes": "keyframes/keyframes_4.json"
        }
    }

    def initialize(self):
        print("Initializing program...")
        
        # Print debug mode status to confirm it's properly set
        print(f"\n==== Program running with debug_mode = {self.debug_mode} ====\n")
        
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
        # Initialize game phase
        self.current_phase = GamePhase.SELECTION
        self.highlighted_index = 0
        
        # Initialize score
        self.score = 0
        
        # Initialize timing adjustment for calibration
        self.timing_adjustment = 0.9
        
        # Initialize debug pause state
        self.debug_paused = False
        self.debug_pause_duration = 3.0  # Pause for 3 seconds
        self.debug_pause_timer = 0
        self.debug_pause_arrow = None
        
        # Initialize music and keyframes
        self.initialize_music()
        self.keyframes = []
        self.current_keyframe_index = 0
        
        # No need to load music/keyframes here as they'll be loaded when an instrument is selected
        print("Music and keyframe system initialized. Tracks will be loaded upon instrument selection.")
        
        # Initialize perfect hit streak counter
        self.perfect_streak = 0
        
        # Track arrows that have contributed to the streak
        self.streak_arrows = []
        
        # Track processed arrows to ensure their status isn't changed by new arrows
        self.processed_arrow_uuids = []
        
        # Define ring configuration constants
        self.RING_INNER_RADIUS = 0.55
        self.RING_OUTER_RADIUS = 0.65
        self.RING_SCALE = 1.0
        self.RING_POSITION = [1, -0.02, 8]  # [x, z, y]
        
        # Camera animation properties - initial setup for gameplay phase
        self.camera_hardcoded_position = CAMERA_INITIAL_POSITION
        self.camera_hardcoded_rotation = CAMERA_INITIAL_ROTATION
        self.camera_animation_time = 0  # Track elapsed time for future animation
        
        self.renderer = Renderer()
        self.scene = Scene()
        self.camera = Camera(aspect_ratio=1280/720)
        
        # Set up camera rig for movement
        self.camera_rig = MovementRig()
        self.camera_rig.add(self.camera)
        self.scene.add(self.camera_rig)

        # Create score text display
        score_texture = TextTexture(
            text="Score: 0",
            system_font_name="Arial",
            font_size=36,
            font_color=(255, 255, 255),  # White text
            background_color=(0, 0, 0, 128),  # Semi-transparent black background
            transparent=True,
            image_width=300,
            image_height=100,
            align_horizontal=0.0,  # Left-aligned
            align_vertical=0.5,    # Vertically centered
            image_border_width=0,  # Remove border
            image_border_color=(255, 255, 255)  # White border
        )
        score_material = TextureMaterial(texture=score_texture, property_dict={"doubleSide": True})
        score_geometry = RectangleGeometry(width=2, height=0.6)
        self.score_mesh = Mesh(score_geometry, score_material)
        
        # Create the score rig but don't add to scene directly - will be added to camera
        self.score_rig = MovementRig()
        self.score_rig.add(self.score_mesh)
        # Position score relative to camera view
        self.score_rig.set_position([2.6, 1.3, -3])
        
        # Store the score texture for updates
        self.score_texture = score_texture
        
        # Create streak text display
        streak_texture = TextTexture(
            text="Streak: 0",
            system_font_name="Arial",
            font_size=24,
            font_color=(255, 255, 255),  # White text
            background_color=(0, 0, 0, 128),  # Semi-transparent black background
            transparent=True,
            image_width=300,
            image_height=60,
            align_horizontal=0.0,  # Left-aligned
            align_vertical=0.5,    # Vertically centered
            image_border_width=0,  # Remove border
            image_border_color=(255, 255, 255)  # White border
        )
        streak_material = TextureMaterial(texture=streak_texture, property_dict={"doubleSide": True})
        streak_geometry = RectangleGeometry(width=2, height=0.4)
        self.streak_mesh = Mesh(streak_geometry, streak_material)
        
        # Create the streak rig but don't add to scene directly - will be added to camera
        self.streak_rig = MovementRig()
        self.streak_rig.add(self.streak_mesh)
        # Position streak below score
        self.streak_rig.set_position([2.6, 0.8, -3])
        
        # Store the streak texture for updates
        self.streak_texture = streak_texture
        
        # Initially hide the score display in selection phase
        # self.score_mesh.visible = False

        # Load textures and materials for each instrument
        miguel_texture = Texture(file_name="images/miguelJPG.jpg")
        miguel_material = TextureMaterial(texture=miguel_texture)

        ze_texture = Texture(file_name="images/zeJPG.jpg") # Assuming this filename
        ze_material = TextureMaterial(texture=ze_texture)

        ana_texture = Texture(file_name="images/anaJPG.jpg") # Assuming this filename
        ana_material = TextureMaterial(texture=ana_texture)

        brandon_texture = Texture(file_name="images/brandonPNG.png") # Assuming this filename
        brandon_material = TextureMaterial(texture=brandon_texture)
        
        # Create geometry, texture, material, and mesh for the title image
        title_geometry = RectangleGeometry(width=16, height=4)  # Adjust width/height as needed
        title_texture = Texture(file_name="images/game_title_transparent.png")
        title_material = TextureMaterial(texture=title_texture, property_dict={"doubleSide": True}) # Ensure it's visible from the back if needed
        self.title_mesh = Mesh(title_geometry, title_material)
        self.title_rig = MovementRig()
        self.title_rig.add(self.title_mesh)
        # Title rig is added to the scene and positioned in setup_selection_phase

        # Load Miguel's object
        positions_miguel, uvs_miguel = my_obj_reader2("geometry/miguelOBJ.obj")
        geometry_miguel = MiguelGeometry(1, 1, 1, positions_miguel, uvs_miguel)
        self.mesh_miguel = Mesh(geometry_miguel, miguel_material) # Use Miguel's material
        self.object_rig_miguel = MovementRig()
        self.object_rig_miguel.add(self.mesh_miguel)
        self.object_rig_miguel.set_position([-3, 0, 0]) # Position Miguel
        self.scene.add(self.object_rig_miguel)

        # Load Ze's object
        positions_ze, uvs_ze = my_obj_reader2("geometry/zeOBJ.obj") # TODO: Replace with zeOBJ.obj later
        geometry_ze = ZeGeometry(1, 1, 1, positions_ze, uvs_ze) # Use ZeGeometry
        self.mesh_ze = Mesh(geometry_ze, ze_material) # Use Ze's material
        self.object_rig_ze = MovementRig()
        self.object_rig_ze.add(self.mesh_ze)
        self.object_rig_ze.set_position([-1, 0, 0]) # Position Ze
        self.scene.add(self.object_rig_ze)

        # Load Ana's object 
        positions_ana, uvs_ana = my_obj_reader2("geometry/anaOBJ.obj") # TODO: Replace with anaOBJ.obj later
        geometry_ana = AnaGeometry(1, 1, 1, positions_ana, uvs_ana) # Use AnaGeometry
        self.mesh_ana = Mesh(geometry_ana, ana_material) # Use Ana's material
        self.object_rig_ana = MovementRig()
        self.object_rig_ana.add(self.mesh_ana)
        self.object_rig_ana.set_position([1, 0, 0]) # Position Ana
        self.scene.add(self.object_rig_ana)

        # Load Brandon's object 
        positions_brandon, uvs_brandon = my_obj_reader2("geometry/brandonOBJ.obj") # TODO: Replace with brandonOBJ.obj later
        geometry_brandon = BrandonGeometry(2, 2, 1, positions_brandon, uvs_brandon) # Use BrandonGeometry
        self.mesh_brandon = Mesh(geometry_brandon, brandon_material) # Use Brandon's material
        self.object_rig_brandon = MovementRig()
        self.object_rig_brandon.add(self.mesh_brandon)
        self.object_rig_brandon.set_position([3, 0, 0]) # Position Brandon
        self.scene.add(self.object_rig_brandon)

        # Store all object rigs in a list for easier management
        self.object_rigs = [
            self.object_rig_miguel,
            self.object_rig_ze,
            self.object_rig_ana,
            self.object_rig_brandon
        ]
        
        # Initially set active object rig to the highlighted one
        self.active_object_rig = self.object_rigs[self.highlighted_index]
        
        # Set up the camera for the selection phase
        self.setup_selection_phase()
        
        # Only show debug elements (axes and grid) when in debug mode
        if self.debug_mode:
            # Debug visualization helpers
            axes = AxesHelper(axis_length=2)
            self.scene.add(axes)
            grid = GridHelper(
                size=20,
                grid_color=[1, 1, 1],
                center_color=[1, 1, 0]
            )
            grid.rotate_x(-math.pi / 2)
            self.scene.add(grid)
        
        self.setup_arrow_spawning(2.0)
        self.handle_nightClub()

        # Ring (target circle)
        ring_geometry = RingGeometry(inner_radius=self.RING_INNER_RADIUS, outer_radius=self.RING_OUTER_RADIUS, segments=32)
        ring_material = SurfaceMaterial(property_dict={"baseColor": [0, 1, 0], "doubleSide": True})  # Green color for the ring, ensure doubleSided
        self.target_ring = Mesh(ring_geometry, ring_material)
        self.target_ring.set_position(self.RING_POSITION) # Use global variable for ring position
        self.target_ring.rotate_x(0)  # Rotated to be vertical
        self.target_ring.scale(self.RING_SCALE) # Apply scaling
        self.scene.add(self.target_ring)
        
        # Create debug visualization for the inner circle of the ring if in debug mode
        if self.debug_mode:
            self.add_ring_debug_visualization()
        
        # Create collision text display (similar to score)
        collision_texture = TextTexture(
            text=" ",  # Initially empty
            system_font_name="Arial",
            font_size=48,
            font_color=(255, 255, 0),  # Yellow text
            background_color=(0, 0, 0, 128),
            transparent=True,
            image_width=300,
            image_height=100,
            align_horizontal=0.5,
            align_vertical=0.5,
            image_border_width=0
        )
        collision_material = TextureMaterial(texture=collision_texture, property_dict={"doubleSide": True})
        collision_geometry = RectangleGeometry(width=2, height=0.6)
        self.collision_mesh = Mesh(collision_geometry, collision_material)
        self.collision_rig = MovementRig()
        self.collision_rig.add(self.collision_mesh)
        self.collision_rig.set_position([-2.6, 1.3, -3]) # Position collision status display
        self.collision_texture = collision_texture

        # Create and set up the arrow manager (Handles arrow spawning, movement, and collision)
        self.arrow_manager = ArrowManager(self.scene, self.target_ring, debug_mode=self.debug_mode)

        # Calculate arrow travel time (needs Arrow class to be defined/imported)
        self.calculate_arrow_travel_time()

        # Initialize rotation animation parameters
        self.is_rotating = False
        self.rotation_start_time = 0
        self.rotation_axis = None
        self.rotation_duration = 0.5  # Duration of rotation animation in seconds
        self.total_rotation_angle = 2 * math.pi  # 360 degrees in radians
        self.original_rotation = [0, 0, 0]  # Store original object rotation

    def calculate_arrow_travel_time(self):
        """Calculate how long it takes an arrow to travel from spawn to target ring."""
        # ARROW_START_POSITION and ARROW_UNITS_PER_SECOND are expected from config.py
        # self.RING_POSITION is defined in initialize()
        
        # Assuming travel is primarily along the X-axis as per the plan.
        # ARROW_START_POSITION[0] is the x-coordinate of arrow spawn.
        # self.RING_POSITION[0] is the x-coordinate of the ring.
        
        if ARROW_START_POSITION is None or self.RING_POSITION is None or ARROW_UNITS_PER_SECOND is None:
            print("Error: Arrow positioning or speed constants not defined. Cannot calculate travel time.")
            self.arrow_travel_time = -1 # Indicate error
            return -1

        if ARROW_UNITS_PER_SECOND == 0:
            print("Error: ARROW_UNITS_PER_SECOND is zero. Cannot calculate travel time (division by zero).")
            self.arrow_travel_time = float('inf') # Or handle as an error appropriately
            return float('inf')

        arrow_start_x = ARROW_START_POSITION[0]
        ring_x = self.RING_POSITION[0]
        
        distance = abs(ring_x - arrow_start_x)
        
        self.arrow_travel_time = distance / ARROW_UNITS_PER_SECOND
        
        print(f"Arrow travel time calculated: {self.arrow_travel_time:.2f} seconds (Distance: {distance}, Speed: {ARROW_UNITS_PER_SECOND} units/sec)")
        return self.arrow_travel_time

    def setup_selection_phase(self):
        # Hide score by removing from camera if it's present
        if self.score_rig in self.camera.descendant_list:
            self.camera.remove(self.score_rig)
            
        # Add the title rig to the scene
        self.scene.add(self.title_rig)
        # Position title rig (adjust coordinates as needed)
        # Camera Y is 105, objects Y is 100. Place title above. Centered X, same Z as objects.
        self.title_rig.set_position([0, 110, 0])

        # Reset camera transform first
        self.camera_rig._matrix = Matrix.make_identity()
        # Position camera high up and facing "backwards" and see all objects
        objects_y = 100 # Set the Y coordinate for the objects
        camera_y = objects_y + 5 # Position camera slightly above objects
        self.camera_rig.set_position([0.5, camera_y, 15]) # Use camera_y for camera, move closer (Z=15)
        
        # Reset all objects to their original positions and rotations with increased spacing, high up
        positions = [[-4.5, objects_y, 0], [-1.5, objects_y, 0], [1.5, objects_y, 0], [4.5, objects_y, 1.5]] # Use objects_y for objects
        for i, rig in enumerate(self.object_rigs):
            # Reset the transformation matrix to identity
            rig._matrix = Matrix.make_identity()
            # Set the initial position
            rig.set_position(positions[i])
            # Reset the scale (as highlight_selected_object changes it)
            rig.scale(1) # Scale back to 1
        
        # Apply highlighting to the currently selected object
        self.highlight_selected_object()

    def setup_gameplay_phase(self):
        # Show score by adding to camera if not already there
        if self.score_rig not in self.camera.descendant_list:
            self.camera.add(self.score_rig)
            
        # Show streak counter by adding to camera
        if self.streak_rig not in self.camera.descendant_list:
            self.camera.add(self.streak_rig)
        
        # Remove the title rig from the scene
        if self.title_rig in self.scene.descendant_list:
            self.scene.remove(self.title_rig)
            
        # Reset camera transform first
        self.camera_rig._matrix = Matrix.make_identity()
        
        # Apply hardcoded position and rotation for camera
        self.camera_rig.set_position(self.camera_hardcoded_position)
        
        # Apply rotations if needed
        if self.camera_hardcoded_rotation[0] != 0:
            self.camera_rig.rotate_x(self.camera_hardcoded_rotation[0])
        if self.camera_hardcoded_rotation[1] != 0:
            self.camera_rig.rotate_y(self.camera_hardcoded_rotation[1])
        if self.camera_hardcoded_rotation[2] != 0:
            self.camera_rig.rotate_z(self.camera_hardcoded_rotation[2])
            
        # Reset the animation time for future camera animation
        self.camera_animation_time = 0
        
        # Reset score to 0 for new game
        self.score = 0
        self.perfect_streak = 0
        self.streak_arrows = [] # Reset streak tracking
        print(f"Score: {self.score}")
        # Update score display text
        self.score_texture.update_text(f"Score: {int(self.score)}")
        self.streak_texture.update_text(f"Streak: {self.perfect_streak}")
        
        # Clear processed arrow UUIDs for new game
        self.processed_arrow_uuids = []
        print("Cleared processed arrow list for new game")
        
        # Initialize/reset arrow-related tracking for keyframe system
        self.arrows = [] # Clear existing arrows from previous game/selection phase
        self.current_keyframe_index = 0
        print(f"Keyframe index reset to {self.current_keyframe_index}")

        # Ensure arrow_travel_time is calculated (it should be from initialize, but good check)
        if not hasattr(self, 'arrow_travel_time') or self.arrow_travel_time == float('inf'):
            print("Warning: arrow_travel_time not properly set. Recalculating...")
            self.calculate_arrow_travel_time()
        
        self.remove_highlighting()
        self.active_object_rig._matrix = Matrix.make_identity()
        self.active_object_rig.set_position([0, 0, 0])
        
        # Get the index of the selected instrument and load its music/keyframes
        selected_index = self.object_rigs.index(self.active_object_rig)
        track_info = self.INSTRUMENT_TRACKS.get(selected_index)
        
        if track_info:
            # First load the music and keyframes
            music_loaded = self.load_music(track_info["music"])
            keyframes_loaded = self.load_keyframes(track_info["keyframes"])
            
            if music_loaded and keyframes_loaded:
                print(f"Loaded music track and keyframes for instrument {selected_index}")
                # Now start the music playback
                if self.play_music():
                    print("Music playback started successfully")
                else:
                    print("Failed to start music playback")
            else:
                print(f"Failed to load music or keyframes for instrument {selected_index}")
                # Set up simulation mode if loading failed
                self.music_playing = True
                self.music_start_time = time.time()
                print(f"Music playback SIMULATED. music_playing: {self.music_playing}, music_start_time: {self.music_start_time:.2f}")
        else:
            print(f"No track information found for instrument {selected_index}")

        # Define positions and rotations based on which instrument was selected
        # Format: [positions for instrument 0, positions for instrument 1, positions for instrument 2, positions for instrument 3]
        # Each "positions for instrument X" is a list of 3 [x,y,z] positions for the other instruments
        positions_by_selection = [
            # Positions when Miguel's instrument (index 0) is selected
            [
                None,                   # No position for Miguel (selected)
                [10, -0.45, 10.5],        # Position for Ze's instrument
                [12, -0.45, 7.2],        # Position for Ana's instrument
                [10, -1, 4.5]         # Position for Brandon's instrument
            ],
            # Positions when Ze's instrument (index 1) is selected
            [
                [10, -0.45, 10.5],        # Position for Miguel's instrument
                None,                   # No position for Ze (selected)
                [12, -0.45, 7.2],        # Position for Ana's instrument
                [10, -1, 4.5]         # Position for Brandon's instrument
            ],
            # Positions when Ana's instrument (index 2) is selected
            [
                [10, -0.45, 10.5],        # Position for Miguel's instrument
                [12, -0.45, 7.2],        # Position for Ze's instrument
                None,                   # No position for Ana (selected)
                [10, -1, 4.5]         # Position for Brandon's instrument
            ],
            # Positions when Brandon's instrument (index 3) is selected
            [
                [10, -0.45, 10.5],        # Position for Miguel's instrument
                [12, -0.45, 7.2],        # Position for Ze's instrument
                [10, -1, 4.5],        # Position for Ana's instrument
                None                    # No position for Brandon (selected)
            ]
        ]
        
        # Define rotations based on which instrument was selected
        # Format similar to positions_by_selection
        rotations_by_selection = [
            # Rotations when Miguel's instrument (index 0) is selected
            # the rotation axis are (x,y,z)
            [
                None,                       # No rotation for Miguel (selected)
                [math.pi/4, math.pi/6, 0],          # Rotation for Ze's instrument
                [math.pi/10, math.pi/2, 0],         # Rotation for Ana's instrument
                [-math.pi/4, -math.pi/8, -math.pi/4]          # Rotation for Brandon's instrument
            ],
            # Rotations when Ze's instrument (index 1) is selected
            [
                [math.pi/4, math.pi/6, 0],          # Rotation for Miguel's instrument
                None,                       # No rotation for Ze (selected)
                [math.pi/10, math.pi/2, 0],         # Rotation for Ana's instrument
                [-math.pi/4, -math.pi/8, -math.pi/4]          # Rotation for Brandon's instrument
            ],
            # Rotations when Ana's instrument (index 2) is selected
            [
                [math.pi/4, math.pi/6, 0],          # Rotation for Miguel's instrument
                [math.pi/4, math.pi/6, 0],          # Rotation for Ze's instrument
                None,                       # No rotation for Ana (selected)
                [-math.pi/4, -math.pi/8, -math.pi/4]          # Rotation for Brandon's instrument
            ],
            # Rotations when Brandon's instrument (index 3) is selected
            [
                [math.pi/4, math.pi/6, 0],          # Rotation for Miguel's instrument
                [math.pi/4, math.pi/6, 0],          # Rotation for Ze's instrument
                [math.pi/10, math.pi/2, 0],         # Rotation for Ana's instrument
                None                        # No rotation for Brandon (selected)
            ]
        ]
        
        # Apply positions and rotations based on selection
        for i, rig in enumerate(self.object_rigs):
            if rig != self.active_object_rig:
                rig._matrix = Matrix.make_identity()
                
                # Get position and rotation for this instrument based on which one was selected
                position = positions_by_selection[selected_index][i]
                rotation = rotations_by_selection[selected_index][i]
                
                if position:
                    rig.set_position(position)
                
                if rotation:
                    rig.rotate_y(rotation[1])
                    rig.rotate_x(rotation[0])
                    rig.rotate_z(rotation[2])

    def highlight_selected_object(self):
        # Simple highlighting by scaling up the selected object
        for i, rig in enumerate(self.object_rigs):
            # First, reset scale to 1 for all
            current_pos = rig.local_position # Store position
            rig._matrix = Matrix.make_identity() # Reset matrix (also resets scale)
            rig.set_position(current_pos) # Reapply position
            
            if i == self.highlighted_index:
                # Scale up the highlighted object
                rig.scale(1.2) # Apply scale
                
    def remove_highlighting(self):
        # Reset scale for all objects
        for rig in self.object_rigs:
            current_pos = rig.local_position # Store position
            rig._matrix = Matrix.make_identity() # Reset matrix (also resets scale)
            rig.set_position(current_pos) # Reapply position
            rig.scale(1) # Ensure scale is 1

    def update_camera_animation(self):
        """
        Updates camera position and rotation based on elapsed time.
        Moves the camera from initial position to final position over 10 seconds,
        then stays at the final position indefinitely.
        """
        # Initial position and rotation (hardcoded)
        initial_position = self.camera_hardcoded_position  # [0, 1.2, 7]
        initial_rotation = self.camera_hardcoded_rotation  # [0, -math.pi/2, 0]
        
        # Final position and rotation
        final_position = CAMERA_FINAL_POSITION
        final_rotation = CAMERA_FINAL_ROTATION
        
        # Time to reach final position (in seconds)
        transition_time = CAMERA_TRANSITION_TIME
        
        # If animation time is less than 0.1, use initial position without interpolation
        if self.camera_animation_time < 0.1:
            self.camera_rig._matrix = Matrix.make_identity()
            self.camera_rig.set_position(initial_position)
            self.apply_camera_rotation(initial_rotation)
            return
        
        # If animation time is greater than transition time, use final position
        if self.camera_animation_time >= transition_time + 0.1:
            self.camera_rig._matrix = Matrix.make_identity()
            self.camera_rig.set_position(final_position)
            self.apply_camera_rotation(final_rotation)
            return
        
        # During transition, interpolate between initial and final positions
        t = (self.camera_animation_time - 0.1) / transition_time  # Normalized time (0 to 1)
        
        # Interpolate position (linear)
        new_position = [
            initial_position[0] + (final_position[0] - initial_position[0]) * t,
            initial_position[1] + (final_position[1] - initial_position[1]) * t,
            initial_position[2] + (final_position[2] - initial_position[2]) * t
        ]
        
        # Interpolate rotation (linear)
        new_rotation = [
            initial_rotation[0] + (final_rotation[0] - initial_rotation[0]) * t,
            initial_rotation[1] + (final_rotation[1] - initial_rotation[1]) * t,
            initial_rotation[2] + (final_rotation[2] - initial_rotation[2]) * t
        ]
        
        # Apply new transforms
        self.camera_rig._matrix = Matrix.make_identity()
        self.camera_rig.set_position(new_position)
        
        # Apply rotations
        self.apply_camera_rotation(new_rotation)

    def apply_camera_rotation(self, rotation):
        """Helper method to apply rotation in the correct order"""
        if rotation[0] != 0:
            self.camera_rig.rotate_x(rotation[0])
        if rotation[1] != 0:
            self.camera_rig.rotate_y(rotation[1])
        if rotation[2] != 0:
            self.camera_rig.rotate_z(rotation[2])

    def update(self):
        if self.current_phase == GamePhase.SELECTION:
            # Handle input for selection phase
            self.handle_selection_input()
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
                pause_text = f"GAME PAUSED FOR COLLISION INSPECTION - Resume in {max(0, self.debug_pause_duration - self.debug_pause_timer):.1f}s"
                self.collision_texture.update_text(pause_text)
                
                # Resume after pause duration or if space is pressed
                if self.debug_pause_timer >= self.debug_pause_duration or self.input.is_key_down('space'):
                    self.debug_paused = False
                    self.debug_pause_arrow = None
                    self.collision_texture.update_text(" ")
                    print("Debug pause ended - game resumed")
            else:
                # Only process game updates if not paused
                # New keyframe-based arrow spawning and handling
                if self.music_playing:
                    self.update_keyframe_arrows()
                
                # Continue handling movement and removal of existing arrows
                self.handle_arrows(self.delta_time) # Pass delta_time for arrow.update
        
        self.renderer.render(self.scene, self.camera)
        
    def handle_gameplay_input(self):
        # Update camera animation time for future use in time-based camera animation
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
                self.collision_texture.update_text(" ")
                print("Debug pause canceled by user")
        
        # All object controls have been removed completely

        # Handle rotation animation with Q, W, E, R keys (only in gameplay phase)
        if self.current_phase == GamePhase.GAMEPLAY and not self.is_rotating:
            if self.input.is_key_down('q'):
                self.start_rotation_animation('x', 1)  # Positive X rotation
            elif self.input.is_key_down('e'):
                self.start_rotation_animation('x', -1)  # Negative X rotation (inverted Q)
            elif self.input.is_key_down('w'):
                self.start_rotation_animation('y', 1)  # Positive Y rotation
            elif self.input.is_key_down('r'):
                self.start_rotation_animation('y', -1)  # Negative Y rotation (inverted W)

        # Update rotation animation if active
        if self.is_rotating:
            self.update_rotation_animation()

        # Increment score by 100 when pressing A (kept for testing)
        if self.input.is_key_down('a'):
            self.score += 100
            print(f"Score: {self.score}")
            # Update score display text
            self.score_texture.update_text(f"Score: {int(self.score)}")
            
    def check_arrow_ring_collision(self, arrow):
        """
        Checks if an arrow is inside the ring.
        Returns:
        - 1: Arrow is completely inside the ring (both body and tip)
        - 0.5: Arrow is partially inside the ring (only part of body or tip)
        - 0: Arrow is outside the ring
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
        inner_radius = self.RING_INNER_RADIUS * self.RING_SCALE
        outer_radius = self.RING_OUTER_RADIUS * self.RING_SCALE
        
        # Get arrow's bounding rectangle
        min_x, min_z, max_x, max_z = arrow.get_bounding_rect()
        
        # Get arrow position
        arrow_pos = arrow.rig.local_position
        
        # IMPORTANT CORRECTION: The ring is vertical, so we need to check in the XZ plane
        # Calculate distance between arrow center and ring center
        dx = arrow_pos[0] - ring_pos[0]
        dz = arrow_pos[2] - ring_pos[2]  # Use Z coordinate for vertical ring
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
        
        # Check if arrow has passed the ring completely
        has_passed_ring = min_x > ring_pos[0] + outer_radius
        
        # Reset waiting state if arrow has passed the ring completely
        if has_passed_ring and hasattr(arrow, 'waiting_for_keypress') and arrow.waiting_for_keypress:
            arrow.waiting_for_keypress = False
            print(f"Arrow[{arrow.unique_id}]: Stopped waiting - passed ring completely")
        
        # First check if arrow has passed the ring without colliding
        if has_passed_ring:
            # If arrow is marked as scored, it collided at some point
            if hasattr(arrow, 'scored') and arrow.scored:
                # Return the previously determined score
                return arrow.collision_value if hasattr(arrow, 'collision_value') else 0
            else:
                # Arrow passed without colliding
                return 0
        
        # Determine collision status
        # Perfect hit: all corners of the bounding box are inside the inner ring
        all_corners_in_inner = all(dist < inner_radius for dist in corner_distances)
        
        # Partial hit: at least one corner is inside the outer ring
        any_corner_in_outer = any(dist < outer_radius for dist in corner_distances)
        
        # Calculate potential collision value
        if all_corners_in_inner:
            # Arrow is completely inside the inner ring (full interception)
            if hasattr(arrow, 'potential_collision_value') and arrow.potential_collision_value != 1:
                print(f"Arrow[{arrow.unique_id}]: Now fully inside ring (value: 1.0)")
            arrow.potential_collision_value = 1
        elif any_corner_in_outer:
            # Arrow is at least partially inside the ring (partial interception)
            if hasattr(arrow, 'potential_collision_value') and arrow.potential_collision_value != 0.5:
                if arrow.potential_collision_value == 1:
                    print(f"Arrow[{arrow.unique_id}]: Now touching outer ring (value: 0.5)")
                else:
                    print(f"Arrow[{arrow.unique_id}]: Now partially inside ring (value: 0.5)")
            arrow.potential_collision_value = 0.5
        else:
            # Arrow is completely outside the ring
            # If arrow was previously waiting, log that it's now outside ring
            if hasattr(arrow, 'potential_collision_value') and arrow.potential_collision_value > 0:
                print(f"Arrow[{arrow.unique_id}]: Now outside ring (value: 0)")
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
            
        # Only register a collision if all conditions are met:
        # 1. Arrow has a potential collision value > 0
        # 2. The correct arrow key is pressed
        # 3. Collision has not been checked while the key is pressed
        # 4. Arrow is eligible for detection (not ineligible)
        if (arrow.potential_collision_value > 0 and 
            correct_key_pressed and 
            not arrow.collision_checked and
            not (hasattr(arrow, 'ineligible_for_detection') and arrow.ineligible_for_detection)):
            # Debug print only essential collision information
            collision_type = "PERFECT" if arrow.potential_collision_value == 1 else "PARTIAL"
            print(f"COLLISION DETECTED - Arrow[{arrow.unique_id}]: {collision_type} (Value {arrow.potential_collision_value})")
            print(f"  Arrow bounds: ({min_x:.2f}, {min_z:.2f}) to ({max_x:.2f}, {max_z:.2f})")
            print(f"  Ring center: ({ring_pos[0]:.2f}, {ring_pos[2]:.2f}), Inner radius: {inner_radius:.2f}, Outer radius: {outer_radius:.2f}")
            
            # Mark that collision has been checked while key is pressed
            arrow.collision_checked = True
            # Store the collision value for scoring
            arrow.collision_value = arrow.potential_collision_value
            
            # Add this arrow to the processed list to prevent future changes
            if hasattr(arrow, 'unique_id') and arrow.unique_id not in self.processed_arrow_uuids:
                self.processed_arrow_uuids.append(arrow.unique_id)
                print(f"Arrow[{arrow.unique_id}]: Added to processed arrows list")
            
            # Debug mode: Pause the game to inspect collision    
            if self.debug_mode and not self.debug_paused:
                self.debug_paused = True
                self.debug_pause_timer = 0
                self.debug_pause_arrow = arrow
                pause_message = f"PAUSED: {collision_type} Hit (Press SPACE to resume)"
                self.collision_texture.update_text(pause_message)
                print(f"Game paused for {self.debug_pause_duration} seconds to inspect collision")
                
            return arrow.collision_value
        else:
            # Only print if potential collision exists and arrow is eligible
            if (arrow.potential_collision_value > 0 and 
                not (hasattr(arrow, 'ineligible_for_detection') and arrow.ineligible_for_detection)):
                # Initialize waiting_for_keypress flag if it doesn't exist
                if not hasattr(arrow, 'waiting_for_keypress'):
                    arrow.waiting_for_keypress = False
                    arrow.last_collision_value = 0
                
                # Simple non-registration reason, abbreviated
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
        # If we're paused in debug mode, don't update arrows
        if self.debug_mode and self.debug_paused:
            return
        
        # Atualiza todas as setas
        arrows_to_remove = []
        
        # Check if any arrow key is pressed (will be used for status display)
        is_arrow_key_pressed = (self.input.is_key_pressed('up') or 
                               self.input.is_key_pressed('down') or 
                               self.input.is_key_pressed('left') or 
                               self.input.is_key_pressed('right'))
        
        # Debug print when key state changes
        if not hasattr(self, 'prev_key_state'):
            self.prev_key_state = False
        
        if is_arrow_key_pressed != self.prev_key_state:
            print(f"Arrow key state changed: {'PRESSED' if is_arrow_key_pressed else 'RELEASED'}")
            self.prev_key_state = is_arrow_key_pressed
            
        # First update all arrows and find two nearest to ring
        ring_pos = self.target_ring.global_position
        arrow_distances = []
        
        # Track if we have a new arrow entering the waiting state
        new_waiting_arrow_found = False
        latest_waiting_arrow_id = None
        
        for i, arrow in enumerate(self.arrows):
            # Update arrow position
            arrow.update(delta_time)
            
            # Reset collision_checked flag when no arrow keys are pressed
            if not is_arrow_key_pressed and hasattr(arrow, 'collision_checked'):
                arrow.collision_checked = False
            
            # Calculate distance to ring
            arrow_pos = arrow.rig.local_position
            dx = arrow_pos[0] - ring_pos[0]
            dz = arrow_pos[2] - ring_pos[2]
            distance = math.sqrt(dx*dx + dz*dz)
            
            # Store arrow index and distance
            arrow_distances.append((i, distance, arrow))
            
            # Check if arrow should be removed
            if not arrow.isVisible():
                arrows_to_remove.append(i)
        
        # Sort arrows by distance to ring
        arrow_distances.sort(key=lambda x: x[1])
        
        # Only process the two nearest arrows
        nearest_arrows = arrow_distances[:2] if len(arrow_distances) >= 2 else arrow_distances
        
        # First pass to find if any arrow is entering the waiting state
        for idx, distance, arrow in nearest_arrows:
            # Skip this arrow if it's already been processed
            if hasattr(arrow, 'unique_id') and arrow.unique_id in self.processed_arrow_uuids:
                continue
                
            # Calculate flat distance to determine if arrow is near/in the ring
            arrow_pos = arrow.rig.local_position
            dx = arrow_pos[0] - ring_pos[0]
            dz = arrow_pos[2] - ring_pos[2]
            flat_distance = math.sqrt(dx*dx + dz*dz)
            
            # Get the outer radius of the ring
            outer_radius = self.RING_OUTER_RADIUS * self.RING_SCALE
            
            # Check if this arrow is entering the ring area
            is_near_ring = flat_distance <= outer_radius
            is_in_waiting = hasattr(arrow, 'waiting_for_keypress') and arrow.waiting_for_keypress
            
            # If arrow is near ring but not yet waiting, it's a new candidate
            if is_near_ring and not is_in_waiting and not hasattr(arrow, 'scored'):
                # Only consider this arrow if we don't already have a waiting arrow
                # or if this is the closest arrow to the ring
                if self.current_waiting_arrow_id is None or idx == 0:
                    new_waiting_arrow_found = True
                    latest_waiting_arrow_id = arrow.unique_id
                    break  # Only consider the first arrow that meets the criteria
        
        # If we found a new arrow entering waiting state, invalidate previous waiting arrows
        if new_waiting_arrow_found:
            # Set the new current waiting arrow ID
            self.current_waiting_arrow_id = latest_waiting_arrow_id
            
            # Mark all other arrows as ineligible - but ONLY those not already processed
            for arrow in self.arrows:
                if (arrow.unique_id != self.current_waiting_arrow_id and 
                    arrow.unique_id not in self.processed_arrow_uuids and
                    hasattr(arrow, 'waiting_for_keypress') and arrow.waiting_for_keypress):
                    arrow.waiting_for_keypress = False
                    arrow.ineligible_for_detection = True
                    print(f"Arrow[{arrow.unique_id}]: No longer waiting - newer arrow detected")
        
        # Process collision checks for arrows
        for idx, distance, arrow in nearest_arrows:
            # Skip arrows that have been marked as ineligible for detection
            if hasattr(arrow, 'ineligible_for_detection') and arrow.ineligible_for_detection:
                continue
                
            # Check for collision with ring
            collision_result = self.check_arrow_ring_collision(arrow)
            
            if collision_result > 0:
                # Update arrow visual feedback based on collision result
                if collision_result == 1:
                    # Calculate score multiplier based on current streak (BEFORE incrementing)
                    score_multiplier = 1.0
                    if self.perfect_streak >= 10:
                        score_multiplier = 2.0
                    elif self.perfect_streak >= 5:
                        score_multiplier = 1.5
                    
                    # Change arrow color to green for perfect hit
                    arrow.change_color([0.0, 1.0, 0.0]) # Green for 1.0
                    
                    # Update score only once per arrow
                    if not hasattr(arrow, 'scored') or not arrow.scored:
                        # Add score based on collision level with streak multiplier
                        score_increase = collision_result * 100 * score_multiplier
                        self.score += score_increase
                        
                        # Update score display
                        self.score_texture.update_text(f"Score: {int(self.score)}")
                        
                        # Mark arrow as scored so we don't count it multiple times
                        arrow.scored = True
                        print(f"Arrow[{arrow.unique_id}] scored: {score_increase} points (multiplier: x{score_multiplier}), total: {self.score}")
                        
                        # After scoring, reset current_waiting_arrow_id to allow next arrow to be detected
                        self.current_waiting_arrow_id = None
                    
                    # AFTER scoring, increment perfect streak for perfect hits
                    # Only increment streak if this arrow hasn't been counted before
                    if hasattr(arrow, 'unique_id') and arrow.unique_id not in self.streak_arrows:
                        self.perfect_streak += 1
                        self.streak_arrows.append(arrow.unique_id)
                        print(f"Perfect hit! Streak incremented to: {self.perfect_streak}")
                        
                        # Show streak with multiplier indicator for NEXT hit
                        multiplier_text = ""
                        if self.perfect_streak >= 10:
                            multiplier_text = " (x2.0)"
                        elif self.perfect_streak >= 5:
                            multiplier_text = " (x1.5)"
                        self.streak_texture.update_text(f"Streak: {self.perfect_streak}{multiplier_text}")
                    
                else: # collision_result must be 0.5 here
                    # No multiplier for partial hits
                    score_multiplier = 1.0
                    
                    # Change arrow color to yellow for partial hit
                    arrow.change_color([1.0, 1.0, 0.0]) # Yellow for 0.5
                    
                    # Update score only once per arrow
                    if not hasattr(arrow, 'scored') or not arrow.scored:
                        # Add score based on collision level with no multiplier
                        score_increase = collision_result * 100
                        self.score += score_increase
                        
                        # Update score display
                        self.score_texture.update_text(f"Score: {int(self.score)}")
                        
                        # Mark arrow as scored so we don't count it multiple times
                        arrow.scored = True
                        print(f"Arrow[{arrow.unique_id}] scored: {score_increase} points (no multiplier), total: {self.score}")
                        
                        # After scoring, reset current_waiting_arrow_id to allow next arrow to be detected
                        self.current_waiting_arrow_id = None
                    
                    # Reset perfect streak for partial hits
                    self.perfect_streak = 0
                    self.streak_arrows = []  # Clear tracked streak arrows
                    self.streak_texture.update_text(f"Streak: {self.perfect_streak}")
                    print(f"Partial hit! Streak reset to: {self.perfect_streak}")
            else:
                # Reset streak on misses
                if (hasattr(arrow, 'unique_id') and 
                    arrow.unique_id not in self.processed_arrow_uuids and
                    hasattr(arrow, 'waiting_for_keypress') and 
                    not arrow.waiting_for_keypress and
                    not hasattr(arrow, 'scored')):
                    # This is a missed arrow that's passed the ring
                    if self.perfect_streak > 0:
                        self.perfect_streak = 0
                        self.streak_arrows = []  # Clear tracked streak arrows
                        self.streak_texture.update_text(f"Streak: {self.perfect_streak}")
                        print("Streak reset due to miss!")
                
                # No need to update status display - we've removed it
                pass

        # Remove setas marcadas em ordem reversa
        for i in sorted(arrows_to_remove, reverse=True):
            if i < len(self.arrows):  # Verificação adicional de segurança
                arrow = self.arrows[i]
                # Log if arrow was in waiting state when removed
                if hasattr(arrow, 'waiting_for_keypress') and arrow.waiting_for_keypress:
                    print(f"Arrow[{arrow.unique_id}]: Stopped waiting (removed from scene)")
                # If this was the current waiting arrow, reset the ID
                if hasattr(arrow, 'unique_id') and self.current_waiting_arrow_id == arrow.unique_id:
                    self.current_waiting_arrow_id = None
                    
                # Only remove from processed list if arrow didn't score
                # We keep scored arrows in the list even after removal from scene
                if hasattr(arrow, 'unique_id') and arrow.unique_id in self.processed_arrow_uuids:
                    if not hasattr(arrow, 'scored') or not arrow.scored:
                        self.processed_arrow_uuids.remove(arrow.unique_id)
                        print(f"Removing Arrow[{arrow.unique_id}] from processed list (no score)")
                    else:
                        print(f"Keeping Arrow[{arrow.unique_id}] in processed list (scored)")
                        
                print(f"Removing Arrow[{arrow.unique_id}] from scene")
                self.arrows.pop(i)  # Remove da lista
                arrow.rig.parent.remove(arrow.rig)  # Remove da cena
                del arrow  # Remove da memória

    def handle_selection_input(self):
        # Check if left/right arrow keys are pressed to change selection
        key_pressed = False
        
        if self.input.is_key_down('left'):
            # Move selection left (with wrap-around)
            self.highlighted_index = (self.highlighted_index - 1) % len(self.object_rigs)
            key_pressed = True
            
        if self.input.is_key_down('right'):
            # Move selection right (with wrap-around)
            self.highlighted_index = (self.highlighted_index + 1) % len(self.object_rigs)
            key_pressed = True
            
        # Update the highlighted object if a key was pressed
        if key_pressed:
            self.highlight_selected_object()
            
        # Check if Enter key is pressed to confirm selection
        if self.input.is_key_down('return'):
            # Set the active object to the currently highlighted one
            self.active_object_rig = self.object_rigs[self.highlighted_index]
            
            # Transition to gameplay phase
            self.setup_gameplay_phase()
            self.current_phase = GamePhase.GAMEPLAY
            
    def create_single_arrow(self, arrow_type_str=None): # Modified to accept arrow_type_str
        """Cria uma única seta com orientação especificada ou aleatória."""
        import random
        import uuid
        
        angle = 0 # Default angle
        
        if arrow_type_str:
            arrow_type_str_lower = arrow_type_str.lower()
            if arrow_type_str_lower in self.ARROW_TYPE_NAMES:
                angle = self.ARROW_TYPE_NAMES[arrow_type_str_lower]
            else:
                print(f"Warning: Unknown arrow_type_str '{arrow_type_str}' in create_single_arrow. Defaulting to UP (0 degrees).")
                angle = self.ARROW_TYPE_UP # Default to UP if type is unknown
        else:
            # If no type specified, choose a random one (optional, consider if this case is still needed)
            possible_angles = [self.ARROW_TYPE_UP, self.ARROW_TYPE_LEFT, self.ARROW_TYPE_DOWN, self.ARROW_TYPE_RIGHT]
            angle = random.choice(possible_angles)
            print(f"Warning: create_single_arrow called without arrow_type_str. Spawning random arrow (angle: {angle}).")

        # Print debug mode before creating arrow
        print(f"\n==== Creating arrow with debug_mode = {self.debug_mode} ====\n")
        
        # Pass debug_mode flag from the base class
        arrow = Arrow(color=[1.0, 0.0, 0.0], offset=[0, 0, 0], debug_mode=self.debug_mode)
        arrow.add_to_scene(self.scene)
        arrow.rotate(math.radians(angle), 'z') # Rotate based on the determined angle
        
        # ARROW_START_POSITION is imported from config.py
        arrow.set_position(ARROW_START_POSITION) 
        
        arrow.unique_id = str(uuid.uuid4())
        
        return arrow

    def setup_arrow_spawning(self, interval=2.0): # This method might become obsolete or repurposed
        """Configura o spawn automático de setas a cada intervalo (OLD METHOD - TO BE REPLACED)"""
        self.arrows = [] # Ensure arrows list is initialized here if not elsewhere for gameplay phase start
        # self.arrow_spawn_timer = 0 # Not needed for keyframe system
        # self.arrow_spawn_interval = interval # Not needed for keyframe system
        
        # Initialize the current waiting arrow ID
        self.current_waiting_arrow_id = None
        print("INFO: setup_arrow_spawning called. Ensure this is intended if using keyframe system.")

    def update_arrow_spawning(self, delta_time): # THIS ENTIRE METHOD IS NOW OBSOLETE
        """Atualiza o timer e cria novas setas quando necessário (OLD METHOD - OBSOLETE)"""
        # This logic is replaced by update_keyframe_arrows
        # self.arrow_spawn_timer += delta_time
        # if self.arrow_spawn_timer >= self.arrow_spawn_interval:
        #     self.arrow_spawn_timer = 0
        #     self.arrows.append(self.create_single_arrow()) # Old random spawning
        pass # Does nothing now

    def update_keyframe_arrows(self):
        """Check if it's time to spawn arrows according to keyframes and music time."""
        if not hasattr(self, 'keyframes') or not self.keyframes or self.current_keyframe_index >= len(self.keyframes):
            return # No keyframes loaded or all keyframes processed

        if not hasattr(self, 'arrow_travel_time'):
            print("Error: arrow_travel_time not calculated. Cannot spawn keyframe arrows accurately.")
            return

        current_music_time = self.get_music_time()

        # Process all keyframes that should have spawned by now
        while (self.current_keyframe_index < len(self.keyframes) and
               current_music_time >= (self.keyframes[self.current_keyframe_index]['time'] - self.arrow_travel_time)):
            
            keyframe = self.keyframes[self.current_keyframe_index]
            arrow_type_to_spawn = keyframe.get('arrow_type') # Already validated in load_keyframes

            print(f"Spawning arrow for keyframe {self.current_keyframe_index}: time {keyframe['time']:.2f}s, type '{arrow_type_to_spawn}', music_time: {current_music_time:.2f}s")
            
            new_arrow = self.create_single_arrow(arrow_type_str=arrow_type_to_spawn)
            if not hasattr(self, 'arrows'): # Ensure self.arrows exists
                self.arrows = []
            self.arrows.append(new_arrow)
            
            self.current_keyframe_index += 1

    def handle_nightClub(self):
        self.nightClub = nightclub.NightClub(self.scene,"geometry/nightClub.obj", [0, -2.5, 10], 3)
        self.nightClub_rig = self.nightClub.get_rig()
        self.scene.add(self.nightClub_rig)

    # Music Playback Methods
    def initialize_music(self):
        """Initialize pygame mixer"""
        try:
            pygame.mixer.init()
            print("Pygame mixer initialized successfully")
            self.music_loaded = False
            self.music_playing = False
            self.music_start_time = 0
            self.music_file = None
        except Exception as e:
            print(f"Error initializing pygame mixer: {e}")

    def load_music(self, music_file):
        """Load a specific music file"""
        import pygame
        try:
            print(f"Attempting to load music file: {music_file}")
            pygame.mixer.music.load(music_file)
            pygame.mixer.music.set_volume(0.2)  # Set volume to 30%
            self.music_loaded = True
            self.music_file = music_file
            print(f"Successfully loaded music file: {music_file}")
            return True
        except pygame.error as e:
            print(f"Error loading music '{music_file}': {e}")
            self.music_loaded = False
            self.music_file = None
            return False
            
    def play_music(self):
        """Start music playback and record start time"""
        import pygame
        import time
        if self.music_loaded:
            try:
                print(f"Attempting to play music: {self.music_file}")
                pygame.mixer.music.play()
                self.music_playing = True
                self.music_start_time = time.time()
                self.current_keyframe_index = 0
                print(f"Music playback started. Start time: {self.music_start_time}")
                return True
            except Exception as e:
                print(f"Error playing music: {e}")
                return False
        print("Music not loaded, cannot play.")
        return False

    def apply_timing_adjustment(self, time_value):
        """Apply timing adjustment to a given time value"""
        return time_value + self.timing_adjustment

    def calibrate_arrow_timing(self, adjustment_seconds):
        """Adjust arrow timing by specified amount in seconds"""
        self.timing_adjustment = adjustment_seconds
        print(f"Timing adjustment set to: {self.timing_adjustment} seconds")
           
    def get_music_time(self):
        """Get current music playback position in seconds with calibration adjustment"""
        import time
        if not self.music_playing or not hasattr(self, 'music_start_time'): # Added check for music_start_time
            return 0
        
        # Calculate raw music time
        current_raw_time = time.time() - self.music_start_time
        
        # Apply calibration adjustment
        adjusted_time = self.apply_timing_adjustment(current_raw_time)
        # print(f"Raw music time: {current_raw_time:.2f}s, Adjusted music time: {adjusted_time:.2f}s") # Optional: for debugging
        return adjusted_time

    # Keyframe Loading Method
    def load_keyframes(self, keyframe_file):
        """Load keyframe data from JSON file"""
        try:
            with open(keyframe_file, 'r') as file:
                keyframes_data = json.load(file)
            
            # Validate and process keyframes
            self.keyframes = []
            for i, keyframe in enumerate(keyframes_data):
                if 'time' not in keyframe:
                    raise ValueError(f"Keyframe {i} in '{keyframe_file}' missing 'time' field.")
                if 'arrow_type' not in keyframe:
                    # Making arrow_type a required field
                    raise ValueError(f"Keyframe {i} in '{keyframe_file}' missing 'arrow_type' field.")
                if not isinstance(keyframe['arrow_type'], str) or keyframe['arrow_type'].lower() not in self.ARROW_TYPE_NAMES:
                    valid_types = ", ".join(self.ARROW_TYPE_NAMES.keys())
                    raise ValueError(f"Keyframe {i} in '{keyframe_file}' has invalid 'arrow_type': '{keyframe['arrow_type']}'. Valid types are: {valid_types}.")
                
                # Store the original string type for now, will be resolved at creation
                self.keyframes.append({'time': float(keyframe['time']), 'arrow_type': keyframe['arrow_type']})
                   
            # Sort keyframes by time
            self.keyframes.sort(key=lambda k: k['time'])
            self.current_keyframe_index = 0 # Reset index when new keyframes are loaded
            print(f"Keyframes from '{keyframe_file}' loaded and sorted successfully ({len(self.keyframes)} keyframes).")
            return True
        except FileNotFoundError:
            print(f"Error loading keyframes: File '{keyframe_file}' not found.")
            self.keyframes = [] # Ensure keyframes list is empty on error
            return False
        except json.JSONDecodeError as e:
            print(f"Error loading keyframes: JSON decoding error in '{keyframe_file}': {e}")
            self.keyframes = []
            return False
        except ValueError as e: # Catch our custom validation errors
            print(f"Error loading keyframes: Data validation error in '{keyframe_file}': {e}")
            self.keyframes = []
            return False
        except Exception as e:
            print(f"Error loading keyframes from '{keyframe_file}': {e}")
            self.keyframes = []
            return False

    def add_ring_debug_visualization(self):
        """Add visual indicators for the inner and outer ring boundaries for debugging"""
        # The ring is actually created in the XY plane (horizontal), but appears vertical due to camera
        def circle_function(u, v):
            # v parameter is not used for a simple circle
            x = self.RING_INNER_RADIUS * np.cos(u * 2 * np.pi)
            y = self.RING_INNER_RADIUS * np.sin(u * 2 * np.pi)  # Keep in XY plane (same as actual ring)
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
        self.inner_circle_mesh.set_position(self.RING_POSITION)
        self.inner_circle_mesh.scale(self.RING_SCALE)  # Apply the same scale as the ring
        
        # Add inner circle to the scene
        self.scene.add(self.inner_circle_mesh)
        
        # Also add small squares at key positions for the collision detection algorithm
        self.add_collision_point_markers()
        
        # Add an explanation text for debug mode
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

    def add_collision_point_markers(self):
        """Add visual markers for the collision detection points"""
        # Create a small rectangle geometry for the markers
        from geometry.rectangle import RectangleGeometry
        
        # Create materials for different types of markers
        inner_marker_material = SurfaceMaterial(
            property_dict={
                "baseColor": [1, 0, 0, 1],  # Red for inner ring boundary
                "doubleSide": True
            }
        )
        
        outer_marker_material = SurfaceMaterial(
            property_dict={
                "baseColor": [0, 0, 1, 1],  # Blue for outer ring boundary
                "doubleSide": True
            }
        )
        
        # Define the ring center for reference
        ring_center = self.RING_POSITION
        inner_radius = self.RING_INNER_RADIUS * self.RING_SCALE
        outer_radius = self.RING_OUTER_RADIUS * self.RING_SCALE
        
        # Create small markers at key points on inner and outer ring
        marker_size = 0.05
        marker_positions = []
        
        # Add markers at four cardinal points on inner circle
        # Ring is actually in the XY plane (horizontal), but appears vertical due to camera
        for angle in [0, math.pi/2, math.pi, 3*math.pi/2]:
            x = ring_center[0] + inner_radius * math.cos(angle)
            y = ring_center[1] + inner_radius * math.sin(angle)  # Use Y for XY plane orientation
            marker_positions.append((x, y, ring_center[2], inner_marker_material, "inner"))
            
        # Add markers at four cardinal points on outer circle
        for angle in [0, math.pi/2, math.pi, 3*math.pi/2]:
            x = ring_center[0] + outer_radius * math.cos(angle)
            y = ring_center[1] + outer_radius * math.sin(angle)  # Use Y for XY plane orientation
            marker_positions.append((x, y, ring_center[2], outer_marker_material, "outer"))
            
        # Create and position all markers
        self.marker_meshes = []
        for i, (x, y, z, material, marker_type) in enumerate(marker_positions):
            marker_geometry = RectangleGeometry(width=marker_size, height=marker_size)
            marker_mesh = Mesh(marker_geometry, material)
            marker_mesh.set_position([x, y, z])
            
            # Add a text label to the marker
            label = f"{marker_type}_{i % 4}"
            print(f"Adding marker: {label} at position: ({x:.2f}, {y:.2f}, {z:.2f})")
            
            self.scene.add(marker_mesh)
            self.marker_meshes.append(marker_mesh)

    def start_rotation_animation(self, axis, direction=1):
        """
        Start a 360° rotation animation around the specified axis.
        
        Parameters:
            axis (str): 'x', 'y', or 'z' - the axis to rotate around
            direction (int): 1 for clockwise, -1 for counter-clockwise
        """
        if not self.is_rotating:  # Only start if not already rotating
            self.is_rotating = True
            self.rotation_start_time = time.time()
            self.rotation_axis = axis
            self.rotation_direction = direction  # Store rotation direction
            
            # Store original rotation for restoration
            # We'll use the current matrix as our reference state
            if hasattr(self, 'active_object_rig') and self.active_object_rig:
                # Create a copy of the current transform matrix
                self.original_matrix = self.active_object_rig._matrix.copy()
    
    def update_rotation_animation(self):
        """
        Update the rotation animation based on elapsed time.
        Completes a 360° rotation and returns to original orientation.
        """
        if not hasattr(self, 'active_object_rig') or not self.active_object_rig:
            self.is_rotating = False
            return
            
        # Calculate elapsed time and progress
        current_time = time.time()
        elapsed_time = current_time - self.rotation_start_time
        
        # Normalize progress to [0, 1] range
        progress = min(1.0, elapsed_time / self.rotation_duration)
        
        # Calculate current rotation angle (full 360°), applying direction
        current_angle = progress * self.total_rotation_angle * self.rotation_direction
        
        # Reset to the original matrix
        self.active_object_rig._matrix = self.original_matrix.copy()
        
        # Apply the animation rotation on top of the original position
        if self.rotation_axis == 'x':
            self.active_object_rig.rotate_x(current_angle)
        elif self.rotation_axis == 'y':
            self.active_object_rig.rotate_y(current_angle)
        elif self.rotation_axis == 'z':
            self.active_object_rig.rotate_z(current_angle)
        
        # Check if animation is complete
        if progress >= 1.0:
            self.is_rotating = False
            # Reset to original state
            self.active_object_rig._matrix = self.original_matrix.copy()

Example(screen_size=SCREEN_SIZE).run()




                    
                    