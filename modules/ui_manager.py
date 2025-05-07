"""
UI manager module for handling user interface elements.
"""

from geometry.rectangle import RectangleGeometry
from extras.text_texture import TextTexture
from material.texture import TextureMaterial
from core_ext.mesh import Mesh
from extras.movement_rig import MovementRig
from core_ext.texture import Texture

class UIManager:
    """
    Manages UI elements like score display, streak counter, and game title.
    """
    
    def __init__(self, scene, camera):
        """
        Initialize the UI manager.
        
        Parameters:
            scene: The scene to add UI elements to
            camera: The camera to attach UI elements to
        """
        self.scene = scene
        self.camera = camera
        self.score = 0
        self.perfect_streak = 0
        self.title_mesh = None
        self.title_rig = None
        self.score_mesh = None
        self.score_rig = None
        self.score_texture = None
        self.streak_mesh = None
        self.streak_rig = None
        self.streak_texture = None
        self.collision_mesh = None
        self.collision_rig = None
        self.collision_texture = None
        self.streak_arrows = []
        
        # Create UI elements
        self._create_score_display()
        self._create_streak_display()
        self._create_collision_display()
        self._create_title_display()
    
    def _create_score_display(self):
        """Create the score display UI element"""
        score_texture = TextTexture(
            text="Score: 0",
            system_font_name="Arial",
            font_size=36,
            font_color=(255, 255, 255),  # White text
            background_color=(0, 0, 0, 128),  # Semi-transparent black background
            transparent=True,
            image_width=300,
            image_height=100,
            align_horizontal=0.0,  # Left-aligned
            align_vertical=0.5,    # Vertically centered
            image_border_width=0,  # Remove border
            image_border_color=(255, 255, 255)  # White border
        )
        score_material = TextureMaterial(texture=score_texture, property_dict={"doubleSide": True})
        score_geometry = RectangleGeometry(width=2, height=0.6)
        self.score_mesh = Mesh(score_geometry, score_material)
        
        # Create the score rig but don't add to scene directly - will be added to camera
        self.score_rig = MovementRig()
        self.score_rig.add(self.score_mesh)
        # Position score relative to camera view
        self.score_rig.set_position([2.6, 1.3, -3])
        
        # Store the score texture for updates
        self.score_texture = score_texture
    
    def _create_streak_display(self):
        """Create the streak display UI element"""
        streak_texture = TextTexture(
            text="Streak: 0",
            system_font_name="Arial",
            font_size=24,
            font_color=(255, 255, 255),  # White text
            background_color=(0, 0, 0, 128),  # Semi-transparent black background
            transparent=True,
            image_width=300,
            image_height=60,
            align_horizontal=0.0,  # Left-aligned
            align_vertical=0.5,    # Vertically centered
            image_border_width=0,  # Remove border
            image_border_color=(255, 255, 255)  # White border
        )
        streak_material = TextureMaterial(texture=streak_texture, property_dict={"doubleSide": True})
        streak_geometry = RectangleGeometry(width=2, height=0.4)
        self.streak_mesh = Mesh(streak_geometry, streak_material)
        
        # Create the streak rig but don't add to scene directly - will be added to camera
        self.streak_rig = MovementRig()
        self.streak_rig.add(self.streak_mesh)
        # Position streak below score
        self.streak_rig.set_position([2.6, 0.8, -3])
        
        # Store the streak texture for updates
        self.streak_texture = streak_texture
    
    def _create_collision_display(self):
        """Create the collision status display UI element"""
        collision_texture = TextTexture(
            text=" ",  # Initially empty
            system_font_name="Arial",
            font_size=48,
            font_color=(255, 255, 0),  # Yellow text
            background_color=(0, 0, 0, 128),
            transparent=True,
            image_width=300,
            image_height=100,
            align_horizontal=0.5,
            align_vertical=0.5,
            image_border_width=0
        )
        collision_material = TextureMaterial(texture=collision_texture, property_dict={"doubleSide": True})
        collision_geometry = RectangleGeometry(width=2, height=0.6)
        self.collision_mesh = Mesh(collision_geometry, collision_material)
        self.collision_rig = MovementRig()
        self.collision_rig.add(self.collision_mesh)
        self.collision_rig.set_position([-2.6, 1.3, -3]) # Position collision status display
        self.collision_texture = collision_texture
    
    def _create_title_display(self):
        """Create the game title display"""
        title_geometry = RectangleGeometry(width=16, height=4)  # Adjust width/height as needed
        title_texture = Texture(file_name="images/game_title_transparent.png")
        title_material = TextureMaterial(texture=title_texture, property_dict={"doubleSide": True}) 
        self.title_mesh = Mesh(title_geometry, title_material)
        self.title_rig = MovementRig()
        self.title_rig.add(self.title_mesh)
        # Title rig position is set when adding to scene
    
    def show_ui_for_selection_phase(self):
        """Configure UI for selection phase"""
        # Remove score and streak displays from camera if present
        if self.score_rig in self.camera.descendant_list:
            self.camera.remove(self.score_rig)
        if self.streak_rig in self.camera.descendant_list:
            self.camera.remove(self.streak_rig)
        if self.collision_rig in self.camera.descendant_list:
            self.camera.remove(self.collision_rig)
        
        # Add title to scene if not already there
        if self.title_rig not in self.scene.descendant_list:
            self.scene.add(self.title_rig)
            # Position title rig
            self.title_rig.set_position([0, 110, 0])
    
    def show_ui_for_gameplay_phase(self):
        """Configure UI for gameplay phase"""
        # Remove title if present
        if self.title_rig in self.scene.descendant_list:
            self.scene.remove(self.title_rig)
        
        # Add score, streak and collision displays to camera if not already there
        if self.score_rig not in self.camera.descendant_list:
            self.camera.add(self.score_rig)
        if self.streak_rig not in self.camera.descendant_list:
            self.camera.add(self.streak_rig)
        if self.collision_rig not in self.camera.descendant_list:
            self.camera.add(self.collision_rig)
        
        # Reset score and streak
        self.reset_score()
    
    def update_score(self, points, is_perfect=False):
        """
        Update the score and related UI elements.
        
        Parameters:
            points: Points to add to the score
            is_perfect: Whether this is a perfect hit (for streak tracking)
        """
        self.score += points
        self.score_texture.update_text(f"Score: {int(self.score)}")
        
        # Handle streak logic
        if is_perfect:
            self.perfect_streak += 1
        else:
            self.perfect_streak = 0
            self.streak_arrows = []
            
        # Show streak with multiplier indicator
        multiplier_text = ""
        if self.perfect_streak >= 10:
            multiplier_text = " (x2.0)"
        elif self.perfect_streak >= 5:
            multiplier_text = " (x1.5)"
            
        self.streak_texture.update_text(f"Streak: {self.perfect_streak}{multiplier_text}")
        
        return self.perfect_streak
    
    def get_score_multiplier(self):
        """Get the current score multiplier based on streak"""
        if self.perfect_streak >= 10:
            return 2.0
        elif self.perfect_streak >= 5:
            return 1.5
        return 1.0
    
    def reset_score(self):
        """Reset score and streak to zero"""
        self.score = 0
        self.perfect_streak = 0
        self.streak_arrows = []
        self.score_texture.update_text(f"Score: {int(self.score)}")
        self.streak_texture.update_text(f"Streak: {self.perfect_streak}")
        self.collision_texture.update_text(" ")
    
    def update_collision_text(self, text):
        """Update the collision status text"""
        self.collision_texture.update_text(text)
    
    def add_arrow_to_streak(self, arrow_id):
        """
        Add arrow to streak tracking.
        
        Parameters:
            arrow_id: Unique ID of the arrow
            
        Returns:
            True if arrow was added, False if already tracked
        """
        if arrow_id not in self.streak_arrows:
            self.streak_arrows.append(arrow_id)
            return True
        return False

    def is_arrow_in_streak(self, arrow_id):
        """Check if arrow is already counted in streak"""
        return arrow_id in self.streak_arrows 