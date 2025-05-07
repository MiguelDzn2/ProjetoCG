import numpy as np
from geometry.geometry import Geometry
from math import sin, cos, pi

class ConeGeometry(Geometry):
    def __init__(self, radius=1, height=1, num_segments=32, closed=True):
        super().__init__()

        positions = []
        colors = [] # Will be used for transparency gradient via vertex attribute
        uvs = []
        normals = []

        # Tip of the cone
        tip_position = [0, 0, 0]
        
        # Base center
        base_center_y = -height 

        # Vertex data for the sides of the cone
        for i in range(num_segments):
            angle_curr = (i / num_segments) * 2 * pi
            x_curr = radius * cos(angle_curr)
            z_curr = radius * sin(angle_curr)
            
            angle_next = ((i + 1) / num_segments) * 2 * pi
            x_next = radius * cos(angle_next)
            z_next = radius * sin(angle_next)

            # Triangle for the side
            # Vertex 1: Tip
            positions.append(tip_position)
            # Vertex 2: Current point on base edge
            positions.append([x_curr, base_center_y, z_curr])
            # Vertex 3: Next point on base edge
            positions.append([x_next, base_center_y, z_next])

            # Normals (simplified for now, proper normals would be more complex)
            # For a cone, the normal calculation is a bit more involved
            # to get smooth shading. This is a placeholder.
            # A better approach involves calculating the normal for each vertex on the cone surface.
            # For the tip, the normal is ambiguous or could be averaged.
            # For the base vertices, normals point outwards and slightly upwards.
            
            # Normal for the tip (average or pointing up)
            # For now, using a simplified approach.
            # Calculate tangent and bitangent for the triangle face
            v1 = np.array(tip_position)
            v2 = np.array([x_curr, base_center_y, z_curr])
            v3 = np.array([x_next, base_center_y, z_next])
            
            edge1 = v2 - v1
            edge2 = v3 - v1
            face_normal = np.cross(edge1, edge2)
            face_normal = face_normal / np.linalg.norm(face_normal)
            
            # For simplicity, using face normal for all three vertices of this side triangle
            # A more accurate lighting would require per-vertex normals that are interpolated.
            normals.extend([list(face_normal)] * 3)


            # Placeholder UVs and Colors (related to transparency)
            # The 'y' position (or a ratio of it) can be used for transparency.
            # Tip (y=0) should be opaque (alpha=1), base (y=-height) should be transparent (alpha=0).
            # We can pass a value [0,1] representing this gradient.
            colors.append([1, 1, 1, 1.0]) # Tip vertex (opaque)
            colors.append([1, 1, 1, 0.0]) # Base vertex (transparent)
            colors.append([1, 1, 1, 0.0]) # Base vertex (transparent)

            uvs.extend([[0.5, 0], [i/num_segments, 1], [(i+1)/num_segments, 1]])


        if closed:
            # Vertex data for the base of the cone (a circle)
            for i in range(num_segments):
                angle_curr = (i / num_segments) * 2 * pi
                x_curr = radius * cos(angle_curr)
                z_curr = radius * sin(angle_curr)

                angle_next = ((i + 1) / num_segments) * 2 * pi
                x_next = radius * cos(angle_next)
                z_next = radius * sin(angle_next)

                # Triangle for the base
                # Vertex 1: Center of the base
                positions.append([0, base_center_y, 0])
                # Vertex 2: Next point on base edge (note order for winding)
                positions.append([x_next, base_center_y, z_next])
                # Vertex 3: Current point on base edge
                positions.append([x_curr, base_center_y, z_curr])
                
                base_normal = [0, -1, 0] # Normals for the base point downwards
                normals.extend([base_normal] * 3)

                # All base vertices are at the 'transparent' end of the gradient
                colors.extend([[1,1,1, 0.0]] * 3)
                
                # UVs for the base
                uvs.append([0.5, 0.5]) # Center
                uvs.append([0.5 + 0.5 * cos(angle_next), 0.5 + 0.5 * sin(angle_next)])
                uvs.append([0.5 + 0.5 * cos(angle_curr), 0.5 + 0.5 * sin(angle_curr)])

        self.add_attribute("vec3", "vertexPosition", positions)
        self.add_attribute("vec3", "vertexNormal", normals)
        self.add_attribute("vec2", "vertexUV", uvs)
        # We will use vertexColor.w (alpha) for transparency, controlled by the shader.
        # The actual color of the cone can be a uniform in the shader.
        # Here, color attribute's alpha channel is used to pass the gradient value.
        self.add_attribute("vec4", "vertexColor", colors) # Using vertexColor to pass gradient
        
        self.count_vertices()

    def count_vertices(self):
        # Overriding if necessary, or ensuring base class does it
        if "vertexPosition" in self._attribute_dict:
            self._vertex_count = len(self._attribute_dict["vertexPosition"].data)
        else:
            self._vertex_count = 0
