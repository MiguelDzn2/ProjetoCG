import OpenGL.GL as GL


class Uniform:
    def __init__(self, data_type, data):
        # type of data:
        # int | bool | float | vec2 | vec3 | vec4
        self._data_type = data_type
        # data to be sent to uniform variable
        self._data = data
        # reference for variable location in program
        self._variable_ref = None

    @property
    def data(self):
        return self._data

    @data.setter
    def data(self, data):
        self._data = data

    def locate_variable(self, program_ref, variable_name):
        """ Get and store reference for program variable with given name """
        if self._data_type == 'Light':
            self._variable_ref = {
                "lightType":    GL.glGetUniformLocation(program_ref, variable_name + ".lightType"),
                "color":        GL.glGetUniformLocation(program_ref, variable_name + ".color"),
                "direction":    GL.glGetUniformLocation(program_ref, variable_name + ".direction"),
                "position":     GL.glGetUniformLocation(program_ref, variable_name + ".position"),
                "attenuation":  GL.glGetUniformLocation(program_ref, variable_name + ".attenuation"),
            }
        elif self._data_type == "Shadow":
            self._variable_ref = {
                "lightDirection": GL.glGetUniformLocation(program_ref, variable_name + ".lightDirection"),
                "projectionMatrix": GL.glGetUniformLocation(program_ref, variable_name + ".projectionMatrix"),
                "viewMatrix": GL.glGetUniformLocation(program_ref, variable_name + ".viewMatrix"),
                "depthTextureSampler": GL.glGetUniformLocation(program_ref, variable_name + ".depthTextureSampler"),
                "strength": GL.glGetUniformLocation(program_ref, variable_name + ".strength"),
                "bias": GL.glGetUniformLocation(program_ref, variable_name + ".bias"),
            }
        else:
            self._variable_ref = GL.glGetUniformLocation(program_ref, variable_name)

    def upload_data(self):
        """ Store data in uniform variable previously located """
        # If the program does not reference the variable, then exit
        if self._variable_ref != -1:
            if self._data_type == 'int':
                GL.glUniform1i(self._variable_ref, self._data)
            elif self._data_type == 'bool':
                GL.glUniform1i(self._variable_ref, self._data)
            elif self._data_type == 'float':
                GL.glUniform1f(self._variable_ref, self._data)
            elif self._data_type == 'vec2':
                GL.glUniform2f(self._variable_ref, *self._data)
            elif self._data_type == 'vec3':
                # Check if data is a list of 3 elements
                if len(self._data) == 3 and all(isinstance(x, (int, float)) for x in self._data):
                    # Convert elements to float if they are ints
                    float_data = [float(x) for x in self._data]
                    # print(f"DEBUG uniform.py: vec3 uniform. ref={self._variable_ref}, data={float_data}, type(data)={type(float_data)}")
                    # print(f"DEBUG uniform.py: vec3 elements types: {[type(x) for x in float_data]}")
                    GL.glUniform3fv(self._variable_ref, 1, float_data)
                else:
                    print(f"ERROR uniform.py: Data type mismatch for vec3 uniform. Expected list of 3 numbers, got: {self._data}")
            elif self._data_type == 'vec4':
                GL.glUniform4f(self._variable_ref, *self._data)
            elif self._data_type == 'mat4':
                GL.glUniformMatrix4fv(self._variable_ref, 1, GL.GL_TRUE, self._data)
            elif self._data_type == "sampler2D":
                texture_object_ref, texture_unit_ref = self._data
                # Activate texture unit
                GL.glActiveTexture(GL.GL_TEXTURE0 + texture_unit_ref)
                # Associate texture object reference to currently active texture unit
                GL.glBindTexture(GL.GL_TEXTURE_2D, texture_object_ref)
                # Upload texture unit number (0...15) to uniform variable in shader
                GL.glUniform1i(self._variable_ref, texture_unit_ref)
            elif self._data_type == "Light":
                GL.glUniform1i(self._variable_ref["lightType"], self._data.light_type)
                GL.glUniform3f(self._variable_ref["color"], *self._data.color)
                GL.glUniform3f(self._variable_ref["direction"], *self._data.direction)
                # Ensure position components are explicitly Python floats
                position_data = [float(p) for p in self._data.local_position]
                GL.glUniform3f(self._variable_ref["position"], *position_data)
                GL.glUniform3f(self._variable_ref["attenuation"], *self._data.attenuation)
            elif self._data_type == "Shadow":
                GL.glUniform3f(self._variable_ref["lightDirection"], *self._data.light_source.direction)
                GL.glUniformMatrix4fv(self._variable_ref["projectionMatrix"], 1, GL.GL_TRUE, self._data.camera.projection_matrix)
                GL.glUniformMatrix4fv(self._variable_ref["viewMatrix"], 1, GL.GL_TRUE, self._data.camera.view_matrix)
                # Configure depth texture
                texture_object_ref = self._data.render_target.texture.texture_ref
                texture_unit_ref = 3
                GL.glActiveTexture(GL.GL_TEXTURE0 + texture_unit_ref)
                GL.glBindTexture(GL.GL_TEXTURE_2D, texture_object_ref)
                GL.glUniform1i(self._variable_ref["depthTextureSampler"], texture_unit_ref)
                GL.glUniform1f(self._variable_ref["strength"], self._data.strength)
                GL.glUniform1f(self._variable_ref["bias"], self._data.bias)
