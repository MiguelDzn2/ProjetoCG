import numpy as np
import math
import pathlib
import sys

from core.base import Base
from core_ext.camera import Camera
from core_ext.mesh import Mesh
from core_ext.renderer import Renderer
from core_ext.scene import Scene
from geometry.agogo2 import AgogoGeometry2
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
        self.camera = Camera(aspect_ratio=800/600)
        
        # Set up camera rig for movement
        self.camera_rig = MovementRig()
        self.camera_rig.add(self.camera)
        self.camera_rig.set_position([0.5, 1, 10])
        self.scene.add(self.camera_rig)
        
        # Load and create the Agogo object with metal texture
        positions, uvs = my_obj_reader2("geometry/agogoFixedUV2.obj")
        geometry = AgogoGeometry2(1, 1, 1, positions, uvs)
        metal_texture = Texture(file_name="images/txt2.jpg")
        material = TextureMaterial(texture=metal_texture)
        self.mesh = Mesh(geometry, material)
        
        # Set up object rig for movement
        self.object_rig = MovementRig()
        self.object_rig.add(self.mesh)
        self.object_rig.set_position([0, 0, 0])
        self.scene.add(self.object_rig)
        
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
        move_amount = 2 * self.delta_time
        rotate_amount = 1 * self.delta_time
        
        # Translation with arrow keys
        if self.input.is_key_pressed('left'):
            self.object_rig.translate(-move_amount, 0, 0)
        if self.input.is_key_pressed('right'):
            self.object_rig.translate(move_amount, 0, 0)
        if self.input.is_key_pressed('up'):
            self.object_rig.translate(0, 0, -move_amount)
        if self.input.is_key_pressed('down'):
            self.object_rig.translate(0, 0, move_amount)
            
        # Rotation with UO
        if self.input.is_key_pressed('u'):
            self.object_rig.rotate_y(rotate_amount)
        if self.input.is_key_pressed('o'):
            self.object_rig.rotate_y(-rotate_amount)
            
        # Tilt with KL
        if self.input.is_key_pressed('k'):
            self.object_rig.rotate_x(rotate_amount)
        if self.input.is_key_pressed('l'):
            self.object_rig.rotate_x(-rotate_amount)
        
        self.renderer.render(self.scene, self.camera)

Example(screen_size=[800, 600]).run()