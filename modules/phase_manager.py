"""
Phase manager module for handling game phase transitions and setup.
"""

import math
from game_phases import GamePhase
from light.ambient import AmbientLight
from light.directional import DirectionalLight
from light.spotlight import SpotLight
from core.matrix import Matrix
from config import (
    CAMERA_INITIAL_POSITION, CAMERA_INITIAL_ROTATION,
    SELECTION_PHASE_OBJECTS_Y, SELECTION_PHASE_CAMERA_POSITION,
    SELECTION_PHASE_POSITIONS, SELECTION_PHASE_SPOTLIGHT_Y_OFFSET,
    SELECTION_PHASE_SPOTLIGHT_COLORS, SELECTION_PHASE_SPOTLIGHT_BRIGHTNESS_MULTIPLIER,
    SELECTION_PHASE_BACKGROUND_POSITION, SELECTION_PHASE_BACKGROUND_WIDTH,
    SELECTION_PHASE_BACKGROUND_HEIGHT, SELECTION_PHASE_BACKGROUND_IMAGE,
    GAMEPLAY_PHASE_POSITIONS, GAMEPLAY_PHASE_ROTATIONS,
    GAMEPLAY_SELECTED_INSTRUMENT_POSITION, GAMEPLAY_SELECTED_INSTRUMENT_POSITIONS,
    CAMERA_WAYPOINTS, SELECTION_PHASE_LIGHTS
)
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
        
        # Add background with configured background image
        if self.background in self.scene.descendant_list:
            self.scene.remove(self.background)
        # Also check if attached to camera and remove
        if self.background in self.camera_rig.descendant_list:
            self.camera_rig.remove(self.background)
            
        # Create a rectangle for the background using configured dimensions
        background_geometry = RectangleGeometry(
            width=SELECTION_PHASE_BACKGROUND_WIDTH,
            height=SELECTION_PHASE_BACKGROUND_HEIGHT
        )
        # Load background texture from configured path
        background_texture = Texture(file_name=SELECTION_PHASE_BACKGROUND_IMAGE)
        # Create material with the background texture
        background_material = TextureMaterial(
            texture=background_texture,
            property_dict={
                "doubleSide": True
            }
        )
        # Create mesh for the background
        self.background = Mesh(background_geometry, background_material)
        # Position the background using configured position
        self.background.set_position(SELECTION_PHASE_BACKGROUND_POSITION)
        # Add the background to the scene
        self.scene.add(self.background)

        # Reset camera transform first
        self.camera_rig._matrix = Matrix.make_identity()
        # Position camera high up and facing "backwards" to see all objects
        self.camera_rig.set_position(SELECTION_PHASE_CAMERA_POSITION)
        
        # Reset all objects to their original positions and rotations with increased spacing, high up
        for i, rig in enumerate(self.object_rigs):
            # Reset the transformation matrix to identity
            rig._matrix = Matrix.make_identity()
            # Set the initial position
            rig.set_position(SELECTION_PHASE_POSITIONS[i])
            # Reset the scale (as highlight_selected_object changes it)
            rig.scale(1)  # Scale back to 1

        # Add lights based on configuration
        for light_cfg in SELECTION_PHASE_LIGHTS:
            if light_cfg['type'] == 'ambient':
                light = AmbientLight(color=light_cfg['color'])
                if 'position' in light_cfg:
                    light.set_position(light_cfg['position'])
                self.scene.add(light)
            elif light_cfg['type'] == 'directional':
                light = DirectionalLight(color=light_cfg['color'], direction=light_cfg['direction'])
                self.scene.add(light)
            elif light_cfg['type'] == 'spot':
                light = SpotLight(
                    color=light_cfg.get('color', [1,1,1]),
                    position=light_cfg.get('position', [0,10,0]),
                    direction=light_cfg.get('direction', [0,-1,0]),
                    angle=light_cfg.get('angle', 30),
                    cone_visible=light_cfg.get('cone_visible', True),
                    cone_opacity=light_cfg.get('cone_opacity', 0.5),
                    cone_height=light_cfg.get('cone_height', 8.0)
                )
                self.scene.add(light)

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
        # Also check if the background is a child of the camera_rig
        if self.background in self.camera_rig.descendant_list:
            self.camera_rig.remove(self.background)
        
        # Reset camera transform first
        self.camera_rig._matrix = Matrix.make_identity()
        
        # Get the index of the selected instrument
        selected_index = self.object_rigs.index(self.active_object_rig)
        
        # Get the instrument name based on index
        instrument_names = ["miguel", "ze", "ana", "brandon"]
        if selected_index < len(instrument_names):
            selected_instrument = instrument_names[selected_index]
            print(f"Selected instrument: {selected_instrument}")
        else:
            selected_instrument = "miguel"  # Default fallback
            print(f"Invalid instrument index {selected_index}, defaulting to miguel")
        
        # Get instrument-specific camera waypoints
        if selected_instrument in CAMERA_WAYPOINTS and len(CAMERA_WAYPOINTS[selected_instrument]) > 0:
            first_waypoint = CAMERA_WAYPOINTS[selected_instrument][0]
            # Apply position and rotation from first waypoint
            self.camera_rig.set_position(first_waypoint["position"])
            
            # Apply rotations if needed (convert degrees to radians)
            self.camera_rig.rotate_x(math.radians(first_waypoint["rotation"][0]))
            self.camera_rig.rotate_y(math.radians(first_waypoint["rotation"][1]))
            self.camera_rig.rotate_z(math.radians(first_waypoint["rotation"][2]))
            print(f"Camera positioned at first waypoint for {selected_instrument}: pos={first_waypoint['position']}, rot={first_waypoint['rotation']}")
        else:
            # Fallback to initial position and rotation if no waypoints defined
            self.camera_rig.set_position(CAMERA_INITIAL_POSITION)
            self.camera_rig.rotate_x(math.radians(CAMERA_INITIAL_ROTATION[0]))
            self.camera_rig.rotate_y(math.radians(CAMERA_INITIAL_ROTATION[1]))
            self.camera_rig.rotate_z(math.radians(CAMERA_INITIAL_ROTATION[2]))
            print(f"No waypoints found for {selected_instrument}, using initial camera position and rotation")
        
        # Remove highlighting and reset active object
        self.remove_highlighting()
        self.active_object_rig._matrix = Matrix.make_identity()
        
        # Set position based on which instrument was selected
        self.active_object_rig.set_position(GAMEPLAY_SELECTED_INSTRUMENT_POSITIONS[selected_index])
        
        # Apply positions and rotations based on selection
        for i, rig in enumerate(self.object_rigs):
            if rig != self.active_object_rig:
                rig._matrix = Matrix.make_identity()
                
                # Get position and rotation for this instrument based on which one was selected
                position = GAMEPLAY_PHASE_POSITIONS[selected_index][i]
                rotation = GAMEPLAY_PHASE_ROTATIONS[selected_index][i]
                
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
                    # Increase brightness by specified multiplier
                    brighter_color = [c * SELECTION_PHASE_SPOTLIGHT_BRIGHTNESS_MULTIPLIER for c in SELECTION_PHASE_SPOTLIGHT_COLORS[i]]
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
                    # Get the original color
                    spotlight = self.spotlights[i]
                    # Ensure spotlight._color has only RGB components (no alpha)
                    spotlight._color = SELECTION_PHASE_SPOTLIGHT_COLORS[i][:3] if len(SELECTION_PHASE_SPOTLIGHT_COLORS[i]) > 3 else SELECTION_PHASE_SPOTLIGHT_COLORS[i]
                    # Update the cone material if it exists
                    if spotlight.visual_cone:
                        # Ensure baseColor only gets RGB components
                        rgb_color = SELECTION_PHASE_SPOTLIGHT_COLORS[i][:3] if len(SELECTION_PHASE_SPOTLIGHT_COLORS[i]) > 3 else SELECTION_PHASE_SPOTLIGHT_COLORS[i]
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
                spotlight = self.spotlights[i]
                # Ensure spotlight._color has only RGB components (no alpha)
                spotlight._color = SELECTION_PHASE_SPOTLIGHT_COLORS[i][:3] if len(SELECTION_PHASE_SPOTLIGHT_COLORS[i]) > 3 else SELECTION_PHASE_SPOTLIGHT_COLORS[i]
                # Update the cone material if it exists
                if spotlight.visual_cone:
                    # Ensure baseColor only gets RGB components
                    rgb_color = SELECTION_PHASE_SPOTLIGHT_COLORS[i][:3] if len(SELECTION_PHASE_SPOTLIGHT_COLORS[i]) > 3 else SELECTION_PHASE_SPOTLIGHT_COLORS[i]
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

