# Uniform Class Explanation (`core/uniform.py`)

This document explains the `Uniform` class found in `core/uniform.py`, which is responsible for managing the transfer of data from the Python application to uniform variables within GLSL shader programs.

## Purpose

The `Uniform` class acts as a wrapper around OpenGL uniform variables. It stores the data type and the actual data intended for a specific uniform in a shader. It also handles obtaining the location of the uniform variable within the linked shader program and uploading the data to that location on the GPU.

## Structure

### `__init__(self, data_type, data)`

-   **Purpose**: Initializes a new `Uniform` object.
-   **Parameters**:
    -   `data_type` (str): The type of data this uniform holds. Supported types include: `'int'`, `'bool'`, `'float'`, `'vec2'`, `'vec3'`, `'vec4'`, `'mat4'`, and `'sampler2D'`.
    -   `data`: The actual data to be sent to the uniform. The structure of this data depends on `data_type`:
        -   Scalar types (`int`, `bool`, `float`): A single value.
        -   Vector types (`vec2`, `vec3`, `vec4`): A list or tuple of floats.
        -   Matrix type (`mat4`): A list or NumPy array representing the 4x4 matrix.
        -   Texture sampler type (`sampler2D`): A list or tuple containing `[texture_object_ref, texture_unit_ref]`.
-   **Internal State**:
    -   `_data_type`: Stores the provided data type.
    -   `_data`: Stores the provided data.
    -   `_variable_ref`: Initialized to `None`. Stores the GPU location reference of the uniform variable after `locate_variable` is called.

### `@property data` and `@data.setter data(self, data)`

-   **Purpose**: Provides controlled access to the `_data` attribute. Allows getting and setting the uniform's data after initialization.

### `locate_variable(self, program_ref, variable_name)`

-   **Purpose**: Finds the location (reference) of the uniform variable within a compiled and linked shader program.
-   **Parameters**:
    -   `program_ref`: The reference ID (an integer) of the linked OpenGL shader program.
    -   `variable_name` (str): The exact name of the uniform variable as defined in the shader code (e.g., `"modelMatrix"`, `"baseColor"`, `"texture"`).
-   **Action**: Calls `glGetUniformLocation` and stores the result in `self._variable_ref`. If the variable isn't found or isn't used by the shader, the location might be -1.

### `upload_data(self)`

-   **Purpose**: Sends the stored `_data` to the GPU uniform variable at the location stored in `self._variable_ref`.
-   **Action**: Checks if `_variable_ref` is valid (not -1). Based on `self._data_type`, it calls the appropriate OpenGL `glUniform*` function to upload the data.
-   **Data Type Handling**:
    -   `int`, `bool`: `glUniform1i`
    -   `float`: `glUniform1f`
    -   `vec2`, `vec3`, `vec4`: `glUniform2f`, `glUniform3f`, `glUniform4f`
    -   `mat4`: `glUniformMatrix4fv`
    -   `sampler2D`: This is crucial for textures.
        1.  It unpacks `self._data` into `texture_object_ref` (the OpenGL texture ID) and `texture_unit_ref` (the desired texture unit, e.g., 0, 1, 2...).
        2.  It activates the specified texture unit using `glActiveTexture(GL.GL_TEXTURE0 + texture_unit_ref)`.
        3.  It binds the texture object (`texture_object_ref`) to the now active texture unit using `glBindTexture(GL.GL_TEXTURE_2D, texture_object_ref)`.
        4.  It uploads the *texture unit number* (`texture_unit_ref`) to the `sampler2D` uniform variable in the shader using `glUniform1i`. This tells the shader which texture unit to sample from.

## Usage Example (Texture Material)

The `Uniform` class is typically used within a `Material` class (like `TextureMaterial` in `material/texture.py`).

1.  **Initialization in `TextureMaterial.__init__`**:

    ```python
    # Inside TextureMaterial.__init__(self, texture, property_dict={})
    # ... (shader code defined)
    super().__init__(vertex_shader_code, fragment_shader_code)
    # ... (other uniforms like baseColor added)
    
    # Create and add the sampler2D uniform for the texture
    # texture.texture_ref is the OpenGL ID generated when loading the texture
    # '1' is the chosen texture unit (could be 0, 1, etc.)
    self.add_uniform("sampler2D", "texture", [texture.texture_ref, 1]) 
    
    # ... (repeatUV, offsetUV uniforms added)
    self.locate_uniforms() # This calls locate_variable for all added uniforms
    ```

2.  **Uploading Data in `Renderer.render`**:

    ```python
    # Inside Renderer.render loop:
    for mesh in mesh_list:
        # ... (check visibility, use program, bind VAO)
        
        # Update standard matrix uniforms
        mesh.material.uniform_dict["modelMatrix"].data = mesh.global_matrix
        # ... (viewMatrix, projectionMatrix)
        
        # Upload all uniforms defined in the material
        for uniform_object in mesh.material.uniform_dict.values():
            uniform_object.upload_data() # This calls upload_data for each uniform
            
        # When the "texture" sampler2D uniform's upload_data() is called:
        # - It activates texture unit 1 (GL_TEXTURE0 + 1)
        # - It binds the correct texture ID (e.g., game_title_texture.texture_ref)
        # - It tells the shader's 'texture' sampler to use texture unit 1
        
        # ... (update render settings, glDrawArrays)
    ```

This setup ensures that before drawing a mesh, the correct texture is bound to the correct texture unit, and the shader is informed which unit to sample from via the `sampler2D` uniform. 