import math
import uuid
import random
from geometry.arrow import Arrow
from config import ARROW_START_POSITION, ARROW_SPAWN_INTERVAL

class ArrowManager:
    def __init__(self, scene, target_ring, debug_mode=False):
        self.scene = scene
        self.target_ring = target_ring
        self.arrows = []
        self.arrow_spawn_timer = 0
        self.arrow_spawn_interval = ARROW_SPAWN_INTERVAL
        self.processed_arrow_uuids = []
        self.current_waiting_arrow_id = None
        self.debug_mode = debug_mode
        
    def create_single_arrow(self):
        """Creates a single arrow with random orientation"""
        possible_angles = [0, 90, 180, 270]
        angle = random.choice(possible_angles)
        
        arrow = Arrow(color=[1.0, 0.0, 0.0], offset=[0, 0, 0], debug_mode=self.debug_mode)
        arrow.add_to_scene(self.scene)
        arrow.rotate(math.radians(angle), 'z')
        
        # Set arrow at hardcoded position
        arrow.set_position(ARROW_START_POSITION)
        
        # Generate a unique ID for this arrow
        arrow.unique_id = str(uuid.uuid4())
        
        return arrow

    def update_arrow_spawning(self, delta_time):
        """Updates the timer and creates new arrows when needed"""
        self.arrow_spawn_timer += delta_time
        if self.arrow_spawn_timer >= self.arrow_spawn_interval:
            self.arrow_spawn_timer = 0
            self.arrows.append(self.create_single_arrow())

    def check_arrow_ring_collision(self, arrow, is_arrow_key_pressed):
        """
        Checks if an arrow is inside the ring.
        Returns:
        - 1: Arrow is completely inside the ring (both body and tip)
        - 0.5: Arrow is partially inside the ring (only part of body or tip)
        - 0: Arrow is outside the ring
        """
        # If arrow has been marked as ineligible for detection, immediately return 0
        if hasattr(arrow, 'ineligible_for_detection') and arrow.ineligible_for_detection:
            return 0
            
        # If this arrow has already been processed, return its saved collision value
        if hasattr(arrow, 'unique_id') and arrow.unique_id in self.processed_arrow_uuids:
            return arrow.collision_value if hasattr(arrow, 'collision_value') else 0
            
        # Get positions of ring
        ring_pos = self.target_ring.global_position
        
        # Get the inner and outer radius of the ring, adjusted by the scale factor
        inner_radius = self.target_ring.geometry.inner_radius * self.target_ring.scale_factors[0]
        outer_radius = self.target_ring.geometry.outer_radius * self.target_ring.scale_factors[0]
        
        # Get arrow's bounding rectangle
        min_x, min_z, max_x, max_z = arrow.get_bounding_rect()
        
        # Get arrow position
        arrow_pos = arrow.rig.local_position
        
        # IMPORTANT CORRECTION: The ring is vertical, so we need to check in the XY plane, not XZ plane
        # For a vertical ring in the ZY plane, we use the Z coordinate of the arrow for distance calculation
        # Calculate distance between arrow center and ring center in the XZ plane (vertical ring)
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
            is_arrow_key_pressed and 
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
                collision_result = self.check_arrow_ring_collision(arrow, is_arrow_key_pressed)
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