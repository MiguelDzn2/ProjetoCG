import OpenGL.GL as GL

from material.basic import BasicMaterial


class SurfaceMaterial(BasicMaterial):
    def __init__(self, vertex_shader_code=None, fragment_shader_code=None, property_dict=None, use_vertex_colors=True):
        super().__init__(vertex_shader_code, fragment_shader_code, use_vertex_colors)
        # Render vertices as surface
        self._setting_dict["drawStyle"] = GL.GL_TRIANGLES
        # Render both sides? default: front side only
        # (vertices ordered counterclockwise)
        self._setting_dict["doubleSide"] = False
        # Render triangles as wireframe?
        self._setting_dict["wireframe"] = False
        # Set line thickness for wireframe rendering
        self._setting_dict["lineWidth"] = 1
        # Use depth testing? (default: True)
        self._setting_dict["depthTest"] = True
        # Blend mode (normal, additive, etc.)
        self._setting_dict["blendMode"] = "normal"
        # Render order (higher numbers render later/on top)
        self._setting_dict["renderOrder"] = 0
        self.set_properties(property_dict)

    def update_render_settings(self):
        if self._setting_dict["doubleSide"]:
            GL.glDisable(GL.GL_CULL_FACE)
        else:
            GL.glEnable(GL.GL_CULL_FACE)
        if self._setting_dict["wireframe"]:
            GL.glPolygonMode(GL.GL_FRONT_AND_BACK, GL.GL_LINE)
        else:
            GL.glPolygonMode(GL.GL_FRONT_AND_BACK, GL.GL_FILL)
        GL.glLineWidth(self._setting_dict["lineWidth"])
        
        # Handle depth testing
        if self._setting_dict["depthTest"]:
            GL.glEnable(GL.GL_DEPTH_TEST)
        else:
            GL.glDisable(GL.GL_DEPTH_TEST)
            
        # Handle blend mode
        if self._setting_dict["blendMode"] == "additive":
            GL.glBlendFunc(GL.GL_SRC_ALPHA, GL.GL_ONE)
        else:  # normal blending
            GL.glBlendFunc(GL.GL_SRC_ALPHA, GL.GL_ONE_MINUS_SRC_ALPHA)

    def set_properties(self, property_dict):
        """
        Set properties of material:
        baseColor, wireframe, doubleSide, lineWidth, etc.
        """
        if property_dict is None:
            property_dict = {}
        
        for name, data in property_dict.items():
            # Ensure baseColor values only have 3 components for vec3 uniforms
            if name == "baseColor" and isinstance(data, list) and len(data) > 3:
                data = data[:3]
                print(f"Warning: baseColor had more than 3 components. Truncated to RGB: {data}")
            
            if name in self._uniform_dict:
                self._uniform_dict[name].data = data
            elif name in self._setting_dict:
                self._setting_dict[name] = data
