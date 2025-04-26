import numpy as np
import math
import pathlib
import sys

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


class Example(Base):
    """
    Render the axes and the rotated xy-grid.
    Features both camera and object movement controls.
    Camera: WASDRF(move), QE(turn), TG(look)
    Object: Arrow keys(move), UO(turn), KL(tilt)
    """
    def initialize(self):
        print("Initializing program...")
        print("\nInstruções de Controlo:")
        print("Controlo da Câmara:")
        print("- WASD: Mover a câmara para a frente/esquerda/trás/direita")
        print("- RF: Mover a câmara para cima/para baixo")
        print("- QE: Virar a câmara para a esquerda/direita")
        print("- TG: Olhar para cima/para baixo")
        print("\nControlo dos Objectos:")
        print("- Setas: Mover o objecto para a frente/esquerda/trás/direita")
        print("- UO: Rodar o objecto para a esquerda/direita")
        print("- KL: Inclinar o objecto para cima/para baixo")

        self.renderer = Renderer()
        self.scene = Scene()
        self.camera = Camera(aspect_ratio=1280/720)
        
        # Set up camera rig for movement
        self.camera_rig = MovementRig()
        self.camera_rig.add(self.camera)
        self.camera_rig.set_position([0.5, 1, 10])
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

        # Keep track of the currently controlled object rig
        self.active_object_rig = self.object_rig_miguel 
        
        axes = AxesHelper(axis_length=2)
        self.scene.add(axes)
        grid = GridHelper(
            size=20,
            grid_color=[1, 1, 1],
            center_color=[1, 1, 0]
        )
        grid.rotate_x(-math.pi / 2)
        self.scene.add(grid)

    def update(self):
        # Camera movement with WASDRF, QE, TG
        self.camera_rig.update(self.input, self.delta_time)
        
        # Object movement with arrow keys and other controls
        # TODO: Add logic to switch between active objects (e.g., number keys 1-4)
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
        
        self.renderer.render(self.scene, self.camera)

Example(screen_size=[1280, 720]).run()