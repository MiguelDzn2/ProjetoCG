import math
from geometry.rectangle import RectangleGeometry
from geometry.polygon import PolygonGeometry
from material.surface import SurfaceMaterial
from core_ext.mesh import Mesh
from extras.movement_rig import MovementRig
from core.matrix import Matrix

class Arrow:
    SPEED_UNITS_PER_SECOND = 2.0 # Default speed if not provided by instance
    RESET_POSITION=10
    
    def __init__(
        self,
        color=[1.0, 0.0, 0.0],
        offset=[0, 0, 0],
        size=0.8,
        angle=0.0,
        axis='z',
        debug_mode=False,
        speed=None  # Add speed parameter
    ):
        # Set instance-specific speed if provided, otherwise use class default
        if speed is not None:
            self.SPEED_UNITS_PER_SECOND = speed
        else:
            # Ensure self.SPEED_UNITS_PER_SECOND exists, inheriting from class if not overridden
            if not hasattr(self, 'SPEED_UNITS_PER_SECOND'):
                 self.SPEED_UNITS_PER_SECOND = Arrow.SPEED_UNITS_PER_SECOND
        
        # Ensure color only has 3 components for vec3 uniforms
        if len(color) > 3:
            color = color[:3]
        
        self.attribute_dict = {
            "vertexPosition": None,
            "vertexColor": None,
            "vertexUV": None
        }
        self.debug_mode = debug_mode
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
        
        # Initialize debug visualization variables
        self.debug_rect_mesh = None
        self.debug_corner_markers = []
        
        # Create debug visualization if in debug mode - Do this after position and rotation
        if self.debug_mode:
            result = self.create_debug_rect_visualization()

    def add_to_scene(self, scene):
        """Add the arrow to the scene and create a separate debug box if in debug mode"""
        scene.add(self.rig)
        
        # Store scene reference for debug visualization
        self.scene = scene
        
        # If in debug mode, create a direct scene debug box
        if self.debug_mode:
            self.create_direct_debug_box()

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

    def update(self, delta_time=None):
        """Updates the arrow's position based on its direction and applies any needed transformations"""
        if not self.is_visible:
            return
            
        # If delta_time is not provided (older code might not pass it), use a default value
        if delta_time is None:
            delta_time = 1/60  # Default to 60 FPS

        # Move the arrow based on direction and speed
        # Handle both legacy X-direction movement and new Z-direction movement
        # First check if we need to move in X direction (old method)
        current_pos = self.rig.local_position
        arrow_stop_x = 4.0  # Preserve the original stopping point logic
        
        # Use self.SPEED_UNITS_PER_SECOND which is now instance-specific or class default
        if current_pos[0] < arrow_stop_x:
            new_x = current_pos[0] + self.SPEED_UNITS_PER_SECOND * self.direction * delta_time
            # Ensure the arrow doesn't overshoot the arrow_stop_x
            new_x = min(new_x, arrow_stop_x)
            self.rig.set_position([new_x, current_pos[1], current_pos[2]])
            
            # Update direct debug box position to match new collision bounds
            if hasattr(self, 'direct_debug_box') and self.direct_debug_box:
                try:
                    # Get updated bounding rect
                    min_x, min_z, max_x, max_z = self.get_bounding_rect()
                    center_x = (min_x + max_x) / 2
                    center_z = (min_z + max_z) / 2
                    
                    # Update debug box position and size
                    self.direct_debug_box.set_position([center_x, current_pos[1] + 0.02, center_z])
                    
                    # Update corner markers
                    if hasattr(self, 'direct_corner_markers'):
                        corners = [
                            (min_x, min_z),  # Bottom-left
                            (max_x, min_z),  # Bottom-right
                            (max_x, max_z),  # Top-right
                            (min_x, max_z)   # Top-left
                        ]
                        
                        for i, (x, z) in enumerate(corners):
                            if i < len(self.direct_corner_markers):
                                self.direct_corner_markers[i].set_position([x, current_pos[1] + 0.04, z])
                except Exception as e:
                    pass
        else:
            # Mark the arrow as not visible once it reaches or passes arrow_stop_x
            self.is_visible = False
            
            # Remove direct debug box if it exists
            if hasattr(self, 'direct_debug_box') and self.direct_debug_box and hasattr(self, 'scene') and self.scene:
                try:
                    self.scene.remove(self.direct_debug_box)
                    self.direct_debug_box = None
                    
                    # Remove corner markers
                    if hasattr(self, 'direct_corner_markers'):
                        for marker in self.direct_corner_markers:
                            self.scene.remove(marker)
                        self.direct_corner_markers = []
                except Exception as e:
                    pass
        
        # Update standard debug visualization if enabled
        if self.debug_mode and self.debug_rect_mesh is not None:
            try:
                self.update_debug_rect_visualization()
            except Exception as e:
                # If we encounter errors, disable debug visualization to prevent crashes
                self.debug_mode = False

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
        # Ensure color only has 3 components for vec3 uniforms
        if len(color) > 3:
            color = color[:3]
        
        # Change body color
        if hasattr(self, 'body_mesh') and self.body_mesh:
            self.body_mesh.material.set_properties({"baseColor": color})
            
        # Change tip color
        if hasattr(self, 'tip_mesh') and self.tip_mesh:
            self.tip_mesh.material.set_properties({"baseColor": color})
            
    def get_bounding_rect(self):
        """
        Returns the precise circumscribed rectangle of the arrow (min_x, min_z, max_x, max_z)
        Takes into account the arrow's position and rotation with improved accuracy
        """
        # Get current arrow position and rotation
        arrow_pos = self.rig.local_position
        rotation_rad = math.radians(self.get_rotation_angle())
        
        # Get dimensions from the arrow
        body_width = 0.2 * 0.8  # width * size from initialization
        body_height = 0.6 * 0.8  # height * size from initialization
        tip_radius = 0.3 * 0.8   # radius * size from initialization
        
        # Calculate dimensions
        triangle_height = tip_radius * math.cos(math.pi/6)
        total_height = body_height + triangle_height
        
        # Calculate the offset from the center
        center_offset_from_top = total_height / 2 - triangle_height / 2
        
        # Create a more precise outline of the arrow shape with more points
        # Rectangle corners
        half_width = body_width / 2
        rect_center_y = center_offset_from_top - triangle_height - body_height/2
        
        rect_points = [
            [-half_width, rect_center_y - body_height/2],  # bottom-left
            [half_width, rect_center_y - body_height/2],   # bottom-right
            [half_width, rect_center_y + body_height/2],   # top-right
            [-half_width, rect_center_y + body_height/2]   # top-left
        ]
        
        # Triangle points - use more points to better define the triangle
        triangle_center_y = center_offset_from_top - triangle_height/2
        
        # Calculate exact points of the equilateral triangle
        triangle_top_y = triangle_center_y + triangle_height/2
        triangle_bottom_y = triangle_center_y - triangle_height/2
        
        triangle_points = [
            [0, triangle_top_y],  # top point
            [-tip_radius, triangle_bottom_y],  # bottom-left
            [tip_radius, triangle_bottom_y]    # bottom-right
        ]
        
        # Add midpoints for better accuracy
        triangle_points.append([tip_radius/2, (triangle_top_y + triangle_bottom_y)/2])  # mid-right
        triangle_points.append([-tip_radius/2, (triangle_top_y + triangle_bottom_y)/2]) # mid-left
        
        # Combine all points to represent the arrow's shape
        all_points = rect_points + triangle_points
        
        # Apply rotation to all points
        rotated_points = []
        for x, y in all_points:
            # Apply rotation
            rotated_x = x * math.cos(rotation_rad) - y * math.sin(rotation_rad)
            rotated_y = x * math.sin(rotation_rad) + y * math.cos(rotation_rad)
            # Add arrow position offset
            rotated_points.append([
                rotated_x + arrow_pos[0],  # x-coordinate
                rotated_y + arrow_pos[2]   # z-coordinate (y in 2D space)
            ])
        
        # Find min/max coordinates for the tight bounding box
        min_x = min(point[0] for point in rotated_points)
        max_x = max(point[0] for point in rotated_points)
        min_z = min(point[1] for point in rotated_points)
        max_z = max(point[1] for point in rotated_points)
        
        # Store the actual rotated points for debug visualization
        self.debug_points = rotated_points
        
        return min_x, min_z, max_x, max_z
        
    def create_debug_rect_visualization(self):
        """Creates a visual representation of the bounding rectangle when in debug mode"""
        try:
            # Get current bounding rect
            min_x, min_z, max_x, max_z = self.get_bounding_rect()
            
            # Make the bounding box much larger and more visible
            # Expand bounds to make it more obvious
            width = (max_x - min_x) * 1.5  # 50% wider
            height = (max_z - min_z) * 1.5  # 50% taller
            
            if width <= 0 or height <= 0:
                width = 0.5  # Use fixed size if calculations are wrong
                height = 0.5
            
            # Create rectangle geometry with simple but highly visible settings
            debug_geometry = RectangleGeometry(width=width, height=height)
            
            # Create a simple material with solid yellow color - avoid any fancy settings
            debug_material = SurfaceMaterial(
                property_dict={
                    "baseColor": [1.0, 1.0, 0.0],  # Bright yellow (removed alpha)
                    "wireframe": False,  # Make it solid
                    "doubleSide": True,  # Visible from both sides
                    "useVertexColors": False,  # Don't use vertex colors
                    "opacity": 1.0  # Set opacity separately if the material supports it
                }
            )
            
            # Create mesh
            self.debug_rect_mesh = Mesh(debug_geometry, debug_material)
            
            # Position it at the center of the bounding box in the XZ plane
            center_x = (min_x + max_x) / 2
            center_z = (min_z + max_z) / 2
            arrow_pos = self.rig.local_position
            
            # Position well above the arrow to prevent z-fighting and make it very visible
            self.debug_rect_mesh.set_position([center_x, arrow_pos[1] + 0.1, center_z])
            
            # Add it to the rig
            self.rig.add(self.debug_rect_mesh)
            
            # Create corner markers with bright white color
            self.create_bright_corner_markers(min_x, min_z, max_x, max_z)
            
            return True
        except Exception as e:
            self.debug_rect_mesh = None
            self.debug_corner_markers = []
            return False
            
    def create_bright_corner_markers(self, min_x, min_z, max_x, max_z):
        """Creates very bright and visible corner markers"""
        try:
            # Create corners
            corner_positions = [
                (min_x, min_z),  # Bottom-left
                (max_x, min_z),  # Bottom-right
                (max_x, max_z),  # Top-right
                (min_x, max_z)   # Top-left
            ]
            
            # Create material properties for corners (bright white for visibility)
            corner_colors = [
                [1.0, 0.0, 0.0],  # Red
                [0.0, 1.0, 0.0],  # Green
                [0.0, 0.0, 1.0],  # Blue
                [1.0, 0.0, 1.0]   # Purple
            ]
            
            # Create large rectangle for each corner
            self.debug_corner_markers = []
            for i, (x, z) in enumerate(corner_positions):
                # Large marker (0.2 units square) for high visibility
                corner_geometry = RectangleGeometry(width=0.2, height=0.2)
                
                # Create a new material for each corner with bright color
                corner_material = SurfaceMaterial(
                    property_dict={
                        "baseColor": corner_colors[i],
                        "doubleSide": True,
                        "wireframe": False  # Solid fill for better visibility
                    }
                )
                
                corner_mesh = Mesh(corner_geometry, corner_material)
                # Position well above the arrow for visibility
                corner_mesh.set_position([x, self.rig.local_position[1] + 0.15, z])
                self.rig.add(corner_mesh)
                self.debug_corner_markers.append(corner_mesh)
                
            return True
        except Exception as e:
            self.debug_corner_markers = []
            return False
    
    def update_debug_rect_visualization(self):
        """Updates the visual representation of the bounding rectangle"""
        if not self.debug_mode or self.debug_rect_mesh is None:
            return
        
        # Remove previous debug meshes
        try:
            # Keep track of whether we need to recreate the debug rect
            should_recreate = True
            
            # Try to remove existing debug visualization
            if self.debug_rect_mesh is not None:
                self.rig.remove(self.debug_rect_mesh)
                self.debug_rect_mesh = None
            
            # Remove corner markers if they exist
            if hasattr(self, 'debug_corner_markers'):
                for marker in self.debug_corner_markers:
                    self.rig.remove(marker)
                self.debug_corner_markers = []
        except Exception as e:
            pass
        
        # Get current bounding rect
        min_x, min_z, max_x, max_z = self.get_bounding_rect()
        width = max_x - min_x
        height = max_z - min_z
        
        # Create a new rectangle with updated dimensions
        debug_geometry = RectangleGeometry(width=width, height=height)
        debug_material = SurfaceMaterial(
            property_dict={
                "baseColor": [1.0, 0.0, 0.0],  # Red
                "wireframe": False,  # Solid fill for better visibility
                "doubleSide": True,  # Visible from both sides
                "lineWidth": 3.0     # Thicker lines
            }
        )
        # Add opacity as a separate uniform
        debug_material.add_uniform("float", "opacity", 0.4)
        debug_material.locate_uniforms()
        
        # Create new mesh
        self.debug_rect_mesh = Mesh(debug_geometry, debug_material)
        
        # Position at center of bounding box
        center_x = (min_x + max_x) / 2
        center_z = (min_z + max_z) / 2
        arrow_pos = self.rig.local_position
        self.debug_rect_mesh.set_position([center_x, arrow_pos[1], center_z])
        
        # Add to rig
        self.rig.add(self.debug_rect_mesh)
        
        # Update corner markers
        self.update_corner_markers(min_x, min_z, max_x, max_z)

    def update_corner_markers(self, min_x, min_z, max_x, max_z):
        """Updates the positions of the corner markers based on the updated bounding box"""
        try:
            # If we don't have corner markers yet, create them
            if not hasattr(self, 'debug_corner_markers') or not self.debug_corner_markers:
                self.create_bright_corner_markers(min_x, min_z, max_x, max_z)
                return
                
            # Update corner positions
            corner_positions = [
                (min_x, min_z),  # Bottom-left
                (max_x, min_z),  # Bottom-right
                (max_x, max_z),  # Top-right
                (min_x, max_z)   # Top-left
            ]
            
            # Update position of each corner marker
            for i, (x, z) in enumerate(corner_positions):
                if i < len(self.debug_corner_markers):
                    marker = self.debug_corner_markers[i]
                    marker.set_position([x, self.rig.local_position[1] + 0.02, z])  # Slightly above bounding box
        except Exception as e:
            # If we encounter errors with corner markers, just create new ones
            try:
                # First try to clean up existing markers if any
                if hasattr(self, 'debug_corner_markers'):
                    for marker in self.debug_corner_markers:
                        try:
                            self.rig.remove(marker)
                        except:
                            pass
                self.debug_corner_markers = []
                # Then create new markers
                self.create_bright_corner_markers(min_x, min_z, max_x, max_z)
            except Exception as inner_e:
                # If recreation fails, disable debug to prevent further errors
                self.debug_mode = False

    def create_direct_debug_box(self):
        """Create a debug box visualization directly in the scene for clearer collision viz"""
        if not hasattr(self, 'scene') or not self.scene:
            return False
            
        try:
            # Get current bounding rect
            min_x, min_z, max_x, max_z = self.get_bounding_rect()
            width = max_x - min_x
            height = max_z - min_z
            
            # Calculate center position relative to the arrow's current position
            current_pos = self.rig.global_position  # Use global position for debug visualization
            center_x = (min_x + max_x) / 2
            center_z = (min_z + max_z) / 2
            
            # Create a rectangle geometry for the debug box
            from geometry.rectangle import RectangleGeometry
            debug_rect_geo = RectangleGeometry(width=width, height=height)
            
            # Create a wireframe material
            from material.surface import SurfaceMaterial
            debug_rect_mat = SurfaceMaterial(
                property_dict={
                    "baseColor": [0, 0, 1, 0.5],  # Semi-transparent blue
                    "wireframe": True,
                    "doubleSide": True,
                    "receiveShadow": False
                }
            )
            
            # Create mesh and position it
            from core_ext.mesh import Mesh
            self.direct_debug_box = Mesh(debug_rect_geo, debug_rect_mat)
            
            # Position the debug box - offset slightly from the arrow to avoid Z-fighting
            # Using the arrow's global position to ensure it's in the same reference frame
            self.direct_debug_box.set_position([
                current_pos[0] + center_x, 
                current_pos[1] + 0.02,  # Slight offset in Y to avoid Z-fighting
                current_pos[2] + center_z
            ])
            
            # Add to the scene
            self.scene.add(self.direct_debug_box)
            
            # Create corner markers
            self.direct_corner_markers = self.create_direct_corner_markers(min_x, min_z, max_x, max_z)
            
            return True
        except Exception as e:
            return False
            
    def create_direct_corner_markers(self, min_x, min_z, max_x, max_z):
        """Create bright markers at the corners of the bounding rectangle"""
        if not hasattr(self, 'scene') or not self.scene:
            return []
            
        try:
            corner_markers = []
            
            # Get arrow's current global position for proper placement
            arrow_pos = self.rig.global_position
            
            # Define the corner positions in world space
            corner_positions = [
                [min_x + arrow_pos[0], arrow_pos[1] + 0.04, min_z + arrow_pos[2]],  # Bottom-left
                [max_x + arrow_pos[0], arrow_pos[1] + 0.04, min_z + arrow_pos[2]],  # Bottom-right
                [max_x + arrow_pos[0], arrow_pos[1] + 0.04, max_z + arrow_pos[2]],  # Top-right
                [min_x + arrow_pos[0], arrow_pos[1] + 0.04, max_z + arrow_pos[2]]   # Top-left
            ]
            
            # Create a marker for each corner with different colors for identification
            colors = [
                [1, 0, 0],  # Red (bottom-left)
                [0, 1, 0],  # Green (bottom-right)
                [0, 0, 1],  # Blue (top-right)
                [1, 1, 0]   # Yellow (top-left)
            ]
            
            for i, (pos, color) in enumerate(zip(corner_positions, colors)):
                # Create tiny sphere geometry for the marker
                from geometry.parametric import ParametricGeometry
                import numpy as np
                
                def sphere_function(u, v):
                    theta = u * 2 * np.pi
                    phi = v * np.pi
                    x = 0.05 * np.sin(phi) * np.cos(theta)  # Small 0.05 unit radius
                    y = 0.05 * np.sin(phi) * np.sin(theta)
                    z = 0.05 * np.cos(phi)
                    return [x, y, z]
                
                marker_geo = ParametricGeometry(0, 1, 8, 0, 1, 8, sphere_function)
                
                # Create a bright material for better visibility
                from material.surface import SurfaceMaterial
                marker_mat = SurfaceMaterial(property_dict={"baseColor": color, "doubleSide": True})
                
                # Create and position the marker
                from core_ext.mesh import Mesh
                marker = Mesh(marker_geo, marker_mat)
                marker.set_position(pos)
                
                # Add to scene and to our list
                self.scene.add(marker)
                corner_markers.append(marker)
            
            return corner_markers
        except Exception as e:
            return []

