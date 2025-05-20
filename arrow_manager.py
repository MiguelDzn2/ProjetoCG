import math
import uuid
import random
from geometry.arrow import Arrow
import config # Import config to access ARROW_TYPE constants

# Constants from config.py (consider direct import for clarity if only a few are needed)
# Example: from config import ARROW_SPAWN_INTERVAL, ARROW_START_POSITION, ARROW_COLOR, ARROW_UNITS_PER_SECOND
# For now, using config.X to access them.
ARROW_SPAWN_INTERVAL = config.ARROW_SPAWN_INTERVAL

class ArrowManager:
    """Manages the creation, tracking, and lifecycle of arrows in the game."""
    def __init__(self, scene, target_ring, arrow_ring_pivot, debug_mode=False):
        """Initialize the ArrowManager.

        Args:
            scene: The main scene object to add arrows to.
            target_ring: The target ring object for collision detection.
            arrow_ring_pivot: The MovementRig that serves as the pivot for arrows and the ring.
            debug_mode (bool): Flag to enable debug features.
        """
        self.scene = scene  # Keep scene reference for now, though arrows are added to pivot
        self.target_ring = target_ring
        self.arrow_ring_pivot = arrow_ring_pivot # Store reference to the pivot
        self.arrows = []
        self.arrow_spawn_timer = 0.0
        self.arrow_spawn_interval = ARROW_SPAWN_INTERVAL
        self.processed_arrow_uuids = []
        self.current_waiting_arrow_id = None
        self.debug_mode = debug_mode
        
    def create_single_arrow(self, arrow_type_str=None):
        """Creates a single arrow with a specified or random orientation, as a child of the pivot."""
        # Determine angle for the arrow
        angle_degrees = self._get_arrow_angle(arrow_type_str)

        arrow = Arrow(
            color=config.ARROW_COLOR, 
            offset=[0,0,0], # Offset is handled by ARROW_START_POSITION relative to pivot
            debug_mode=self.debug_mode,
            speed=config.ARROW_UNITS_PER_SECOND
        )
        
        # Add arrow's rig to the arrow_ring_pivot instead of the main scene
        self.arrow_ring_pivot.add(arrow.rig)
        
        arrow.rotate(math.radians(angle_degrees), 'z')
        
        # Set arrow position relative to the pivot
        arrow.set_position(list(config.ARROW_START_POSITION))
        
        # Generate a unique ID for this arrow
        arrow.unique_id = str(uuid.uuid4())
        
        # Add to internal tracking list
        # self.arrows.append(arrow) # This will be done by music_system or update_arrow_spawning
        print(f"Created Arrow[{arrow.unique_id}] at {config.ARROW_START_POSITION} relative to pivot, angle: {angle_degrees}")
        return arrow

    def _get_arrow_angle(self, arrow_type_str=None):
        """Determines the arrow's rotation angle based on type string or randomly."""
        if arrow_type_str:
            arrow_type_str_lower = arrow_type_str.lower()
            if arrow_type_str_lower in config.ARROW_TYPE_NAMES:
                return config.ARROW_TYPE_NAMES[arrow_type_str_lower]
            else:
                print(f"Warning: Unknown arrow_type_str '{arrow_type_str}'. Defaulting to UP (0 degrees).")
                return config.ARROW_TYPE_UP  # Default to UP
        else:
            # If no type specified, choose a random one
            possible_angles = [
                config.ARROW_TYPE_UP, 
                config.ARROW_TYPE_LEFT, 
                config.ARROW_TYPE_DOWN, 
                config.ARROW_TYPE_RIGHT
            ]
            return random.choice(possible_angles)

    def update_arrow_spawning(self, delta_time):
        """Updates the timer and creates new arrows when needed"""
        self.arrow_spawn_timer += delta_time
        if self.arrow_spawn_timer >= self.arrow_spawn_interval:
            self.arrow_spawn_timer = 0
            self.arrows.append(self.create_single_arrow())

    def check_arrow_ring_collision(self, arrow):
        """Check for collision between an arrow and the target ring, using pivot-relative positions."""
        # If arrow has been marked as ineligible for detection, immediately return 0
        if hasattr(arrow, 'ineligible_for_detection') and arrow.ineligible_for_detection:
            return 0
            
        # If this arrow has already been processed, return its saved collision value
        if hasattr(arrow, 'unique_id') and arrow.unique_id in self.processed_arrow_uuids:
            return arrow.collision_value if hasattr(arrow, 'collision_value') else 0
            
        # Use local_position of the target_ring, which is relative to the arrow_ring_pivot
        ring_pos = self.target_ring.local_position 
        
        # Ring radii are based on its geometry and scale, assumed to be correct in local space
        inner_radius = self.target_ring.geometry.inner_radius * self.target_ring.scale_factors[0]
        outer_radius = self.target_ring.geometry.outer_radius * self.target_ring.scale_factors[0]
        
        # Arrow's bounding rectangle should be in its local space or compatible pivot space
        min_x, min_z, max_x, max_z = arrow.get_bounding_rect() # Assuming this gives local coords or pivot-relative
        
        # Arrow's position is also local to its parent (the pivot)
        arrow_pos = arrow.rig.local_position
        
        # Calculate distance between arrow center and ring center (all in pivot's local XZ plane)
        dx = arrow_pos[0] - ring_pos[0]
        dz = arrow_pos[2] - ring_pos[2]  # Use Z coordinate for vertical ring
        center_distance = math.sqrt(dx*dx + dz*dz)
        
        # Calculate the corner points of the bounding rectangle
        # For a vertical ring, we need the points in the XZ plane
        corner_points = [
            (min_x, min_z),  # Bottom-left
            (max_x, min_z),  # Bottom-right
            (max_x, max_z),  # Top-right
            (min_x, max_z)   # Top-left
        ]
        
        # Calculate distances from each corner of the bounding box to the ring center
        corner_distances = []
        for corner_x, corner_z in corner_points:
            # Use XZ distance for vertical ring
            dist = math.sqrt((corner_x - ring_pos[0])**2 + (corner_z - ring_pos[2])**2)
            corner_distances.append(dist)
        
        # Visual debug: Update corner markers if in debug mode and the arrow has debug corner markers
        if self.debug_mode and hasattr(arrow, 'debug_corner_markers'):
            for i, ((corner_x, corner_z), dist) in enumerate(zip(corner_points, corner_distances)):
                # Determine color based on whether the corner is inside inner ring, outer ring, or outside
                if dist < inner_radius:
                    color = [0, 1, 0]  # Green for inside inner ring
                elif dist < outer_radius:
                    color = [1, 1, 0]  # Yellow for between inner and outer ring
                else:
                    color = [1, 0, 0]  # Red for outside
                
                # Update marker position and color
                marker = arrow.debug_corner_markers[i]
                # For visual debug, place markers in 3D space at their actual positions
                marker.set_position([corner_x, arrow_pos[1], corner_z])
                marker.material.set_properties({"baseColor": color})
        
        # Check if arrow has passed the ring completely (still using X coordinate)
        has_passed_ring = min_x > ring_pos[0] + outer_radius
        
        # Reset waiting state if arrow has passed the ring completely
        if has_passed_ring and hasattr(arrow, 'waiting_for_keypress') and arrow.waiting_for_keypress:
            arrow.waiting_for_keypress = False
            print(f"Arrow[{arrow.unique_id}]: Stopped waiting - passed ring completely")
        
        # First check if arrow has passed the ring without colliding
        if has_passed_ring:
            # If arrow is marked as scored, it collided at some point
            if hasattr(arrow, 'scored') and arrow.scored:
                # Return the previously determined score
                return arrow.collision_value if hasattr(arrow, 'collision_value') else 0
            else:
                # Arrow passed without colliding
                return 0
        
        # Determine collision status
        # Perfect hit: all corners of the bounding box are inside the inner ring
        all_corners_in_inner = all(dist < inner_radius for dist in corner_distances)
        
        # Partial hit: at least one corner is inside the outer ring
        any_corner_in_outer = any(dist < outer_radius for dist in corner_distances)
        
        # Calculate potential collision value
        if all_corners_in_inner:
            arrow.potential_collision_value = 1
        elif any_corner_in_outer:
            arrow.potential_collision_value = 0.5
        else:
            arrow.potential_collision_value = 0
        
        # Initialize collision checked flag if it doesn't exist
        if not hasattr(arrow, 'collision_checked'):
            arrow.collision_checked = False
            
        # Only register a collision if all conditions are met
        if (arrow.potential_collision_value > 0 and 
            not arrow.collision_checked and
            not (hasattr(arrow, 'ineligible_for_detection') and arrow.ineligible_for_detection)):
            
            # Mark that collision has been checked while key is pressed
            arrow.collision_checked = True
            # Store the collision value for scoring
            arrow.collision_value = arrow.potential_collision_value
            
            # Add this arrow to the processed list to prevent future changes
            if hasattr(arrow, 'unique_id') and arrow.unique_id not in self.processed_arrow_uuids:
                self.processed_arrow_uuids.append(arrow.unique_id)
                
            return arrow.collision_value
            
        return 0

    def handle_arrows(self, delta_time, is_arrow_key_pressed):
        """Updates all arrows and handles their collisions"""
        # Update arrow spawning
        self.update_arrow_spawning(delta_time)

        # Track arrows to remove
        arrows_to_remove = []
        
        # Get ring position for distance calculations
        ring_pos = self.target_ring.global_position
        arrow_distances = []
        
        # Track if we have a new arrow entering the waiting state
        new_waiting_arrow_found = False
        latest_waiting_arrow_id = None
        
        # First pass: update positions and calculate distances
        for i, arrow in enumerate(self.arrows):
            # Update arrow position with delta_time
            arrow.update(delta_time)
            
            # Reset collision_checked flag when no arrow keys are pressed
            if not is_arrow_key_pressed and hasattr(arrow, 'collision_checked'):
                arrow.collision_checked = False
            
            # Calculate distance to ring
            arrow_pos = arrow.rig.local_position
            dx = arrow_pos[0] - ring_pos[0]
            dz = arrow_pos[2] - ring_pos[2]
            distance = math.sqrt(dx*dx + dz*dz)
            
            arrow_distances.append((i, distance, arrow))
            
            # Check if arrow should be removed
            if not arrow.isVisible():
                arrows_to_remove.append(i)
        
        # Sort arrows by distance to ring
        arrow_distances.sort(key=lambda x: x[1])
        
        # Only process the two nearest arrows
        nearest_arrows = arrow_distances[:2] if len(arrow_distances) >= 2 else arrow_distances
        
        # Process collisions for nearest arrows
        collision_results = []
        for idx, distance, arrow in nearest_arrows:
            if not (hasattr(arrow, 'ineligible_for_detection') and arrow.ineligible_for_detection):
                collision_result = self.check_arrow_ring_collision(arrow)
                if collision_result > 0:
                    collision_results.append((arrow, collision_result))
        
        # Remove arrows marked for removal
        for i in sorted(arrows_to_remove, reverse=True):
            if i < len(self.arrows):
                arrow = self.arrows[i]
                if hasattr(arrow, 'unique_id') and self.current_waiting_arrow_id == arrow.unique_id:
                    self.current_waiting_arrow_id = None
                    
                if hasattr(arrow, 'unique_id') and arrow.unique_id in self.processed_arrow_uuids:
                    if not hasattr(arrow, 'scored') or not arrow.scored:
                        self.processed_arrow_uuids.remove(arrow.unique_id)
                        
                self.arrows.pop(i)
                arrow.rig.parent.remove(arrow.rig)
                del arrow
        
        return collision_results 

    def create_random_arrow(self, arrow_type=None):
        """Create an arrow with random type at the spawn position"""
        # Choose a random arrow type if none is specified
        if arrow_type is None:
            arrow_type = random.choice([
                Game.ARROW_TYPE_UP,
                Game.ARROW_TYPE_DOWN,
                Game.ARROW_TYPE_LEFT,
                Game.ARROW_TYPE_RIGHT
            ])
        
        # Convert arrow_type values to fixed angles for better readability
        angle_map = {
            Game.ARROW_TYPE_UP: 0,
            Game.ARROW_TYPE_DOWN: 180,
            Game.ARROW_TYPE_LEFT: 90,
            Game.ARROW_TYPE_RIGHT: 270
        }
        
        # Use the angle_map to get a consistent angle for each arrow type
        # Defaulting to 0 degrees if the arrow_type doesn't match (shouldn't happen)
        angle = angle_map.get(arrow_type, 0)
        
        # Create arrow with the specific angle and ensure color is RGB only (3 components)
        arrow = Arrow(color=[1.0, 0.0, 0.0], offset=[0, 0, 0], debug_mode=self.debug_mode)
        
        # Set arrow angle based on the type
        arrow.rotate(math.radians(angle))
        
        # Set position at the spawn point
        arrow.set_position(self.spawn_position)
        
        # Add to the scene
        arrow.add_to_scene(self.scene)
        
        # Return the arrow for tracking
        return arrow 