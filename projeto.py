import numpy as np
import math
import pathlib
import sys
from enum import Enum, auto

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
        print("Controlo da Câmara:")
        print("- WASD: Mover a câmara para a frente/esquerda/trás/direita")
        print("- RF: Mover a câmara para cima/para baixo")
        print("- QE: Virar a câmara para a esquerda/direita")
        print("- TG: Olhar para cima/para baixo")
        print("\nControlo dos Objectos:")
        print("- Setas: Mover o objecto para a frente/esquerda/trás/direita")
        print("- UO: Rodar o objecto para a esquerda/direita")
        print("- KL: Inclinar o objecto para cima/para baixo")

        # Initialize game phase
        self.current_phase = GamePhase.SELECTION
        self.highlighted_index = 0
        
        self.renderer = Renderer()
        self.scene = Scene()
        self.camera = Camera(aspect_ratio=1280/720)
        
        # Set up camera rig for movement
        self.camera_rig = MovementRig()
        self.camera_rig.add(self.camera)
        self.scene.add(self.camera_rig)

        # Common texture for now
        metal_texture = Texture(file_name="images/miguelJPG.jpg")
        material = TextureMaterial(texture=metal_texture)
        
        # Load Miguel's object (using the same OBJ for now)
        positions_miguel, uvs_miguel = my_obj_reader2("geometry/miguelOBJ.obj") 
        geometry_miguel = MiguelGeometry(1, 1, 1, positions_miguel, uvs_miguel)
        self.mesh_miguel = Mesh(geometry_miguel, material)
        self.object_rig_miguel = MovementRig()
        self.object_rig_miguel.add(self.mesh_miguel)
        self.object_rig_miguel.set_position([-3, 0, 0]) # Position Miguel
        self.scene.add(self.object_rig_miguel)

        # Load Ze's object (using the same OBJ for now)
        positions_ze, uvs_ze = my_obj_reader2("geometry/miguelOBJ.obj") # TODO: Replace with zeOBJ.obj later
        geometry_ze = ZeGeometry(1, 1, 1, positions_ze, uvs_ze) # Use ZeGeometry
        self.mesh_ze = Mesh(geometry_ze, material)
        self.object_rig_ze = MovementRig()
        self.object_rig_ze.add(self.mesh_ze)
        self.object_rig_ze.set_position([-1, 0, 0]) # Position Ze
        self.scene.add(self.object_rig_ze)

        # Load Ana's object (using the same OBJ for now)
        positions_ana, uvs_ana = my_obj_reader2("geometry/miguelOBJ.obj") # TODO: Replace with anaOBJ.obj later
        geometry_ana = AnaGeometry(1, 1, 1, positions_ana, uvs_ana) # Use AnaGeometry
        self.mesh_ana = Mesh(geometry_ana, material)
        self.object_rig_ana = MovementRig()
        self.object_rig_ana.add(self.mesh_ana)
        self.object_rig_ana.set_position([1, 0, 0]) # Position Ana
        self.scene.add(self.object_rig_ana)

        # Load Brandon's object (using the same OBJ for now)
        positions_brandon, uvs_brandon = my_obj_reader2("geometry/miguelOBJ.obj") # TODO: Replace with brandonOBJ.obj later
        geometry_brandon = BrandonGeometry(1, 1, 1, positions_brandon, uvs_brandon) # Use BrandonGeometry
        self.mesh_brandon = Mesh(geometry_brandon, material)
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
        
        axes = AxesHelper(axis_length=2)
        self.scene.add(axes)
        grid = GridHelper(
            size=20,
            grid_color=[1, 1, 1],
            center_color=[1, 1, 0]
        )
        grid.rotate_x(-math.pi / 2)
        self.scene.add(grid)
        
    def setup_selection_phase(self):
        # Reset camera transform first
        self.camera_rig._matrix = Matrix.make_identity()
        # Position camera high up and facing "backwards" and see all objects
        objects_y = 100 # Set the Y coordinate for the objects
        camera_y = objects_y + 5 # Position camera slightly above objects
        self.camera_rig.set_position([0.5, camera_y, 15]) # Use camera_y for camera, move closer (Z=15)
        
        # Reset all objects to their original positions and rotations with increased spacing, high up
        positions = [[-4.5, objects_y, 0], [-1.5, objects_y, 0], [1.5, objects_y, 0], [4.5, objects_y, 0]] # Use objects_y for objects
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
        # Position camera to face "forward"
        # Reset camera transform before setting position
        self.camera_rig._matrix = Matrix.make_identity()
        self.camera_rig.set_position([0.5, 1, 10])
        
        # Remove highlighting before moving objects
        self.remove_highlighting()
        
        # Move selected object to center
        # Reset transform before setting position
        self.active_object_rig._matrix = Matrix.make_identity()
        self.active_object_rig.set_position([0, 0, 0])

        # Move other objects behind the selected one, centered and more separated
        behind_z = -5  # Z position behind the selected object
        side_positions = [[-5, 0, behind_z], [0, 0, behind_z], [5, 0, behind_z]] # Increased separation

        # Keep track of which position to use for non-active objects
        pos_index = 0

        # Position the non-selected objects
        for rig in self.object_rigs:
            if rig != self.active_object_rig:
                # Reset transform before setting position
                rig._matrix = Matrix.make_identity()
                # Assign one of the predefined side positions
                rig.set_position(side_positions[pos_index])
                pos_index += 1 # Move to the next position for the next non-active object
    
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

    def update(self):
        if self.current_phase == GamePhase.SELECTION:
            # Handle input for selection phase
            self.handle_selection_input()
            
            # Render scene with current camera
            self.renderer.render(self.scene, self.camera)
            
        elif self.current_phase == GamePhase.GAMEPLAY:
            # Handle input for gameplay phase
            self.handle_gameplay_input()
            
            # Render scene with current camera
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
        # Camera movement with WASDRF, QE, TG
        self.camera_rig.update(self.input, self.delta_time)
        
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

Example(screen_size=[1280, 720]).run()