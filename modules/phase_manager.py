"""
Phase manager module for handling game phase transitions and setup.
"""

import math
from game_phases import GamePhase
from light.ambient import AmbientLight
from light.directional import DirectionalLight
from light.spotlight import SpotLight
from core.matrix import Matrix
from config import CAMERA_INITIAL_POSITION, CAMERA_INITIAL_ROTATION
from geometry.rectangle import RectangleGeometry
from core_ext.mesh import Mesh
from core_ext.texture import Texture
from material.texture import TextureMaterial

class PhaseManager:
    """
    Manages game phases, transitions, and phase-specific setup.
    """
    
    def __init__(self, scene, camera_rig, ui_manager):
        """
        Initialize the phase manager.
        
        Parameters:
            scene: The scene to modify
            camera_rig: The camera rig to position
            ui_manager: The UI manager for phase-specific UI
        """
        self.scene = scene
        self.camera_rig = camera_rig
        self.ui_manager = ui_manager
        self.current_phase = GamePhase.SELECTION
        self.highlighted_index = 0
        self.object_rigs = []
        self.active_object_rig = None
        self.spotlights = []
        self.background = None
    
    def set_object_rigs(self, object_rigs):
        """Set the list of object rigs to manage"""
        self.object_rigs = object_rigs
        if self.object_rigs:
            self.active_object_rig = self.object_rigs[self.highlighted_index]
    
    def setup_selection_phase(self):
        """Configure the scene for selection phase"""
        # Update UI for selection phase
        self.ui_manager.show_ui_for_selection_phase()
        
        # Add background with background3500x3500.jpg
        if self.background in self.scene.descendant_list:
            self.scene.remove(self.background)
            
        # Create a large rectangle for the background
        # Using a wider rectangle to maintain the image aspect ratio
        background_geometry = RectangleGeometry(width=80, height=40)
        # Load background3500x3500.jpg texture
        grid_texture = Texture(file_name="images/background3500x3500.jpg")
        # Create material with the background texture
        background_material = TextureMaterial(
            texture=grid_texture,
            property_dict={
                "doubleSide": True,
                "repeatUV": [2, 1]  # Repeat the texture horizontally to avoid black sides
            }
        )
        # Create mesh for the background
        self.background = Mesh(background_geometry, background_material)
        # Position the background behind everything
        self.background.set_position([0.5, 105, -15])  # Centered position and moved further back
        # Add the background to the scene
        self.scene.add(self.background)

        # Reset camera transform first
        self.camera_rig._matrix = Matrix.make_identity()
        # Position camera high up and facing "backwards" to see all objects
        objects_y = 100  # Set the Y coordinate for the objects
        camera_y = objects_y + 5  # Position camera slightly above objects
        self.camera_rig.set_position([0.5, camera_y, 15])
        
        # Reset all objects to their original positions and rotations with increased spacing, high up
        positions = [[-4.5, objects_y, 0], [-1.5, objects_y, 0], [1.5, objects_y, 0], [4.5, objects_y, 1.5]]
        for i, rig in enumerate(self.object_rigs):
            # Reset the transformation matrix to identity
            rig._matrix = Matrix.make_identity()
            # Set the initial position
            rig.set_position(positions[i])
            # Reset the scale (as highlight_selected_object changes it)
            rig.scale(1)  # Scale back to 1
        
        # Remove any existing lights from previous phases or runs
        for obj in self.scene.descendant_list[:]:
            if isinstance(obj, AmbientLight) or isinstance(obj, DirectionalLight) or isinstance(obj, SpotLight):
                self.scene.remove(obj)
        
        # Add ambient light for general illumination
        ambient_light = AmbientLight(color=[0.7, 0.7, 0.7])  # Increased for texture visibility
        self.scene.add(ambient_light)
        
        # Add an ambient light beneath the game title
        title_ambient_light = AmbientLight(color=[0.05, 0.05, 0.15])  # Kept low
        title_ambient_light.set_position([0, 108, 0])
        self.scene.add(title_ambient_light)
        
        # Add directional light for overall directionality
        directional_light = DirectionalLight(color=[0.3, 0.3, 0.3], direction=[-1, -1, -1])
        self.scene.add(directional_light)
        
        # Add spotlights above each selectable object
        spotlight_colors = [
            [1.0, 1.0, 1.0],  # White for all spotlights
            [1.0, 1.0, 1.0],  # White for all spotlights
            [1.0, 1.0, 1.0],  # White for all spotlights
            [1.0, 1.0, 1.0]   # White for all spotlights
        ]
        
        self.spotlights = []
        spotlight_y_offset = 8  # Increased offset to move lights higher
        for i, position in enumerate(positions):
            # Position the spotlight above the object
            spotlight_pos = [position[0], position[1] + spotlight_y_offset, position[2]]
            # Direct it downward toward the object
            spotlight_dir = [0, -1, 0]
            # Create the spotlight with a color matching the instrument
            spotlight = SpotLight(
                color=spotlight_colors[i],
                position=spotlight_pos,
                direction=spotlight_dir,
                angle=35,                  # Cone angle (degrees)
                attenuation=(1, 0.01, 0.005),  # Standard attenuation
                cone_visible=True,         # Ensure cone is visible
                cone_opacity=0.35,         # Increased opacity for cones
                cone_height=4.0            # Visual height of the cone
            )
            self.scene.add(spotlight)
            
            # Store the spotlight for later use
            self.spotlights.append(spotlight)
        
        # Apply highlighting to the currently selected object
        self.highlight_selected_object()
        
        # Set current phase
        self.current_phase = GamePhase.SELECTION
    
    def setup_gameplay_phase(self):
        """Configure the scene for gameplay phase"""
        # Update UI for gameplay phase
        self.ui_manager.show_ui_for_gameplay_phase()
        
        # Remove the background if it exists
        if self.background in self.scene.descendant_list:
            self.scene.remove(self.background)
        
        # Reset camera transform first
        self.camera_rig._matrix = Matrix.make_identity()
        
        # Apply hardcoded position and rotation for camera
        self.camera_rig.set_position(CAMERA_INITIAL_POSITION)
        
        # Apply rotations if needed
        if CAMERA_INITIAL_ROTATION[0] != 0:
            self.camera_rig.rotate_x(CAMERA_INITIAL_ROTATION[0])
        if CAMERA_INITIAL_ROTATION[1] != 0:
            self.camera_rig.rotate_y(CAMERA_INITIAL_ROTATION[1])
        if CAMERA_INITIAL_ROTATION[2] != 0:
            self.camera_rig.rotate_z(CAMERA_INITIAL_ROTATION[2])
        
        # Remove highlighting and reset active object
        self.remove_highlighting()
        self.active_object_rig._matrix = Matrix.make_identity()
        self.active_object_rig.set_position([0, 0, 0])
        
        # Get the index of the selected instrument
        selected_index = self.object_rigs.index(self.active_object_rig)
        
        # Define positions and rotations based on which instrument was selected
        # Format: [positions for instrument 0, positions for instrument 1, positions for instrument 2, positions for instrument 3]
        # Each "positions for instrument X" is a list of 3 [x,y,z] positions for the other instruments
        positions_by_selection = [
            # Positions when Miguel's instrument (index 0) is selected
            [
                None,                   # No position for Miguel (selected)
                [10, -0.45, 10.5],      # Position for Ze's instrument
                [12, -0.45, 7.2],       # Position for Ana's instrument
                [10, -1, 4.5]           # Position for Brandon's instrument
            ],
            # Positions when Ze's instrument (index 1) is selected
            [
                [10, -0.45, 10.5],      # Position for Miguel's instrument
                None,                   # No position for Ze (selected)
                [12, -0.45, 7.2],       # Position for Ana's instrument
                [10, -1, 4.5]           # Position for Brandon's instrument
            ],
            # Positions when Ana's instrument (index 2) is selected
            [
                [10, -0.45, 10.5],      # Position for Miguel's instrument
                [12, -0.45, 7.2],       # Position for Ze's instrument
                None,                   # No position for Ana (selected)
                [10, -1, 4.5]           # Position for Brandon's instrument
            ],
            # Positions when Brandon's instrument (index 3) is selected
            [
                [10, -0.45, 10.5],      # Position for Miguel's instrument
                [12, -0.45, 7.2],       # Position for Ze's instrument
                [10, -1, 4.5],          # Position for Ana's instrument
                None                    # No position for Brandon (selected)
            ]
        ]
        
        # Define rotations based on which instrument was selected
        # Format similar to positions_by_selection
        rotations_by_selection = [
            # Rotations when Miguel's instrument (index 0) is selected
            # the rotation axis are (x,y,z)
            [
                None,                       # No rotation for Miguel (selected)
                [math.pi/4, math.pi/6, 0],          # Rotation for Ze's instrument
                [math.pi/10, math.pi/2, 0],         # Rotation for Ana's instrument
                [-math.pi/4, -math.pi/8, -math.pi/4]          # Rotation for Brandon's instrument
            ],
            # Rotations when Ze's instrument (index 1) is selected
            [
                [math.pi/4, math.pi/6, 0],          # Rotation for Miguel's instrument
                None,                       # No rotation for Ze (selected)
                [math.pi/10, math.pi/2, 0],         # Rotation for Ana's instrument
                [-math.pi/4, -math.pi/8, -math.pi/4]          # Rotation for Brandon's instrument
            ],
            # Rotations when Ana's instrument (index 2) is selected
            [
                [math.pi/4, math.pi/6, 0],          # Rotation for Miguel's instrument
                [math.pi/4, math.pi/6, 0],          # Rotation for Ze's instrument
                None,                       # No rotation for Ana (selected)
                [-math.pi/4, -math.pi/8, -math.pi/4]          # Rotation for Brandon's instrument
            ],
            # Rotations when Brandon's instrument (index 3) is selected
            [
                [math.pi/4, math.pi/6, 0],          # Rotation for Miguel's instrument
                [math.pi/4, math.pi/6, 0],          # Rotation for Ze's instrument
                [math.pi/10, math.pi/2, 0],         # Rotation for Ana's instrument
                None                        # No rotation for Brandon (selected)
            ]
        ]
        
        # Apply positions and rotations based on selection
        for i, rig in enumerate(self.object_rigs):
            if rig != self.active_object_rig:
                rig._matrix = Matrix.make_identity()
                
                # Get position and rotation for this instrument based on which one was selected
                position = positions_by_selection[selected_index][i]
                rotation = rotations_by_selection[selected_index][i]
                
                if position:
                    rig.set_position(position)
                
                if rotation:
                    rig.rotate_y(rotation[1])
                    rig.rotate_x(rotation[0])
                    rig.rotate_z(rotation[2])
        
        # Set current phase
        self.current_phase = GamePhase.GAMEPLAY
        
        return selected_index  # Return the selected instrument index for music loading
    
    def highlight_selected_object(self):
        """Apply visual highlighting to the selected object"""
        # Simple highlighting by scaling up the selected object
        for i, rig in enumerate(self.object_rigs):
            # First, reset scale to 1 for all
            current_pos = rig.local_position  # Store position
            rig._matrix = Matrix.make_identity()  # Reset matrix (also resets scale)
            rig.set_position(current_pos)  # Reapply position
            
            if i == self.highlighted_index:
                # Scale up the highlighted object
                rig.scale(1.2)  # Apply scale
                
                # Also make its spotlight brighter if spotlights exist
                if hasattr(self, 'spotlights') and i < len(self.spotlights):
                    # Make the selected spotlight brighter
                    spotlight = self.spotlights[i]
                    # Get the original color based on the spotlight_colors list
                    spotlight_colors = [
                        [1.0, 1.0, 1.0],  # White for all spotlights
                        [1.0, 1.0, 1.0],  # White for all spotlights
                        [1.0, 1.0, 1.0],  # White for all spotlights
                        [1.0, 1.0, 1.0]   # White for all spotlights
                    ]
                    # Increase brightness by 50%
                    brighter_color = [c * 1.5 for c in spotlight_colors[i]]
                    # Ensure spotlight._color has only RGB components (no alpha)
                    spotlight._color = brighter_color[:3] if len(brighter_color) > 3 else brighter_color
                    # Update the cone material if it exists
                    if spotlight.visual_cone:
                        # Ensure baseColor only gets RGB components
                        rgb_color = brighter_color[:3] if len(brighter_color) > 3 else brighter_color
                        spotlight.visual_cone.material.uniform_dict["baseColor"].data = rgb_color
            else:
                # Return other spotlights to normal brightness
                if hasattr(self, 'spotlights') and i < len(self.spotlights):
                    # Get the original color based on the spotlight_colors list
                    spotlight_colors = [
                        [1.0, 1.0, 1.0],  # White for all spotlights
                        [1.0, 1.0, 1.0],  # White for all spotlights
                        [1.0, 1.0, 1.0],  # White for all spotlights
                        [1.0, 1.0, 1.0]   # White for all spotlights
                    ]
                    spotlight = self.spotlights[i]
                    # Ensure spotlight._color has only RGB components (no alpha)
                    spotlight._color = spotlight_colors[i][:3] if len(spotlight_colors[i]) > 3 else spotlight_colors[i]
                    # Update the cone material if it exists
                    if spotlight.visual_cone:
                        # Ensure baseColor only gets RGB components
                        rgb_color = spotlight_colors[i][:3] if len(spotlight_colors[i]) > 3 else spotlight_colors[i]
                        spotlight.visual_cone.material.uniform_dict["baseColor"].data = rgb_color
    
    def remove_highlighting(self):
        """Remove highlighting from all objects"""
        # Reset scale for all objects
        for i, rig in enumerate(self.object_rigs):
            current_pos = rig.local_position  # Store position
            rig._matrix = Matrix.make_identity()  # Reset matrix (also resets scale)
            rig.set_position(current_pos)  # Reapply position
            rig.scale(1)  # Ensure scale is 1
            
            # Reset spotlight colors
            if hasattr(self, 'spotlights') and i < len(self.spotlights):
                spotlight_colors = [
                    [1.0, 1.0, 1.0],  # White for all spotlights
                    [1.0, 1.0, 1.0],  # White for all spotlights
                    [1.0, 1.0, 1.0],  # White for all spotlights
                    [1.0, 1.0, 1.0]   # White for all spotlights
                ]
                spotlight = self.spotlights[i]
                # Ensure spotlight._color has only RGB components (no alpha)
                spotlight._color = spotlight_colors[i][:3] if len(spotlight_colors[i]) > 3 else spotlight_colors[i]
                # Update the cone material if it exists
                if spotlight.visual_cone:
                    # Ensure baseColor only gets RGB components
                    rgb_color = spotlight_colors[i][:3] if len(spotlight_colors[i]) > 3 else spotlight_colors[i]
                    spotlight.visual_cone.material.uniform_dict["baseColor"].data = rgb_color
    
    def handle_selection_input(self, input_handler):
        """
        Process input for the selection phase.
        
        Parameters:
            input_handler: Input handling object
        
        Returns:
            True if phase should change to gameplay, False otherwise
        """
        key_pressed = False
        phase_changed = False
        
        if input_handler.is_key_down('left'):
            # Move selection left (with wrap-around)
            self.highlighted_index = (self.highlighted_index - 1) % len(self.object_rigs)
            key_pressed = True
            
        if input_handler.is_key_down('right'):
            # Move selection right (with wrap-around)
            self.highlighted_index = (self.highlighted_index + 1) % len(self.object_rigs)
            key_pressed = True
            
        # Update the highlighted object if a key was pressed
        if key_pressed:
            self.highlight_selected_object()
            
        # Check if Enter key is pressed to confirm selection
        if input_handler.is_key_down('return'):
            # Set the active object to the currently highlighted one
            self.active_object_rig = self.object_rigs[self.highlighted_index]
            
            # Transition to gameplay phase
            selected_index = self.setup_gameplay_phase()
            phase_changed = True
            
        return phase_changed, self.highlighted_index 