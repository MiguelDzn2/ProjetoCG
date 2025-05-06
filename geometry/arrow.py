import math
from geometry.rectangle import RectangleGeometry
from geometry.polygon import PolygonGeometry
from material.surface import SurfaceMaterial
from core_ext.mesh import Mesh
from extras.movement_rig import MovementRig
from core.matrix import Matrix

class Arrow:
    SPEED_UNITS_PER_SECOND = 2.0
    RESET_POSITION=10
    
    def __init__(
        self,
        color=[1.0, 0.0, 0.0],
        offset=[0, 0, 0],
        size=0.8,
        angle=0.0,
        axis='z'
    ):
        self.attribute_dict = {
            "vertexPosition": None,
            "vertexColor": None,
            "vertexUV": None
        }
        body_width = 0.2 * size
        body_height = 0.6 * size
        tip_radius = 0.3 * size

        # Calculate precise dimensions
        triangle_height = tip_radius * math.cos(math.pi/6)
        total_height = body_height + triangle_height
        
        # Create a container rig for all components
        self.rig = MovementRig()
        
        # Create the inner rig that will be rotated and centered
        self.inner_rig = MovementRig()
        self.rig.add(self.inner_rig)
        
        # Calculate the center point of the combined shape
        # The center should be at (total_height / 2 - triangle_height / 2) from the top of the arrow
        center_offset_from_top = total_height / 2 - triangle_height / 2
        
        # Create the body (rectangle)
        body_geometry = RectangleGeometry(width=body_width, height=body_height)
        body_material = SurfaceMaterial(property_dict={"baseColor": color})
        self.body_mesh = Mesh(body_geometry, body_material)
        
        # Create the tip (triangle)
        tip_geometry = PolygonGeometry(sides=3, radius=tip_radius)
        tip_material = SurfaceMaterial(property_dict={"baseColor": color})
        self.tip_mesh = Mesh(tip_geometry, tip_material)
        self.tip_mesh.rotate_z(math.pi/2)  # Make triangle point up
        
        # Position the tip and body relative to the center
        # The triangle tip is at position (center_offset_from_top) from origin
        self.tip_mesh.set_position([0, center_offset_from_top - triangle_height/2, 0])
        
        # The rectangle is positioned below the triangle tip
        # Its top edge should be at position (center_offset_from_top - triangle_height) from origin
        self.body_mesh.set_position([0, center_offset_from_top - triangle_height - body_height/2, 0])
        
        # Add components to the inner rig
        self.inner_rig.add(self.body_mesh)
        self.inner_rig.add(self.tip_mesh)

        # Initialize movement attributes
        self.direction = 1  # Movement direction (1 for right, -1 for left)
        self.initial_y = 1  # Initial Y position
        self.fall_speed = 0 # Speed of Y decrease
        self.is_visible = True  # Track visibility
        
        # Apply initial rotation if specified
        if angle != 0.0:
            self.rotate(angle, axis)
            
        # Apply offset if specified
        if offset != [0, 0, 0]:
            current_pos = self.rig.local_position
            self.rig.set_position([
                current_pos[0] + offset[0],
                current_pos[1] + offset[1],
                current_pos[2] + offset[2]
            ])

    def add_to_scene(self, scene):
        scene.add(self.rig)

    def set_position(self, position):
        self.rig.set_position(position)
        
    def rotate(self, angle, axis='z'):
        """Rotaciona la flecha en el eje especificado (z por defecto)"""
        if axis == 'x':
            self.inner_rig.rotate_x(angle)
        elif axis == 'y':
            self.inner_rig.rotate_y(angle)
        else:  # Por defecto rotación en Z
            self.inner_rig.rotate_z(angle)

    def update(self, delta_time):
        """Atualiza o movimento da seta"""
        current_pos = self.rig.local_position
        
        # Define the absolute stopping X-coordinate
        arrow_stop_x = 4.0
        
        # Only update position if the arrow hasn't reached the stopping point
        if current_pos[0] < arrow_stop_x:
            new_x = current_pos[0] + self.SPEED_UNITS_PER_SECOND * self.direction * delta_time
            # Ensure the arrow doesn't overshoot the arrow_stop_x
            new_x = min(new_x, arrow_stop_x)
            self.rig.set_position([new_x, current_pos[1], current_pos[2]])
        else:
            # Mark the arrow as not visible once it reaches or passes arrow_stop_x
            self.is_visible = False

    def get_rotation_angle(self):
        """Obtém o ângulo de rotação atual da seta em graus"""
        # Extrai a rotação Z da matriz de transformação
        rotation_z = math.atan2(self.inner_rig._matrix[1][0], self.inner_rig._matrix[0][0])
        # Converte de radianos para graus
        return math.degrees(rotation_z) % 360

    def set_speed(self, speed):
        """Define a velocidade da seta"""
        self.SPEED_UNITS_PER_SECOND = speed
        
    def increment_speed(self, increment):
        """Incrementa a velocidade da seta"""
        self.SPEED_UNITS_PER_SECOND += increment

    def set_reset_position(self, position):
        """Define a posição de reset da seta"""
        self.RESET_POSITION = position
        
    def isVisible(self):
        return self.is_visible
        
    def change_color(self, color):
        """Changes the color of both parts of the arrow"""
        # Change body color
        if hasattr(self, 'body_mesh') and self.body_mesh:
            self.body_mesh.material.set_properties({"baseColor": color})
            
        # Change tip color
        if hasattr(self, 'tip_mesh') and self.tip_mesh:
            self.tip_mesh.material.set_properties({"baseColor": color})
            
    def get_bounding_rect(self):
        """
        Returns the circumscribed rectangle of the arrow (min_x, min_z, max_x, max_z)
        Takes into account the arrow's position and rotation
        """
        # Get current arrow position and rotation
        arrow_pos = self.rig.local_position
        rotation_rad = math.radians(self.get_rotation_angle())
        
        # Get dimensions from the arrow
        body_width = 0.2 * 0.8  # width * size from initialization
        body_height = 0.6 * 0.8  # height * size from initialization
        tip_radius = 0.3 * 0.8   # radius * size from initialization
        
        # Calculate the corners of the rectangle and triangle in local coordinates
        # Calculate dimensions
        triangle_height = tip_radius * math.cos(math.pi/6)
        total_height = body_height + triangle_height
        
        # Calculate the offset from the center
        center_offset_from_top = total_height / 2 - triangle_height / 2
        
        # Calculate the rectangle's corners relative to its center
        half_width = body_width / 2
        half_height = body_height / 2
        rect_center_y = center_offset_from_top - triangle_height - half_height
        
        # Rectangle corners (before rotation)
        rect_corners = [
            [-half_width, rect_center_y - half_height],  # bottom-left
            [half_width, rect_center_y - half_height],   # bottom-right
            [half_width, rect_center_y + half_height],   # top-right
            [-half_width, rect_center_y + half_height]   # top-left
        ]
        
        # Triangle corners (before rotation)
        triangle_center_y = center_offset_from_top - triangle_height/2
        triangle_corners = [
            [0, triangle_center_y + triangle_height/2],  # top
            [-tip_radius, triangle_center_y - triangle_height/2],  # bottom-left
            [tip_radius, triangle_center_y - triangle_height/2]    # bottom-right
        ]
        
        # Combine all corners
        all_corners = rect_corners + triangle_corners
        
        # Apply rotation to all corners
        rotated_corners = []
        for x, y in all_corners:
            # Apply rotation
            rotated_x = x * math.cos(rotation_rad) - y * math.sin(rotation_rad)
            rotated_y = x * math.sin(rotation_rad) + y * math.cos(rotation_rad)
            # Add arrow position offset
            rotated_corners.append([
                rotated_x + arrow_pos[0],  # x-coordinate
                rotated_y + arrow_pos[2]   # z-coordinate (y in 2D space)
            ])
        
        # Find min/max coordinates
        min_x = min(corner[0] for corner in rotated_corners)
        max_x = max(corner[0] for corner in rotated_corners)
        min_z = min(corner[1] for corner in rotated_corners)
        max_z = max(corner[1] for corner in rotated_corners)
        
        return min_x, min_z, max_x, max_z


