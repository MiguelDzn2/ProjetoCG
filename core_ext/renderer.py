import OpenGL.GL as GL
import pygame
import numpy as np # Added for SSAO kernel/noise
import random      # Added for SSAO kernel/noise
import math        # Added for SSAO kernel

from core_ext.mesh import Mesh
from light.light import Light
from light.shadow import Shadow
from material.basic import BasicMaterial
from core.utils import Utils # Added for shader program initialization
# Texture class is not used for ssao_noise_texture anymore
# from core_ext.texture import Texture 
import config # Added for SSAO parameters
import ctypes # Added for VAO attribute pointers
from core_ext.object3d import Object3D


class Renderer:
    def _load_shader_code(self, filepath: str) -> str:
        with open(filepath, 'r', encoding='utf-8-sig') as f:
            lines = f.readlines()
        
        processed_code_lines = []
        version_directive_found_and_skipped = False
        for line in lines:
            # Strip each line individually for the startswith check, 
            # but append the original line to preserve formatting if it's not the version line.
            stripped_line_for_check = line.strip()
            if not version_directive_found_and_skipped and stripped_line_for_check.startswith("#version"):
                version_directive_found_and_skipped = True
                continue # Skip this line as core/utils.py is expected to add it
            processed_code_lines.append(line) 
            
        return "".join(processed_code_lines).strip() # Join the kept lines and strip leading/trailing whitespace from the final string

    def __init__(self, clear_color=(0, 0, 0)):
        GL.glEnable(GL.GL_DEPTH_TEST)
        # required for antialiasing
        GL.glEnable(GL.GL_MULTISAMPLE)
        GL.glClearColor(*clear_color, 1)
        self.clear_color = clear_color # Store clear_color as an instance attribute
        self._window_size = pygame.display.get_surface().get_size()
        self._shadows_enabled = False

        # Get screen dimensions locally for use in __init__ FBO setups
        screen_width, screen_height = self._window_size

        # G-Buffer setup
        self.g_buffer_fbo = GL.glGenFramebuffers(1)
        GL.glBindFramebuffer(GL.GL_FRAMEBUFFER, self.g_buffer_fbo)

        # Position color buffer
        self.g_position_texture = GL.glGenTextures(1)
        GL.glBindTexture(GL.GL_TEXTURE_2D, self.g_position_texture)
        GL.glTexImage2D(GL.GL_TEXTURE_2D, 0, GL.GL_RGB16F, screen_width, screen_height, 0, GL.GL_RGB, GL.GL_FLOAT, None)
        GL.glTexParameteri(GL.GL_TEXTURE_2D, GL.GL_TEXTURE_MIN_FILTER, GL.GL_NEAREST)
        GL.glTexParameteri(GL.GL_TEXTURE_2D, GL.GL_TEXTURE_MAG_FILTER, GL.GL_NEAREST)
        GL.glFramebufferTexture2D(GL.GL_FRAMEBUFFER, GL.GL_COLOR_ATTACHMENT0, GL.GL_TEXTURE_2D, self.g_position_texture, 0)

        # Normal color buffer
        self.g_normal_texture = GL.glGenTextures(1)
        GL.glBindTexture(GL.GL_TEXTURE_2D, self.g_normal_texture)
        GL.glTexImage2D(GL.GL_TEXTURE_2D, 0, GL.GL_RGB16F, screen_width, screen_height, 0, GL.GL_RGB, GL.GL_FLOAT, None)
        GL.glTexParameteri(GL.GL_TEXTURE_2D, GL.GL_TEXTURE_MIN_FILTER, GL.GL_NEAREST)
        GL.glTexParameteri(GL.GL_TEXTURE_2D, GL.GL_TEXTURE_MAG_FILTER, GL.GL_NEAREST)
        GL.glFramebufferTexture2D(GL.GL_FRAMEBUFFER, GL.GL_COLOR_ATTACHMENT1, GL.GL_TEXTURE_2D, self.g_normal_texture, 0)

        # Tell OpenGL which color attachments we'll use (of this framebuffer) for rendering 
        attachments = [GL.GL_COLOR_ATTACHMENT0, GL.GL_COLOR_ATTACHMENT1]
        GL.glDrawBuffers(len(attachments), attachments)

        # Create and attach depth buffer (renderbuffer)
        self.g_depth_rbo = GL.glGenRenderbuffers(1)
        GL.glBindRenderbuffer(GL.GL_RENDERBUFFER, self.g_depth_rbo)
        GL.glRenderbufferStorage(GL.GL_RENDERBUFFER, GL.GL_DEPTH_COMPONENT24, screen_width, screen_height)
        GL.glFramebufferRenderbuffer(GL.GL_FRAMEBUFFER, GL.GL_DEPTH_ATTACHMENT, GL.GL_RENDERBUFFER, self.g_depth_rbo)

        # Check if framebuffer is complete
        if GL.glCheckFramebufferStatus(GL.GL_FRAMEBUFFER) != GL.GL_FRAMEBUFFER_COMPLETE:
            print("ERROR::FRAMEBUFFER:: G-Buffer Framebuffer is not complete!")
        GL.glBindFramebuffer(GL.GL_FRAMEBUFFER, 0)

        # Load G-Buffer shader code
        gbuffer_vert_code = self._load_shader_code("material/gbuffer_vert.glsl")
        gbuffer_frag_code = self._load_shader_code("material/gbuffer_frag.glsl")

        # G-Buffer material using the new shaders
        self.gbuffer_material = BasicMaterial(
            vertex_shader_code=gbuffer_vert_code,
            fragment_shader_code=gbuffer_frag_code,
            use_vertex_colors=False # G-Buffer shaders don't use vertex colors
        )
        self.gbuffer_material.locate_uniforms()

        # SSAO Setup
        # ------------------------------------------------------------------
        # 1. Load SSAO Shaders and Create Program
        ssao_vert_code = self._load_shader_code("material/ssao_vert.glsl")
        ssao_frag_code = self._load_shader_code("material/ssao_frag.glsl")
        self.ssao_program_id = Utils.initialize_program(ssao_vert_code, ssao_frag_code)

        # 2. Get SSAO Uniform Locations
        GL.glUseProgram(self.ssao_program_id)
        self.ssao_uniforms = {
            "gPositionView": GL.glGetUniformLocation(self.ssao_program_id, "gPositionView"),
            "gNormalView": GL.glGetUniformLocation(self.ssao_program_id, "gNormalView"),
            "texNoise": GL.glGetUniformLocation(self.ssao_program_id, "texNoise"),
            "samples": GL.glGetUniformLocation(self.ssao_program_id, "samples[0]"), # Location of the first element
            "projectionMatrix": GL.glGetUniformLocation(self.ssao_program_id, "projectionMatrix"),
            "radius": GL.glGetUniformLocation(self.ssao_program_id, "radius"),
            "bias": GL.glGetUniformLocation(self.ssao_program_id, "bias"),
            "kernelSize": GL.glGetUniformLocation(self.ssao_program_id, "kernelSize"),
            "ssaoPower": GL.glGetUniformLocation(self.ssao_program_id, "ssaoPower"),
            "noiseScale": GL.glGetUniformLocation(self.ssao_program_id, "noiseScale")
        }
        # Set texture units for samplers once (they don't change)
        GL.glUniform1i(self.ssao_uniforms["gPositionView"], 0)
        GL.glUniform1i(self.ssao_uniforms["gNormalView"], 1)
        GL.glUniform1i(self.ssao_uniforms["texNoise"], 2)
        GL.glUseProgram(0)

        # 3. Generate SSAO Kernel
        self.ssao_kernel = []
        for i in range(config.SSAO_KERNEL_SIZE):
            sample = np.array([
                random.uniform(-1.0, 1.0),
                random.uniform(-1.0, 1.0),
                random.uniform(0.0, 1.0) # Hemisphere in tangent space (Z positive)
            ], dtype=np.float32)
            sample = sample / np.linalg.norm(sample) # Normalize
            sample *= random.uniform(0.0, 1.0) # Randomize scale for variety
            
            # Distribute samples more towards the center of the kernel
            scale = float(i) / float(config.SSAO_KERNEL_SIZE)
            # lerp(0.1, 1.0, scale * scale) - Accelerating interpolation
            scale = 0.1 + 0.9 * (scale * scale) 
            sample *= scale
            self.ssao_kernel.extend(sample.tolist()) # Flatten for glUniform3fv

        # 4. Generate SSAO Noise Texture (Manual OpenGL Object)
        noise_data_list = []
        for i in range(config.SSAO_NOISE_TEXTURE_SIZE * config.SSAO_NOISE_TEXTURE_SIZE):
            noise_data_list.extend([
                random.uniform(-1.0, 1.0), # R: random tangent x
                random.uniform(-1.0, 1.0), # G: random tangent y
                0.0                        # B: tangent z (0.0 for 2D rotation vector)
            ])
        noise_byte_data = np.array(noise_data_list, dtype=np.float32).tobytes()
        
        self.ssao_noise_texture_ref = GL.glGenTextures(1)
        GL.glBindTexture(GL.GL_TEXTURE_2D, self.ssao_noise_texture_ref)
        GL.glTexImage2D(GL.GL_TEXTURE_2D, 0, GL.GL_RGB16F, 
                        config.SSAO_NOISE_TEXTURE_SIZE, config.SSAO_NOISE_TEXTURE_SIZE, 
                        0, GL.GL_RGB, GL.GL_FLOAT, noise_byte_data)
        GL.glTexParameteri(GL.GL_TEXTURE_2D, GL.GL_TEXTURE_MIN_FILTER, GL.GL_NEAREST)
        GL.glTexParameteri(GL.GL_TEXTURE_2D, GL.GL_TEXTURE_MAG_FILTER, GL.GL_NEAREST)
        GL.glTexParameteri(GL.GL_TEXTURE_2D, GL.GL_TEXTURE_WRAP_S, GL.GL_REPEAT)
        GL.glTexParameteri(GL.GL_TEXTURE_2D, GL.GL_TEXTURE_WRAP_T, GL.GL_REPEAT)
        GL.glBindTexture(GL.GL_TEXTURE_2D, 0) # Unbind

        # 5. SSAO Framebuffer Object (FBO)
        self.ssao_fbo = GL.glGenFramebuffers(1)
        GL.glBindFramebuffer(GL.GL_FRAMEBUFFER, self.ssao_fbo)

        # SSAO color buffer texture (stores occlusion factor)
        self.ssao_color_texture = GL.glGenTextures(1)
        GL.glBindTexture(GL.GL_TEXTURE_2D, self.ssao_color_texture)
        # Using GL_RED as SSAO is a grayscale value. GL_R16F for precision.
        GL.glTexImage2D(GL.GL_TEXTURE_2D, 0, GL.GL_R16F, screen_width, screen_height, 0, GL.GL_RED, GL.GL_FLOAT, None)
        GL.glTexParameteri(GL.GL_TEXTURE_2D, GL.GL_TEXTURE_MIN_FILTER, GL.GL_NEAREST)
        GL.glTexParameteri(GL.GL_TEXTURE_2D, GL.GL_TEXTURE_MAG_FILTER, GL.GL_NEAREST)
        GL.glFramebufferTexture2D(GL.GL_FRAMEBUFFER, GL.GL_COLOR_ATTACHMENT0, GL.GL_TEXTURE_2D, self.ssao_color_texture, 0)
        
        if GL.glCheckFramebufferStatus(GL.GL_FRAMEBUFFER) != GL.GL_FRAMEBUFFER_COMPLETE:
            print("ERROR::FRAMEBUFFER:: SSAO Framebuffer is not complete!")
        GL.glBindFramebuffer(GL.GL_FRAMEBUFFER, 0)

        # 6. Full-Screen Quad VAO
        quad_vertices = np.array([
            # positions   # texCoords
            -1.0,  1.0,   0.0, 1.0,
            -1.0, -1.0,   0.0, 0.0,
             1.0, -1.0,   1.0, 0.0,

            -1.0,  1.0,   0.0, 1.0,
             1.0, -1.0,   1.0, 0.0,
             1.0,  1.0,   1.0, 1.0
        ], dtype=np.float32)

        self.quad_vao = GL.glGenVertexArrays(1)
        quad_vbo = GL.glGenBuffers(1)
        GL.glBindVertexArray(self.quad_vao)
        GL.glBindBuffer(GL.GL_ARRAY_BUFFER, quad_vbo)
        GL.glBufferData(GL.GL_ARRAY_BUFFER, quad_vertices.nbytes, quad_vertices, GL.GL_STATIC_DRAW)
        # Position attribute (location = 0)
        GL.glEnableVertexAttribArray(0)
        GL.glVertexAttribPointer(0, 2, GL.GL_FLOAT, GL.GL_FALSE, 4 * quad_vertices.itemsize, ctypes.c_void_p(0))
        # Texture coordinate attribute (location = 1)
        GL.glEnableVertexAttribArray(1)
        GL.glVertexAttribPointer(1, 2, GL.GL_FLOAT, GL.GL_FALSE, 4 * quad_vertices.itemsize, ctypes.c_void_p(2 * quad_vertices.itemsize))
        GL.glBindVertexArray(0)
        # End SSAO Setup
        # ------------------------------------------------------------------

        # SSAO Blur Pass Setup
        ssao_blur_vertex_shader_code = self._load_shader_code("material/ssao_blur_vert.glsl")
        ssao_blur_fragment_shader_code = self._load_shader_code("material/ssao_blur_frag.glsl")
        self.ssao_blur_material = BasicMaterial(
            ssao_blur_vertex_shader_code,
            ssao_blur_fragment_shader_code,
            use_vertex_colors=False
        )
        self.ssao_blur_material.add_uniform("sampler2D", "ssaoInput", 0)
        self.ssao_blur_material.locate_uniforms()

        # Create FBO for SSAO Blur Pass
        self.ssao_blur_fbo = GL.glGenFramebuffers(1)
        GL.glBindFramebuffer(GL.GL_FRAMEBUFFER, self.ssao_blur_fbo)

        self.ssao_blur_color_texture = GL.glGenTextures(1)
        GL.glBindTexture(GL.GL_TEXTURE_2D, self.ssao_blur_color_texture)
        GL.glTexImage2D(GL.GL_TEXTURE_2D, 0, GL.GL_RED, screen_width, screen_height, 0, GL.GL_RED, GL.GL_FLOAT, None)
        GL.glTexParameteri(GL.GL_TEXTURE_2D, GL.GL_TEXTURE_MIN_FILTER, GL.GL_NEAREST)
        GL.glTexParameteri(GL.GL_TEXTURE_2D, GL.GL_TEXTURE_MAG_FILTER, GL.GL_NEAREST)
        GL.glTexParameteri(GL.GL_TEXTURE_2D, GL.GL_TEXTURE_WRAP_S, GL.GL_CLAMP_TO_EDGE)
        GL.glTexParameteri(GL.GL_TEXTURE_2D, GL.GL_TEXTURE_WRAP_T, GL.GL_CLAMP_TO_EDGE)
        GL.glFramebufferTexture2D(GL.GL_FRAMEBUFFER, GL.GL_COLOR_ATTACHMENT0, GL.GL_TEXTURE_2D, self.ssao_blur_color_texture, 0)
        
        draw_buffers_blur = [GL.GL_COLOR_ATTACHMENT0]
        GL.glDrawBuffers(len(draw_buffers_blur), draw_buffers_blur)

        if GL.glCheckFramebufferStatus(GL.GL_FRAMEBUFFER) != GL.GL_FRAMEBUFFER_COMPLETE:
            print("ERROR: SSAO Blur Framebuffer is not complete!")
        GL.glBindFramebuffer(GL.GL_FRAMEBUFFER, 0)

        # Shader loading (ensure _load_shader_code is present and working)
        # G-Buffer Shaders (already loaded)
        # SSAO Shaders (already loaded)
        # SSAO Blur Shaders (already loaded, ssao_blur_vert.glsl is our quad pass-through)
        vertex_shader_code_quad_passthrough = self._load_shader_code("material/ssao_blur_vert.glsl") # Reusing
        fragment_shader_code_ssao_composite = self._load_shader_code("material/ssao_composite_frag.glsl")

        # SSAO Composite Material
        self.ssao_composite_material = BasicMaterial(vertex_shader_code_quad_passthrough, fragment_shader_code_ssao_composite)
        self.ssao_composite_material.add_uniform("sampler2D", "sceneTexture", None)
        self.ssao_composite_material.add_uniform("sampler2D", "ssaoBlurTexture", None)
        self.ssao_composite_material.locate_uniforms()

        # Main Scene FBO (for rendering the scene to a texture)
        self.main_scene_fbo = GL.glGenFramebuffers(1)
        GL.glBindFramebuffer(GL.GL_FRAMEBUFFER, self.main_scene_fbo)

        self.main_scene_color_texture = GL.glGenTextures(1)
        GL.glBindTexture(GL.GL_TEXTURE_2D, self.main_scene_color_texture)
        # Use local screen_width, screen_height for main_scene_fbo textures
        GL.glTexImage2D(GL.GL_TEXTURE_2D, 0, GL.GL_RGB16F, screen_width, screen_height, 0, GL.GL_RGB, GL.GL_FLOAT, None)
        GL.glTexParameteri(GL.GL_TEXTURE_2D, GL.GL_TEXTURE_MIN_FILTER, GL.GL_LINEAR)
        GL.glTexParameteri(GL.GL_TEXTURE_2D, GL.GL_TEXTURE_MAG_FILTER, GL.GL_LINEAR)
        GL.glFramebufferTexture2D(GL.GL_FRAMEBUFFER, GL.GL_COLOR_ATTACHMENT0, GL.GL_TEXTURE_2D, self.main_scene_color_texture, 0)

        self.main_scene_depth_rbo = GL.glGenRenderbuffers(1)
        GL.glBindRenderbuffer(GL.GL_RENDERBUFFER, self.main_scene_depth_rbo)
        # Use local screen_width, screen_height for main_scene_fbo renderbuffer
        GL.glRenderbufferStorage(GL.GL_RENDERBUFFER, GL.GL_DEPTH_COMPONENT24, screen_width, screen_height)
        GL.glFramebufferRenderbuffer(GL.GL_FRAMEBUFFER, GL.GL_DEPTH_ATTACHMENT, GL.GL_RENDERBUFFER, self.main_scene_depth_rbo)

        if GL.glCheckFramebufferStatus(GL.GL_FRAMEBUFFER) != GL.GL_FRAMEBUFFER_COMPLETE:
            print("ERROR: Main Scene Framebuffer is not complete!")
        
        GL.glBindFramebuffer(GL.GL_FRAMEBUFFER, 0) # Unbind

    @property
    def window_size(self):
        return self._window_size

    @property
    def shadow_object(self):
        return self._shadow_object

    def render(self, scene: Object3D, camera, clear_color_arg=True, clear_depth_arg=True, render_target_param=None):
        # Get screen dimensions locally
        screen_width, screen_height = self._window_size
        
        # Prepare mesh and light lists once
        descendant_list = scene.descendant_list
        mesh_filter = lambda x: isinstance(x, Mesh)
        mesh_list = list(filter(mesh_filter, descendant_list))
        light_list = list(filter(lambda x: isinstance(x, Light), descendant_list))

        camera.update_view_matrix()

        # 1. G-BUFFER PASS
        # ------------------------------------------------------------------
        GL.glBindFramebuffer(GL.GL_FRAMEBUFFER, self.g_buffer_fbo)
        GL.glViewport(0, 0, screen_width, screen_height)
        GL.glClearColor(0.0, 0.0, 0.0, 0.0)
        GL.glClear(GL.GL_COLOR_BUFFER_BIT | GL.GL_DEPTH_BUFFER_BIT)
        GL.glEnable(GL.GL_DEPTH_TEST)

        GL.glUseProgram(self.gbuffer_material.program_ref)
        self.gbuffer_material.uniform_dict["viewMatrix"].data = camera.view_matrix
        self.gbuffer_material.uniform_dict["projectionMatrix"].data = camera.projection_matrix
        self.gbuffer_material.uniform_dict["viewMatrix"].upload_data()
        self.gbuffer_material.uniform_dict["projectionMatrix"].upload_data()

        for mesh in mesh_list:
            if not mesh.visible:
                continue
            # Consider adding a check here if only certain types of objects should go to G-Buffer
            GL.glBindVertexArray(mesh.vao_ref)
            self.gbuffer_material.uniform_dict["modelMatrix"].data = mesh.global_matrix
            self.gbuffer_material.uniform_dict["modelMatrix"].upload_data()
            GL.glDrawArrays(mesh.material.setting_dict["drawStyle"], 0, mesh.geometry.vertex_count)
        # Unbinding g_buffer_fbo is implicitly handled by binding the next FBO

        # 2. SSAO CALCULATION PASS
        # ------------------------------------------------------------------
        GL.glBindFramebuffer(GL.GL_FRAMEBUFFER, self.ssao_fbo)
        GL.glViewport(0, 0, screen_width, screen_height)
        GL.glClearColor(1.0, 1.0, 1.0, 1.0) # Clear to white (no occlusion)
        GL.glClear(GL.GL_COLOR_BUFFER_BIT)
        GL.glDisable(GL.GL_DEPTH_TEST)

        GL.glUseProgram(self.ssao_program_id)
        GL.glActiveTexture(GL.GL_TEXTURE0)
        GL.glBindTexture(GL.GL_TEXTURE_2D, self.g_position_texture)
        GL.glActiveTexture(GL.GL_TEXTURE1)
        GL.glBindTexture(GL.GL_TEXTURE_2D, self.g_normal_texture)
        GL.glActiveTexture(GL.GL_TEXTURE2)
        GL.glBindTexture(GL.GL_TEXTURE_2D, self.ssao_noise_texture_ref)
        
        GL.glUniform1i(self.ssao_uniforms["gPositionView"], 0)
        GL.glUniform1i(self.ssao_uniforms["gNormalView"], 1)
        GL.glUniform1i(self.ssao_uniforms["texNoise"], 2)
        GL.glUniform3fv(self.ssao_uniforms["samples"], config.SSAO_KERNEL_SIZE, self.ssao_kernel)
        GL.glUniformMatrix4fv(self.ssao_uniforms["projectionMatrix"], 1, GL.GL_FALSE, camera.projection_matrix)
        GL.glUniform1f(self.ssao_uniforms["radius"], config.SSAO_RADIUS)
        GL.glUniform1f(self.ssao_uniforms["bias"], config.SSAO_BIAS)
        GL.glUniform1i(self.ssao_uniforms["kernelSize"], config.SSAO_KERNEL_SIZE)
        GL.glUniform1f(self.ssao_uniforms["ssaoPower"], config.SSAO_POWER)
        noise_scale_data = np.array([screen_width / config.SSAO_NOISE_TEXTURE_SIZE, screen_height / config.SSAO_NOISE_TEXTURE_SIZE], dtype=np.float32)
        GL.glUniform2fv(self.ssao_uniforms["noiseScale"], 1, noise_scale_data)

        GL.glBindVertexArray(self.quad_vao)
        GL.glDrawArrays(GL.GL_TRIANGLES, 0, 6)
        GL.glBindVertexArray(0)

        # 3. SSAO BLUR PASS
        # ------------------------------------------------------------------
        GL.glBindFramebuffer(GL.GL_FRAMEBUFFER, self.ssao_blur_fbo)
        GL.glViewport(0, 0, screen_width, screen_height)
        GL.glClear(GL.GL_COLOR_BUFFER_BIT)
        # Depth test remains disabled

        GL.glUseProgram(self.ssao_blur_material.program_ref)
        GL.glActiveTexture(GL.GL_TEXTURE0)
        GL.glBindTexture(GL.GL_TEXTURE_2D, self.ssao_color_texture)
        self.ssao_blur_material.uniform_dict["ssaoInput"].data = (self.ssao_color_texture, 0)
        self.ssao_blur_material.uniform_dict["ssaoInput"].upload_data()

        GL.glBindVertexArray(self.quad_vao)
        GL.glDrawArrays(GL.GL_TRIANGLES, 0, 6)
        GL.glBindVertexArray(0)

        # 4. SHADOW MAP GENERATION PASS (Only if shadows are enabled)
        # ------------------------------------------------------------------
        if self._shadows_enabled:
            GL.glBindFramebuffer(GL.GL_FRAMEBUFFER, self._shadow_object.render_target.framebuffer_ref)
            GL.glViewport(0, 0, self._shadow_object.render_target.width, self._shadow_object.render_target.height)
            GL.glClearColor(1.0, 1.0, 1.0, 1.0) # Clear depth to max (white for depth texture)
            GL.glClear(GL.GL_DEPTH_BUFFER_BIT) # Only clear depth for shadow map
            # Note: Some shadow implementations also clear color if using a color texture for variance shadow maps etc.
            # Assuming standard depth map here.
            GL.glEnable(GL.GL_DEPTH_TEST) # Depth test is crucial for shadow map generation
            GL.glEnable(GL.GL_CULL_FACE)  # Standard practice for shadow maps to avoid self-shadowing issues
            GL.glCullFace(GL.GL_FRONT)    # Cull front faces to help with peter-panning (or GL_BACK, depending on setup)

            GL.glUseProgram(self._shadow_object.material.program_ref) # Depth material
            self._shadow_object.update_internal() # Update shadow light's view/projection matrix
            
            # Upload shadow light's view and projection matrices (likely part of shadow_object.material or shadow_object itself)
            # This assumes shadow_object.material handles its own light-specific matrix uniforms.
            # For example:
            # self._shadow_object.material.uniform_dict["viewMatrix"].data = self._shadow_object.light_view_matrix
            # self._shadow_object.material.uniform_dict["projectionMatrix"].data = self._shadow_object.light_projection_matrix
            # These would be uploaded within the loop or once if shared.
            # The existing code: `for var_name, uniform_obj in self._shadow_object.material.uniform_dict.items(): uniform_obj.upload_data()`
            # implies the shadow material is responsible for all its uniforms including the light's view/proj. We'll keep that for now.

            for mesh in mesh_list:
                if not mesh.visible or mesh.material.setting_dict["drawStyle"] != GL.GL_TRIANGLES:
                    continue # Only visible, triangle meshes cast shadows
                
                GL.glBindVertexArray(mesh.vao_ref)
                self._shadow_object.material.uniform_dict["modelMatrix"].data = mesh.global_matrix
                # Upload all uniforms for shadow material (model matrix, and potentially shadow light view/proj if not set globally for the pass)
                for uniform_obj in self._shadow_object.material.uniform_dict.values():
                    uniform_obj.upload_data()
                GL.glDrawArrays(GL.GL_TRIANGLES, 0, mesh.geometry.vertex_count)
            
            GL.glCullFace(GL.GL_BACK) # Reset cull face to default
            # GL.glDisable(GL.GL_CULL_FACE) # Or disable if not default for main scene

        # 5. UNIFIED MAIN SCENE PASS (renders to self.main_scene_fbo)
        # ------------------------------------------------------------------
        GL.glBindFramebuffer(GL.GL_FRAMEBUFFER, self.main_scene_fbo)
        GL.glViewport(0, 0, screen_width, screen_height)
        GL.glClearColor(self.clear_color[0], self.clear_color[1], self.clear_color[2], 1.0)
        GL.glClear(GL.GL_COLOR_BUFFER_BIT | GL.GL_DEPTH_BUFFER_BIT)
        GL.glEnable(GL.GL_DEPTH_TEST)
        # Default blending for main scene (can be overridden by material settings)
        GL.glEnable(GL.GL_BLEND)
        GL.glBlendFunc(GL.GL_SRC_ALPHA, GL.GL_ONE_MINUS_SRC_ALPHA)
        # Default culling for main scene (can be overridden by material settings)
        GL.glEnable(GL.GL_CULL_FACE)
        GL.glCullFace(GL.GL_BACK)

        for mesh in mesh_list: # Changed from scene.descendant_list to pre-filtered mesh_list
            if not mesh.visible:
                continue

            GL.glUseProgram(mesh.material.program_ref)
            GL.glBindVertexArray(mesh.vao_ref)

            # Standard matrix uniforms
            mesh.material.uniform_dict["modelMatrix"].data = mesh.global_matrix
            mesh.material.uniform_dict["viewMatrix"].data = camera.view_matrix
            mesh.material.uniform_dict["projectionMatrix"].data = camera.projection_matrix
            
            if "viewPosition" in mesh.material.uniform_dict:
                 mesh.material.uniform_dict["viewPosition"].data = camera.global_position
            elif "cameraPosition" in mesh.material.uniform_dict:
                 mesh.material.uniform_dict["cameraPosition"].data = camera.global_position

            # Lighting uniforms
            if "light0" in mesh.material.uniform_dict: # Check if material uses old light array system
                for i in range(len(light_list)):
                    light_name = f"light{i}"
                    if light_name in mesh.material.uniform_dict:
                        mesh.material.uniform_dict[light_name].data = light_list[i]
            # Potentially add more sophisticated light handling here if materials expect it
            # e.g., passing number of lights, or arrays of light properties.

            # Shadow uniforms (if shadows enabled and material supports them)
            if self._shadows_enabled and "shadow0" in mesh.material.uniform_dict:
                 mesh.material.uniform_dict["shadow0"].data = self._shadow_object # self._shadow_object contains shadow map texture and matrices
            
            # Material-specific texture uniforms (e.g., diffuse map)
            # This part assumes that if a material has a texture (e.g., 'diffuseTexture'),
            # its 'data' field in uniform_dict is already set to a (texture_ref, texture_unit) tuple.
            # The BasicMaterial.add_uniform("sampler2D", name, (tex_ref, unit)) pattern, or similar,
            # should be used when materials are initialized with textures.

            # Upload all uniforms for this mesh's material
            for uniform_obj in mesh.material.uniform_dict.values():
                uniform_obj.upload_data()
            
            # Material-specific render settings (culling, blending)
            current_cull_face_enabled = True # Track current culling state for restoration
            if hasattr(mesh.material, 'settings') and "doubleSide" in mesh.material.settings and mesh.material.settings["doubleSide"]:
                GL.glDisable(GL.GL_CULL_FACE)
                current_cull_face_enabled = False
            else:
                GL.glEnable(GL.GL_CULL_FACE) # Ensure culling is on if not doubleSided
                GL.glCullFace(GL.GL_BACK)    # Ensure it's back-face culling
                current_cull_face_enabled = True

            # Handle blend mode if specified by material (example from light_cone_implementation.md)
            # Store original blend func to restore it if changed
            # original_blend_src, original_blend_dst = GL.glGetIntegerv(GL.GL_BLEND_SRC_ALPHA), GL.glGetIntegerv(GL.GL_BLEND_DST_ALPHA)
            blend_changed = False
            if hasattr(mesh.material, 'settings') and "blendMode" in mesh.material.settings:
                blend_mode = mesh.material.settings["blendMode"]
                if blend_mode == "additive":
                    GL.glBlendFunc(GL.GL_SRC_ALPHA, GL.GL_ONE)
                    blend_changed = True
                elif blend_mode == "normal": 
                    GL.glBlendFunc(GL.GL_SRC_ALPHA, GL.GL_ONE_MINUS_SRC_ALPHA)
                    blend_changed = True 
                # Add other blend modes if necessary
            
            # The old renderer had mesh.material.update_render_settings()
            # This function likely encapsulated the culling and blending logic. Replicating its intent here.
            if hasattr(mesh.material, 'update_render_settings') and callable(mesh.material.update_render_settings):
                 mesh.material.update_render_settings() # If this method handles culling/blending, the above manual GL calls might be redundant or conflict.
                                                       # For now, assuming the manual GL calls are needed due to refactoring.

            GL.glDrawArrays(mesh.material.setting_dict["drawStyle"], 0, mesh.geometry.vertex_count)

            # Restore default OpenGL states if they were changed for this mesh
            if not current_cull_face_enabled: # If culling was disabled for this mesh
                 GL.glEnable(GL.GL_CULL_FACE) # Re-enable default culling
                 GL.glCullFace(GL.GL_BACK)   # Reset to back-face culling
            if blend_changed:
                 GL.glBlendFunc(GL.GL_SRC_ALPHA, GL.GL_ONE_MINUS_SRC_ALPHA) # Reset to default blend mode

        # 6. FINAL COMPOSITE PASS (renders to default framebuffer - screen)
        # ------------------------------------------------------------------
        GL.glBindFramebuffer(GL.GL_FRAMEBUFFER, 0) 
        GL.glViewport(0, 0, screen_width, screen_height)
        GL.glClearColor(0.0, 0.0, 0.0, 1.0) # Clear with a distinct color for debugging if needed
        GL.glClear(GL.GL_COLOR_BUFFER_BIT) # Only color needed, depth already handled by main scene FBO
        GL.glDisable(GL.GL_DEPTH_TEST)
        GL.glDisable(GL.GL_BLEND)
        GL.glDisable(GL.GL_CULL_FACE) # Typically not needed for full-screen quad

        GL.glUseProgram(self.ssao_composite_material.program_ref)
        GL.glActiveTexture(GL.GL_TEXTURE0)
        GL.glBindTexture(GL.GL_TEXTURE_2D, self.main_scene_color_texture)
        self.ssao_composite_material.uniform_dict["sceneTexture"].data = (self.main_scene_color_texture, 0)
        
        GL.glActiveTexture(GL.GL_TEXTURE1)
        GL.glBindTexture(GL.GL_TEXTURE_2D, self.ssao_blur_color_texture)
        self.ssao_composite_material.uniform_dict["ssaoBlurTexture"].data = (self.ssao_blur_color_texture, 1)
        
        self.ssao_composite_material.uniform_dict["sceneTexture"].upload_data()
        self.ssao_composite_material.uniform_dict["ssaoBlurTexture"].upload_data()

        GL.glBindVertexArray(self.quad_vao)
        GL.glDrawArrays(GL.GL_TRIANGLES, 0, 6)
        GL.glBindVertexArray(0)

        # GL.glEnable(GL.GL_DEPTH_TEST) # Optional: re-enable if UI or other rendering follows and needs it.

    def enable_shadows(self, shadow_light, strength=0.5, resolution=(512, 512)):
        self._shadows_enabled = True
        self._shadow_object = Shadow(shadow_light, strength=strength, resolution=resolution)
