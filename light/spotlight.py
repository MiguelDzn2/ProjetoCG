from light.light import Light
import numpy as np
from math import tan, acos, pi, radians
from core.matrix import Matrix
from geometry.cone import ConeGeometry
from material.basic import BasicMaterial
from core_ext.mesh import Mesh

def normalize_vector(v):
    v_arr = np.array(v, dtype=float) # Ensure it's a numpy array for linalg.norm
    norm = np.linalg.norm(v_arr)
    if norm == 0:
        return [float(x) for x in v_arr] # Return list of python floats
    normalized_arr = v_arr / norm
    return [float(x) for x in normalized_arr] # Return list of python floats

def rotation_matrix_from_vectors(default_forward_vec, target_direction_vec):
    # This function uses normalize_vector, so its outputs will be based on Python floats
    default_forward = normalize_vector(default_forward_vec) 
    target_direction = normalize_vector(target_direction_vec)

    # Convert to numpy arrays for cross/dot products if not already
    default_forward_np = np.array(default_forward)
    target_direction_np = np.array(target_direction)

    v = np.cross(default_forward_np, target_direction_np)
    s = np.linalg.norm(v)
    c = np.dot(default_forward_np, target_direction_np)

    if np.isclose(s, 0):
        if c > 0: # Same direction
            return Matrix.make_identity()
        else: # Opposite direction (180-degree rotation)
            # Try to find a perpendicular axis
            if not np.allclose(default_forward, [0, 1, 0]) and not np.allclose(default_forward, [0, -1, 0]):
                axis = np.cross(default_forward, [0, 1, 0])
            else: # Default forward is along Y, try X-axis
                axis = np.cross(default_forward, [1, 0, 0])
            axis = normalize_vector(axis)
            
            # Manual construction for 180-degree rotation around an axis (Rodrigues' formula simplified)
            # M = I + 2 * (axis_skew_matrix^2)
            # Or, if Matrix class has make_rotation_around_axis(angle, axis)
            # return Matrix.make_rotation_around_axis(pi, axis)
            # For now, let's use a sequence of rotations if axis is simple, or identity if complex.
            # This part can be made more robust with a general angle-axis rotation matrix.
            # If target is (0,1,0) and default is (0,-1,0), rotate pi around X.
            if np.allclose(default_forward, [0,-1,0]) and np.allclose(target_direction, [0,1,0]):
                return Matrix.make_rotation_x(pi)
            # Fallback if a simple 180 deg rotation isn't obvious here
            # A full angle-axis implementation would be better.
            # Create rotation matrix for 180 degrees around X if vectors are opposite along Y
            if np.allclose(default_forward, -target_direction):
                 # This is a simplified case, might need to find a perpendicular axis
                 # For (0,-1,0) to (0,1,0), rotate PI around X or Z
                 return Matrix.make_rotation_x(pi) # Or Z, or any axis perp to Y
            return Matrix.make_identity() # Fallback

    vx_skew = np.array([
        [0, -v[2], v[1]],
        [v[2], 0, -v[0]],
        [-v[1], v[0], 0]
    ])
    
    rotation_matrix_3x3 = np.identity(3) + vx_skew + (vx_skew @ vx_skew) * ((1 - c) / (s**2))
    
    rotation_matrix_4x4 = Matrix.make_identity()
    rotation_matrix_4x4[0:3, 0:3] = rotation_matrix_3x3
    return rotation_matrix_4x4

cone_vertex_shader_code = """
in vec3 vertexPosition;
in vec4 vertexColor; 
in vec3 vertexNormal; 
in vec2 vertexUV;     

out vec4 fragmentColor; 
out vec3 fragmentNormal;

uniform mat4 modelMatrix;
uniform mat4 viewMatrix;
uniform mat4 projectionMatrix;

void main()
{
    gl_Position = projectionMatrix * viewMatrix * modelMatrix * vec4(vertexPosition, 1.0);
    fragmentColor = vertexColor; 
    fragmentNormal = normalize(mat3(modelMatrix) * vertexNormal); 
}
"""

cone_fragment_shader_code = """
in vec4 fragmentColor; 
in vec3 fragmentNormal; 

uniform vec3 baseColor;      
uniform float opacity;       

out vec4 FragColor;

void main()
{
    FragColor = vec4(baseColor, fragmentColor.a * opacity);
}
"""

