#!/usr/bin/python3
import pathlib
import sys
import math

# Get the package directory
#package_dir = str(pathlib.Path(__file__).resolve().parents[2])
# Add the package directory into sys.path if necessary
#if package_dir not in sys.path:
#    sys.path.insert(0, package_dir)

from core.base import Base
from core_ext.camera import Camera
from core_ext.mesh import Mesh
from core_ext.renderer import Renderer
from core_ext.scene import Scene
from core_ext.texture import Texture
from extras.movement_rig import MovementRig
from geometry.sphere import SphereGeometry
from light.ambient import AmbientLight
from light.directional import DirectionalLight
from light.point import PointLight
from material.flat import FlatMaterial
from material.lambert import LambertMaterial
from material.phong import PhongMaterial


class Example(Base):
    """
    Demonstrate:
    - the flat shading model;
    - the Lambert illumination model and Phong shading model;
    - the Phong illumination model and Phong shading model.
    The Lambert illumination model uses a combination of ambient and diffuse lighting.
    The Phong illumination model uses ambient, diffuse, and specular lighting.
    In the flat shading model, the light calculations are performed in the vertex shader.
    In the Phong shading model, the light calculations are performed in the fragment shader.

    Move a camera: WASDRF(move), QE(turn), TG(look).
    The camera also automatically rotates around the scene.
    """
    def initialize(self):
        print("Initializing program...")
        self.renderer = Renderer()
        self.scene = Scene()
        self.camera = Camera(aspect_ratio=800/600)
        self.rig = MovementRig()
        self.rig.add(self.camera)
        self.rig.set_position([0, 0, 8])
        self.scene.add(self.rig)
        
        # Camera rotation variables
        self.rotation_angle = 0
        self.rotation_speed = 0.5
        self.orbit_radius = 8

        # four light sources
        ambient_light = AmbientLight(color=[0.1, 0.1, 0.1])
        self.scene.add(ambient_light)
        directional_light = DirectionalLight(color=[1.5, 1.5, 1.5], direction=[-1, -1, -2])
        self.scene.add(directional_light)
        point_light1 = PointLight(color=[0.9, 0, 0], position=[4, 0, 0])
        self.scene.add(point_light1)
        point_light2 = PointLight(color=[0, 0.9, 0], position=[-4, 0, 0])
        self.scene.add(point_light2)

        # lighted materials with a color
        flat_material = FlatMaterial(
            property_dict={"baseColor": [0.2, 0.5, 0.5]},
            number_of_light_sources=4
        )
        lambert_material = LambertMaterial(
            property_dict={"baseColor": [0.2, 0.5, 0.5]},
            number_of_light_sources=4
        )
        phong_material = PhongMaterial(
            property_dict={"baseColor": [0.2, 0.5, 0.5]},
            number_of_light_sources=4
        )

        # lighted spheres with a color
        sphere_geometry = SphereGeometry()
        sphere_left_top = Mesh(sphere_geometry, flat_material)
        sphere_left_top.set_position([-2.5, 1.5, 0])
        self.scene.add(sphere_left_top)
        sphere_center_top = Mesh(sphere_geometry, lambert_material)
        sphere_center_top.set_position([0, 1.5, 0])
        self.scene.add(sphere_center_top)
        sphere_right_top = Mesh(sphere_geometry, phong_material)
        sphere_right_top.set_position([2.5, 1.5, 0])
        self.scene.add(sphere_right_top)

        # lighted materials with a texture
        textured_flat_material = FlatMaterial(
            texture=Texture("images/grid.jpg"),
            number_of_light_sources=4
        )
        textured_lambert_material = LambertMaterial(
            texture=Texture("images/grid.jpg"),
            number_of_light_sources=4
        )
        textured_phong_material = PhongMaterial(
            texture=Texture("images/grid.jpg"),
            number_of_light_sources=4
        )

        # lighted spheres with a texture
        sphere_left_bottom = Mesh(sphere_geometry, textured_flat_material)
        sphere_left_bottom.set_position([-2.5, -1.5, 0])
        self.scene.add(sphere_left_bottom)
        sphere_center_bottom = Mesh(sphere_geometry, textured_lambert_material)
        sphere_center_bottom.set_position([0, -1.5, 0])
        self.scene.add(sphere_center_bottom)
        sphere_right_bottom = Mesh(sphere_geometry, textured_phong_material)
        sphere_right_bottom.set_position([2.5, -1.5, 0])
        self.scene.add(sphere_right_bottom)

    def update(self):
        # Handle manual movement
        self.rig.update(self.input, self.delta_time)
        
        # Update rotation angle
        self.rotation_angle += self.rotation_speed * self.delta_time
        
        # Calculate new camera position
        x = self.orbit_radius * math.sin(self.rotation_angle)
        z = self.orbit_radius * math.cos(self.rotation_angle)
        
        # Update camera position
        self.rig.set_position([x, 0, z])
        
        # Make camera look at center
        self.rig.look_at([0, 0, 0])
        
        # Render the scene
        self.renderer.render(self.scene, self.camera)


# Instantiate this class and run the program
Example(screen_size=[800, 600]).run()
