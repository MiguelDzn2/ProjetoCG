import math

from core_ext.object3d import Object3D


class MovementRig(Object3D):
    """
    Add moving forwards and backwards, left and right, up and down (all local translations),
    as well as turning left and right, and looking up and down
    """
    def __init__(self, units_per_second=1, degrees_per_second=60):
        # Initialize base Object3D.
        # Controls movement and turn left/right.
        super().__init__()
        # Initialize attached Object3D; controls look up/down
        self._look_attachment = Object3D()
        self.children_list = [self._look_attachment]
        self._look_attachment.parent = self
        # Control rate of movement
        self._units_per_second = units_per_second
        self._degrees_per_second = degrees_per_second
        
        # Track rotation values for debug display
        self.x_rotation = 0  # Look up/down (pitch)
        self.y_rotation = 0  # Turn left/right (yaw)
        self.z_rotation = 0  # Roll

        # Customizable key mappings.
        # Defaults: W, A, S, D, R, F (move), Q, E (turn), T, G (look)
        self.KEY_MOVE_FORWARDS = "w"
        self.KEY_MOVE_BACKWARDS = "s"
        self.KEY_MOVE_LEFT = "a"
        self.KEY_MOVE_RIGHT = "d"
        self.KEY_MOVE_UP = "r"
        self.KEY_MOVE_DOWN = "f"
        self.KEY_TURN_LEFT = "q"
        self.KEY_TURN_RIGHT = "e"
        self.KEY_LOOK_UP = "t"
        self.KEY_LOOK_DOWN = "g"

    # Adding and removing objects applies to look attachment.
    # Override functions from the Object3D class.
    def add(self, child):
        self._look_attachment.add(child)

    def remove(self, child):
        self._look_attachment.remove(child)

    def update(self, input_object, delta_time):
        move_amount = self._units_per_second * delta_time
        rotate_amount = self._degrees_per_second * (math.pi / 180) * delta_time
        if input_object.is_key_pressed(self.KEY_MOVE_FORWARDS):
            self.translate(0, 0, -move_amount)
        if input_object.is_key_pressed(self.KEY_MOVE_BACKWARDS):
            self.translate(0, 0, move_amount)
        if input_object.is_key_pressed(self.KEY_MOVE_LEFT):
            self.translate(-move_amount, 0, 0)
        if input_object.is_key_pressed(self.KEY_MOVE_RIGHT):
            self.translate(move_amount, 0, 0)
        if input_object.is_key_pressed(self.KEY_MOVE_UP):
            self.translate(0, move_amount, 0)
        if input_object.is_key_pressed(self.KEY_MOVE_DOWN):
            self.translate(0, -move_amount, 0)
        if input_object.is_key_pressed(self.KEY_TURN_RIGHT):
            self.rotate_y(-rotate_amount)
        if input_object.is_key_pressed(self.KEY_TURN_LEFT):
            self.rotate_y(rotate_amount)
        if input_object.is_key_pressed(self.KEY_LOOK_UP):
            self._look_attachment.rotate_x(rotate_amount)
            self.x_rotation += rotate_amount * (180/math.pi)  # Track rotation in degrees
        if input_object.is_key_pressed(self.KEY_LOOK_DOWN):
            self._look_attachment.rotate_x(-rotate_amount)
            self.x_rotation -= rotate_amount * (180/math.pi)  # Track rotation in degrees

    def rotate_y(self, angle):
        """Override rotate_y to track rotation values"""
        self.y_rotation += angle * (180/math.pi)  # Convert to degrees for tracking
        super().rotate_y(angle)
        
    def rotate_x(self, angle):
        """Override rotate_x to track rotation values"""
        self.x_rotation += angle * (180/math.pi)  # Convert to degrees for tracking
        super().rotate_x(angle)
        
    def rotate_z(self, angle):
        """Override rotate_z to track rotation values"""
        self.z_rotation += angle * (180/math.pi)  # Convert to degrees for tracking
        super().rotate_z(angle)

    def get_rotation_values(self):
        """Return rotation values in degrees for debugging"""
        return {
            'x': self.x_rotation,  # Pitch (look up/down)
            'y': self.y_rotation,  # Yaw (turn left/right)
            'z': self.z_rotation   # Roll
        }
