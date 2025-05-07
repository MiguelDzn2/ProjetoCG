from geometry.cone import ConeGeometry
from material.surface import SurfaceMaterial
from core_ext.mesh import Mesh
import math


class SpotLightHelper(Mesh):
    def __init__(self, spotlight, size=0.2, line_width=1):
        color = spotlight.color
        # Calculate radius at the end of the cone based on angle
        angle_radians = math.radians(spotlight.angle)
        radius = math.tan(angle_radians) * size
        
        # Create a cone geometry to represent the spotlight
        geometry = ConeGeometry(
            radius=radius, 
            height=size,
            radial_segments=16,
            height_segments=1
        )
        
        material = SurfaceMaterial(
            property_dict={
                "baseColor": color,
                "wireframe": True,
                "doubleSide": True,
                "lineWidth": line_width,
            }
        )
        
        super().__init__(geometry, material)
        
        # Rotate the cone to point in the direction of the spotlight
        # By default, the cone points down (-Y direction) 