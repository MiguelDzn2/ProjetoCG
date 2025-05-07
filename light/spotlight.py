from light.light import Light


class SpotLight(Light):
    def __init__(self,
                 color=(1, 1, 1),
                 position=(0, 0, 0),
                 direction=(0, -1, 0),
                 angle=30,
                 attenuation=(1, 0, 0.1)
                 ):
        """
        Initialize a spotlight
        
        Args:
            color: RGB tuple with values between 0 and 1
            position: (x, y, z) tuple for light position
            direction: (x, y, z) tuple for light direction
            angle: spotlight cone angle in degrees
            attenuation: (constant, linear, quadratic) attenuation factors
        """
        # Create a new light type for spotlight (4)
        super().__init__(4)  # We'll use type 4 for spotlight
        self._color = color
        self._attenuation = attenuation
        self.set_position(position)
        self.set_direction(direction)
        self._angle = angle
        
    def set_direction(self, direction):
        """Set the direction of the spotlight."""
        self._direction = direction
        
    @property
    def direction(self):
        """Get the direction of the spotlight."""
        return self._direction
        
    @property
    def angle(self):
        """Get the angle of the spotlight cone in degrees."""
        return self._angle
    
    def set_angle(self, angle):
        """Set the angle of the spotlight cone in degrees."""
        self._angle = angle 