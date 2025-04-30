from geometry.geometry import Geometry
import numpy as np

class NightClubGeometry(Geometry):
    def __init__(self, width=2, height=2, depth=1, vertices=[], uv_data=[]):
        super().__init__()
        position_data = vertices
        self.add_attribute("vec3", "vertexPosition", position_data)
        self.add_attribute("vec2", "vertexUV", uv_data)
        self.count_vertices()