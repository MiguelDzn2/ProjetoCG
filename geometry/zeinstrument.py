from geometry.geometry import Geometry

class ZeGeometry(Geometry):
    def __init__(self, width=1, height=1, depth=1, positions=None, uvs=None, vertex_normals=None):
        super().__init__()
        # positions, uvs, vertex_normals are expected to be flat lists of coordinates
        # from the load_multimaterial_from_object loader. The Attribute class handles grouping.

        if positions is None: positions = []
        if uvs is None: uvs = []
        if vertex_normals is None: vertex_normals = [] # Initialize to empty list if None

        self.add_attribute("vec3", "vertexPosition", positions)
        self.add_attribute("vec2", "vertexUV", uvs)
        self.add_attribute("vec3", "vertexNormal", vertex_normals) # Add normals
        
        # Vertex count is automatically handled by the Geometry base class
        # when vertexPosition is added. 