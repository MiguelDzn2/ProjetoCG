from geometry.geometry import Geometry
import numpy as np


class BrandonGeometry(Geometry):
    def __init__(self, width=1, height=1, depth=1, verticesAgogo=[], uv_data=[]):
        super().__init__()

        # Cada lado consiste em dois triângulos
        position_data = verticesAgogo

        # Usa as coordenadas UV fornecidas
        self.add_attribute("vec3", "vertexPosition", position_data)
        self.add_attribute("vec2", "vertexUV", uv_data)
        # Vertex count is handled by add_attribute