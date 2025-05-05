import math
from nt import remove
import pathlib
import sys
import pygame
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

class GamePhase(Enum):
    SELECTION = auto()
    GAMEPLAY = auto()

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
    """
    def initialize(self):
        print("Initializing program...")
        print("\nInstruções de Controlo:")
        print("Fase de Seleção:")
        print("- Setas Esquerda/Direita: Selecionar objeto")
        print("- Enter: Confirmar seleção e passar para fase de jogo")
        print("\nFase de Jogo:")
        print("Controlo dos Objectos:")
        print("- Setas: Mover o objecto para a frente/esquerda/trás/direita")
        print("- UO: Rodar o objecto para a esquerda/direita")
        print("- KL: Inclinar o objecto para cima/para baixo")
        print("\nNota: A câmara está agora em modo automático.")

        # Initialize game phase
        self.current_phase = GamePhase.SELECTION
        self.highlighted_index = 0
        
        # Initialize score
        self.score = 0
        
        # Camera animation properties - initial setup for gameplay phase
        self.camera_hardcoded_position = [0, 1.2, 7]  # X, Y, Z
        self.camera_hardcoded_rotation = [0, -math.pi/2, 0]  # X, Y, Z rotations in radians
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
        
        # Create collision status display
        collision_texture = TextTexture(
            text="Status: --",
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
        collision_material = TextureMaterial(texture=collision_texture, property_dict={"doubleSide": True})
        collision_geometry = RectangleGeometry(width=2, height=0.6)
        self.collision_mesh = Mesh(collision_geometry, collision_material)
        
        # Create the collision status rig
        self.collision_rig = MovementRig()
        self.collision_rig.add(self.collision_mesh)
        # Position collision status below score
        self.collision_rig.set_position([2.6, 0.7, -3])
        
        # Store the collision texture for updates
        self.collision_texture = collision_texture
        
        # Create the score rig but don't add to scene directly - will be added to camera
        self.score_rig = MovementRig()
        self.score_rig.add(self.score_mesh)
        self.score_rig.add(self.collision_mesh)
        # Position score relative to camera view
        self.score_rig.set_position([2.6, 1.3, -3])
        
        # Store the score texture for updates
        self.score_texture = score_texture
        
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
        
        # behind_z = -5
        axes = AxesHelper(axis_length=2)
        self.scene.add(axes)
        grid = GridHelper(
            size=20,
            grid_color=[1, 1, 1],
            center_color=[1, 1, 0]
        )
        grid.rotate_x(-math.pi / 2)
        self.setup_arrow_spawning(2.0)
        self.handle_nightClub()

        # Ring (target circle)
        ring_geometry = RingGeometry(inner_radius=0.4, outer_radius=0.5, segments=32) # Adjust radii as needed
        self.target_ring = Mesh(ring_geometry, SurfaceMaterial(property_dict={"baseColor": [0, 1, 0], "doubleSide": True}))
        self.target_ring.scale(1.5) # Scale the ring up by 50%
        self.target_ring.translate(1.3, -0.03, 5) # Place slightly above the ground plane
        self.target_ring.rotate_x(0) # Rotate to lie flat on XZ plane

        self.scene.add(self.target_ring)

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
        print(f"Score: {self.score}")
        # Update score display text
        self.score_texture.update_text(f"Score: {self.score}")
        
        self.remove_highlighting()
        self.active_object_rig._matrix = Matrix.make_identity()
        self.active_object_rig.set_position([0, 0, 0])
        
        # Get the index of the selected instrument
        selected_index = self.object_rigs.index(self.active_object_rig)
        
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
        final_position = [-3, 1.2, 12.5]
        final_rotation = [0, -math.pi/4, 0]
        
        # Time to reach final position (in seconds)
        transition_time = 4.0
        
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
            # Update camera animation
            self.update_camera_animation()
            self.handle_arrows(self.delta_time)
        
        self.renderer.render(self.scene, self.camera)

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
    
    def handle_gameplay_input(self):
        # Camera is now hardcoded and no longer controlled manually
        
        # Update camera animation time for future use in time-based camera animation
        self.camera_animation_time += self.delta_time
        
        # Object movement with arrow keys and other controls
        move_amount = 2 * self.delta_time
        rotate_amount = 1 * self.delta_time
        
        # Translation with arrow keys affects the active object
        if self.input.is_key_pressed('left'):
            self.active_object_rig.translate(-move_amount, 0, 0)
        if self.input.is_key_pressed('right'):
            self.active_object_rig.translate(move_amount, 0, 0)
        if self.input.is_key_pressed('up'):
            self.active_object_rig.translate(0, 0, -move_amount)
        if self.input.is_key_pressed('down'):
            self.active_object_rig.translate(0, 0, move_amount)

        # Rotation with UO affects the active object
        if self.input.is_key_pressed('u'):
            self.active_object_rig.rotate_y(rotate_amount)
        if self.input.is_key_pressed('o'):
            self.active_object_rig.rotate_y(-rotate_amount)

        # Tilt with KL affects the active object
        if self.input.is_key_pressed('k'):
            self.active_object_rig.rotate_x(rotate_amount)
        if self.input.is_key_pressed('l'):
            self.active_object_rig.rotate_x(-rotate_amount)
            
        # Increment score by 100 when pressing A
        if self.input.is_key_down('a'):
            self.score += 100
            print(f"Score: {self.score}")
            # Update score display text
            self.score_texture.update_text(f"Score: {self.score}")

    def create_single_arrow(self):
        """Cria uma única seta com orientação aleatória, considerando offset de origem"""
        import random
        possible_angles = [0, 90, 180, 270, 360, 90, 270]
        angle = random.choice(possible_angles)
        
        arrow = Arrow(color=[1.0, 0.0, 0.0], offset=[-0.5, 0, 0])  # Offset para compensar origem não central
        arrow.add_to_scene(self.scene)
        arrow.rotate(math.radians(angle), 'z')
        
        # Hardcoded position for arrows
        arrow_x = -3 # Starting X position (left side)
        arrow_y = 0    # Fixed Y position
        arrow_z = 8    # Fixed Z position
        # Set arrow at hardcoded position
        arrow.set_position([arrow_x, arrow_y, arrow_z])
        
        return arrow

    def setup_arrow_spawning(self, interval=2.0):
        """Configura o spawn automático de setas a cada intervalo"""
        self.arrows = []
        self.arrow_spawn_timer = 0
        self.arrow_spawn_interval = interval

    def update_arrow_spawning(self, delta_time):
        """Atualiza o timer e cria novas setas quando necessário"""
        self.arrow_spawn_timer += delta_time
        if self.arrow_spawn_timer >= self.arrow_spawn_interval:
            self.arrow_spawn_timer = 0
            self.arrows.append(self.create_single_arrow())

    def check_arrow_ring_collision(self, arrow, arrow_index):
        """
        Checks if an arrow is inside the ring.
        Returns:
        - 1: Arrow is completely inside the ring (both body and tip)
        - 0.5: Arrow is partially inside the ring (only part of body or tip)
        - 0: Arrow is outside the ring
        """
        # Get positions of arrow and ring
        arrow_pos = arrow.rig.local_position
        ring_pos = self.target_ring.global_position
        
        # First check if arrow has passed the ring without colliding
        # If the arrow is already more than 0.5 units past the ring on the X axis, it can no longer collide
        if arrow_pos[0] > ring_pos[0] + 0.5:
            # If arrow is marked as scored, it collided at some point
            if hasattr(arrow, 'scored') and arrow.scored:
                # Return the previously determined score
                return arrow.collision_value if hasattr(arrow, 'collision_value') else 0
            else:
                # Arrow passed without colliding
                return 0
        
        # Calculate distance between arrow center and ring center
        dx = arrow_pos[0] - ring_pos[0]
        dy = arrow_pos[1] - ring_pos[1]
        dz = arrow_pos[2] - ring_pos[2]
        
        # Calculate flat distance (considering only X and Z planes, as the game is essentially planar)
        flat_distance = math.sqrt(dx*dx + dz*dz)
        
        # Get the inner and outer radius of the ring, adjusted by the scale factor
        inner_radius = 0.4 * 1.5  # Original inner_radius * scale
        outer_radius = 0.5 * 1.5  # Original outer_radius * scale
        
        # Get dimensions of arrow parts
        # These values should match those in the Arrow class
        body_width = 0.2 * 0.8  # width * size from Arrow class
        body_height = 0.6 * 0.8  # height * size from Arrow class
        tip_radius = 0.3 * 0.8   # radius * size from Arrow class
        
        # Maximum extent of arrow from its center point
        # This is half the width of the body and the radius of the tip
        arrow_max_extent = max(body_width/2, tip_radius)
        
        # Calculate arrow bounds for debugging
        arrow_min_x = arrow_pos[0] - arrow_max_extent
        arrow_max_x = arrow_pos[0] + arrow_max_extent
        arrow_min_z = arrow_pos[2] - arrow_max_extent
        arrow_max_z = arrow_pos[2] + arrow_max_extent
        
        # Calculate ring bounds for debugging
        ring_min_x = ring_pos[0] - outer_radius
        ring_max_x = ring_pos[0] + outer_radius
        ring_min_z = ring_pos[2] - outer_radius
        ring_max_z = ring_pos[2] + outer_radius
        
        # Calculate potential collision value
        if flat_distance + arrow_max_extent <= inner_radius:
            # Arrow is completely inside the inner ring (full interception)
            arrow.potential_collision_value = 1
        elif flat_distance <= outer_radius:
            # Arrow is at least partially inside the ring (partial interception)
            arrow.potential_collision_value = 0.5
        else:
            # Arrow is completely outside the ring
            arrow.potential_collision_value = 0
            
        # Check if any arrow key is pressed
        is_arrow_key_pressed = (self.input.is_key_pressed('up') or 
                               self.input.is_key_pressed('down') or 
                               self.input.is_key_pressed('left') or 
                               self.input.is_key_pressed('right'))
        
        # Initialize collision checked flag if it doesn't exist
        if not hasattr(arrow, 'collision_checked'):
            arrow.collision_checked = False
            
        # Only register a collision if all conditions are met:
        # 1. Arrow has a potential collision value > 0
        # 2. An arrow key is pressed
        # 3. Collision has not been checked while the key is pressed
        if arrow.potential_collision_value > 0 and is_arrow_key_pressed and not arrow.collision_checked:
            # Debug print only essential collision information
            print(f"COLLISION DETECTED - Arrow[{arrow_index}]: Value {arrow.potential_collision_value}")
            print(f"  Arrow X,Z: ({arrow_pos[0]:.2f}, {arrow_pos[2]:.2f}), Ring X,Z: ({ring_pos[0]:.2f}, {ring_pos[2]:.2f})")
            print(f"  Distance: {flat_distance:.2f}, Arrow extent: {arrow_max_extent:.2f}, Ring radius: {outer_radius:.2f}")
            
            # Mark that collision has been checked while key is pressed
            arrow.collision_checked = True
            # Store the collision value for scoring
            arrow.collision_value = arrow.potential_collision_value
            return arrow.collision_value
        else:
            # Only print if potential collision exists
            if arrow.potential_collision_value > 0:
                # Simple non-registration reason, abbreviated
                if is_arrow_key_pressed and arrow.collision_checked:
                    print(f"Arrow[{arrow_index}]: Waiting for key release (already checked)")
                elif arrow.potential_collision_value > 0 and not is_arrow_key_pressed:
                    print(f"Arrow[{arrow_index}]: Waiting for key press (value: {arrow.potential_collision_value})")
            
            # No collision registered
            return 0
    
    def handle_arrows(self, delta_time):
        # Atualiza spawn de setas
        self.update_arrow_spawning(self.delta_time)

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
        
        for i, arrow in enumerate(self.arrows):
            # Update arrow position
            arrow.update()
            
            # Reset collision_checked flag when no arrow keys are pressed
            if not is_arrow_key_pressed and hasattr(arrow, 'collision_checked'):
                arrow.collision_checked = False
            
            # Calculate distance to ring
            arrow_pos = arrow.rig.local_position
            dx = arrow_pos[0] - ring_pos[0]
            dz = arrow_pos[2] - ring_pos[2]
            distance = math.sqrt(dx*dx + dz*dz)
            
            # Store arrow index and distance
            arrow_distances.append((i, distance))
            
            # Check if arrow should be removed
            if not arrow.isVisible():
                arrows_to_remove.append(i)
        
        # Sort arrows by distance to ring
        arrow_distances.sort(key=lambda x: x[1])
        
        # Only process the two nearest arrows
        nearest_arrows = arrow_distances[:2] if len(arrow_distances) >= 2 else arrow_distances
        
        # Process only the nearest arrows
        for idx, distance in nearest_arrows:
            arrow = self.arrows[idx]
            
            # Check for collision with ring
            collision_result = self.check_arrow_ring_collision(arrow, idx)
            
            if collision_result > 0:
                # Update the collision status display
                if collision_result == 1:
                    status_text = "Status: 1.0 (Perfect!)"
                    # Change arrow color to gold for perfect hit
                    arrow.change_color([1.0, 0.84, 0.0])
                else:
                    status_text = "Status: 0.5 (Partial)"
                    # Change arrow color to green for partial hit
                    arrow.change_color([0.0, 1.0, 0.0])
                
                self.collision_texture.update_text(status_text)
                
                # Update score only once per arrow
                if not hasattr(arrow, 'scored') or not arrow.scored:
                    # Add score based on collision level
                    self.score += collision_result * 100
                    # Update score display
                    self.score_texture.update_text(f"Score: {self.score}")
                    # Mark arrow as scored so we don't count it multiple times
                    arrow.scored = True
                    print(f"Arrow[{idx}] scored: {collision_result * 100} points, total: {self.score}")
            else:
                # If no collision and arrow is far enough to be past the ring
                if arrow.rig.local_position[0] > ring_pos[0] + 0.5:
                    # Update status to show miss
                    self.collision_texture.update_text("Status: 0 (Miss)")
                # If we have a potential collision but no arrow key is pressed
                elif hasattr(arrow, 'potential_collision_value') and arrow.potential_collision_value > 0 and not is_arrow_key_pressed:
                    # Show that an arrow key needs to be pressed
                    self.collision_texture.update_text("Status: Press Arrow Key!")

        # Remove setas marcadas em ordem reversa
        for i in sorted(arrows_to_remove, reverse=True):
            if i < len(self.arrows):  # Verificação adicional de segurança
                print(f"Removing Arrow[{i}] from scene")
                arrow = self.arrows.pop(i)  # Remove da lista
                arrow.rig.parent.remove(arrow.rig)  # Remove da cena
                del arrow  # Remove da memória

    def handle_nightClub(self):
        self.nightClub = nightclub.NightClub(self.scene,"geometry/nightClub.obj", [0, -2.5, 10], 3)
        self.nightClub_rig = self.nightClub.get_rig()
        self.scene.add(self.nightClub_rig)

Example(screen_size=[1280, 720]).run()




                    
                    