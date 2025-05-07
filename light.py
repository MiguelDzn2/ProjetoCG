#!/usr/bin/python3
# import pathlib
# import sys

# Get the package directory
# package_dir = str(pathlib.Path(__file__).resolve().parents[2])
# Add the package directory into sys.path if necessary
# if package_dir not in sys.path:
# sys.path.insert(0, package_dir)

from core.base import Base
from core_ext.camera import Camera
from core_ext.mesh import Mesh
from core_ext.renderer import Renderer
from core_ext.scene import Scene
from extras.movement_rig import MovementRig
from geometry.sphere import SphereGeometry
from light.ambient import AmbientLight
from light.point import PointLight
from material.phong import PhongMaterial
from material.basic import BasicMaterial # Assuming BasicMaterial is in material.basic as per user context


class Example(Base):
    """
    Demonstrates a visible point light source, ambient light,
    and a reflective object.
    The point light source is visualized as a glowing sphere.
    The object below it reflects the light.

    Camera controls:
    - WASD to move forward/left/backward/right
    - RF to move up/down
    - QE to turn left/right
    - TG to look up/down
    """
    def initialize(self):
        print("Initializing program...")
        self.renderer = Renderer()
        self.scene = Scene()
        self.camera = Camera(aspect_ratio=800/600)
        
        self.rig = MovementRig()
        self.rig.add(self.camera)
        self.rig.set_position([0, 1.5, 7]) # Position camera to see the setup
        self.scene.add(self.rig)

        # Lights
        ambient_light = AmbientLight(color=[0.1, 0.1, 0.1])
        self.scene.add(ambient_light)

        point_light_color = [1.0, 1.0, 1.0]
        self.point_light = PointLight(color=point_light_color, position=[0, 2.5, 0])
        self.scene.add(self.point_light)

        # Make the point light source visible
        glow_geometry = SphereGeometry(radius=0.2)
        # Assuming BasicMaterial uses baseColor for an unlit/emissive effect
        glow_material = BasicMaterial()
        glow_material.add_uniform("vec3", "baseColor", point_light_color)
        glow_material.locate_uniforms() # Crucial after adding/modifying uniforms

        glow_mesh = Mesh(glow_geometry, glow_material)
        self.point_light.add(glow_mesh) # Attach glow mesh to the light

        # Reflective object at the bottom
        object_geometry = SphereGeometry(radius=1.0)
        # Phong material for reflections, reacting to 2 light sources (ambient + point)
        object_material = PhongMaterial(
            property_dict={
                "baseColor": [0.2, 0.3, 0.8], # Bluish
                "specularStrength": 1.0, # Default is 1.0, explicitly stated
                "shininess": 50.0 # You had 50.0, so we keep it
            },
            number_of_light_sources=2 
        )
        
        object_mesh = Mesh(object_geometry, object_material)
        object_mesh.set_position([0, -1.0, 0]) # Position below the light
        self.scene.add(object_mesh)

    def update(self):
        self.rig.update(self.input, self.delta_time) # Handle camera movement
        self.renderer.render(self.scene, self.camera)


# Instantiate this class and run the program
if __name__ == "__main__":
    Example(screen_size=[800, 600]).run() 