class SpotLight(Light):
    def __init__(self,
                 color=(1, 1, 1), # This will be used for both light emission and cone visualization
                 position=(0, 0, 0),
                 direction=(0, -1, 0),
                 angle=30,
                 attenuation=(1, 0, 0.1),
                 cone_visible=True,
                 cone_opacity=0.3,
                 cone_height=2.0):
        
        super().__init__(Light.SPOTLIGHT)
        self._color = [float(c) for c in color] # Ensure list of Python floats
        self._attenuation = [float(a) for a in attenuation] # Ensure list of Python floats
        self.transform = Matrix.make_identity()
        self.set_position(list(position)) # set_position is from Object3D, should be fine
        
        # _direction will be a list of Python floats due to updated normalize_vector
        self._direction = normalize_vector(direction)
        self._angle = float(angle) # Ensure angle is float
        self._cone_height = float(cone_height)
        self._initial_angle = float(angle)

        self.visual_cone = None
        if cone_visible:
            # Pass self._color (the light's main color) to _create_visual_cone
            self._create_visual_cone(self._color, float(cone_opacity))
            self.add(self.visual_cone)

    def _create_visual_cone(self, visual_cone_color_floats, cone_opacity_float):
        current_radius = self._cone_height * tan(radians(self._angle) / 2.0)

        self.cone_geometry = ConeGeometry(radius=current_radius, height=self._cone_height, num_segments=16, closed=True)
        
        self.cone_material = BasicMaterial(vertex_shader_code=cone_vertex_shader_code, 
                                           fragment_shader_code=cone_fragment_shader_code)
        # Ensure we only use the RGB components (first 3 values) of the color
        rgb_color = visual_cone_color_floats[:3] if len(visual_cone_color_floats) >= 3 else visual_cone_color_floats
        self.cone_material.add_uniform("vec3", "baseColor", rgb_color)
        self.cone_material.add_uniform("float", "opacity", cone_opacity_float)
        self.cone_material.locate_uniforms()
        self.cone_material.setting_dict["blendMode"] = "additive" 
        self.cone_material.setting_dict["doubleSide"] = True

        self.visual_cone = Mesh(self.cone_geometry, self.cone_material)
        self._update_cone_transform()

    def _update_cone_transform(self):
        if not self.visual_cone:
            return

        default_cone_axis = [0.0, -1.0, 0.0] # Ensure floats
        rotation_mat = rotation_matrix_from_vectors(default_cone_axis, self._direction)
        
        self.visual_cone.local_matrix = rotation_mat

    # Ensure SpotLight itself can be positioned.
    # Light class (parent) is an Object3D, so it has transform methods.
    # We override set_position and set_direction to also update our members.

    def set_position(self, position):
        super().set_position(list(position)) # Call Object3D's set_position

    def get_position(self): # Added getter for consistency
        return self.local_position


    def set_direction(self, direction):
        # normalize_vector now returns list of Python floats
        new_direction = normalize_vector(direction)
        # Compare lists of floats element-wise or convert to numpy for np.array_equal
        if not np.allclose(np.array(self._direction), np.array(new_direction)):
            self._direction = new_direction
            self._update_cone_transform()
        
    @property
    def direction(self):
        return self._direction
        
    @property
    def angle(self):
        return self._angle
    
    def set_angle(self, angle_degrees):
        angle_degrees_float = float(angle_degrees)
        if self._angle != angle_degrees_float:
            self._angle = angle_degrees_float
            if self.visual_cone:
                # When recreating cone, use self._color for its visual color
                cone_opacity = self.visual_cone.material.uniform_dict["opacity"].data
                
                if self.visual_cone in self._children_list:
                    self.remove(self.visual_cone)

                self._create_visual_cone(self._color, float(cone_opacity))
                if self.visual_cone:
                     self.add(self.visual_cone)
    
    # Make sure add/remove are available if SpotLight is also a parent
    def add(self, child):
        super().add(child)

    def remove(self, child):
        super().remove(child)

    def set_color(self, color):
        """
        Set the color of the spotlight and its visual cone.
        
        Parameters:
            color: List of RGB or RGBA values. If RGBA, the alpha component is ignored for the light.
        """
        # Ensure color is a list of floats with at least 3 components
        if len(color) >= 3:
            # Only use the RGB components for the light itself
            self._color = [float(c) for c in color[:3]]
            
            # Update the visual cone material if it exists
            if self.visual_cone:
                rgb_color = self._color[:3]  # Ensure it's only RGB
                self.visual_cone.material.uniform_dict["baseColor"].data = rgb_color
    
# Example usage:
# from core_ext.scene import Scene
# scene = Scene()
# my_spotlight = SpotLight(position=[0,3,0], direction=[0,-1,0], angle=45)
# scene.add(my_spotlight)
# print(my_spotlight.visual_cone.local_matrix)
# my_spotlight.set_direction([1,-1,0])
# print(my_spotlight.visual_cone.local_matrix)
# my_spotlight.set_angle(60)
# print(my_spotlight.visual_cone.local_matrix) 