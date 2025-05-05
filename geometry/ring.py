import numpy as np
from geometry.parametric import ParametricGeometry

class RingGeometry(ParametricGeometry):
    def __init__(self, inner_radius=0.8, outer_radius=1.0, segments=32):
        """
        Creates a flat ring (annulus) geometry on the XY plane.

        Args:
            inner_radius (float): The inner radius of the ring.
            outer_radius (float): The outer radius of the ring.
            segments (int): The number of segments used to approximate the ring.
        """
        def S(u, v):
            radius = inner_radius + v * (outer_radius - inner_radius)
            x = radius * np.cos(u * 2 * np.pi)
            y = radius * np.sin(u * 2 * np.pi)
            z = 0  # Flat on XY plane
            return [x, y, z]

        super().__init__(0, 1, segments, 0, 1, segments, S) 