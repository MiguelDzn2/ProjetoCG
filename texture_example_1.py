"""Textures examples"""

from core.base import Base
from core_ext.camera import Camera
from core_ext.mesh import Mesh
from core_ext.renderer import Renderer
from core_ext.scene import Scene
from core_ext.texture import Texture
from geometry.rectangle import RectangleGeometry
from material.texture import TextureMaterial


class Example(Base):
    """ Render a textured square """
    def initialize(self):
        print("Initializing program...")
        self.renderer = Renderer()
        self.scene = Scene()
        self.camera = Camera(aspect_ratio=800/600)
        self.camera.set_position([0, 0, 2])
        geometry = RectangleGeometry(2, 1)
        grid_texture = Texture(file_name="images/grid.jpg")
        #grid_texture = Texture(file_name="images/sky.jpg")
        material = TextureMaterial(texture=grid_texture)
        self.mesh = Mesh(
            geometry=geometry,
            material=material
        )
        self.scene.add(self.mesh)

    def update(self):
        self.renderer.render(self.scene, self.camera)


# Instantiate this class and run the program
Example(screen_size=[800, 600]).run()
