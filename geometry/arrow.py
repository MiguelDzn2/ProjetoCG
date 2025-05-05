import math
from geometry.rectangle import RectangleGeometry
from geometry.polygon import PolygonGeometry
from material.surface import SurfaceMaterial
from core_ext.mesh import Mesh
from extras.movement_rig import MovementRig
from core.matrix import Matrix

class Arrow:
    SPEED = 0.01
    RESET_POSITION=10
    
    def __init__(
        self,
        color=[1.0, 0.0, 0.0],
        offset=[0, 0, 0],
        size=0.8,
        angle=0.0,
        axis='z'
    ):
        self.attribute_dict = {
            "vertexPosition": None,
            "vertexColor": None,
            "vertexUV": None
        }
        body_width = 0.2 * size
        body_height = 0.6 * size
        tip_radius = 0.3 * size

        # Criação da geometria combinada (corpo + ponta)
        self.rig = MovementRig()

        # Calcula dimensões precisas
        triangle_height = tip_radius * math.cos(math.pi/6)
        total_height = body_height + triangle_height

        # Posiciona o corpo (retângulo) na parte inferior
        body_geometry = RectangleGeometry(width=body_width, height=body_height)
        body_material = SurfaceMaterial(property_dict={"baseColor": color})
        body_mesh = Mesh(body_geometry, body_material)
        body_mesh.set_position([0, -total_height/2 + body_height/2, 0])
        self.rig.add(body_mesh)
        self.body_mesh = body_mesh  # Save reference to body
        
        # Posiciona a ponta (triângulo) na parte superior
        tip_geometry = PolygonGeometry(sides=3, radius=tip_radius)
        tip_material = SurfaceMaterial(property_dict={"baseColor": color})
        tip_mesh = Mesh(tip_geometry, tip_material)
        tip_mesh.rotate_z(math.pi/2)  # Orientação padrão
        tip_mesh.set_position([0, total_height/2 - triangle_height/3, 0])
        self.rig.add(tip_mesh)
        tip_mesh.rotate_z(math.pi*2)
        
        # Posição ajustada considerando o centro do triângulo
        triangle_center_offset = tip_radius * math.cos(math.pi/6)  # Altura do triângulo equilátero
        tip_mesh.set_position([0, body_height/2 + triangle_center_offset/3, 0])
        self.rig.add(tip_mesh)
        self.tip_mesh = tip_mesh  # Save reference to tip

        # Initialize movement attributes
        self.direction = 1  # Movement direction (1 for right, -1 for left)
        self.initial_y = 1  # Initial Y position
        self.fall_speed = 0 # Speed of Y decrease
        self.is_visible = True  # Add this line to track visibility
        
        # Aplicar rotação inicial se especificado
        if angle != 0.0:
            self.rotate(angle, axis)
        else:
            # Rotação padrão para 0 graus
            self.rig.rotate_z(0)
            
        self.offset = offset
        self.position_increment = 0.0001
        self.rotate(0)

    def add_to_scene(self, scene):
        scene.add(self.rig)

    def set_position(self, position):
        self.rig.set_position(position)
        
    def rotate(self, angle, axis='z'):
        """Rotaciona la flecha en el eje especificado (z por defecto)"""
        if axis == 'x':
            self.rig.rotate_x(angle)
        elif axis == 'y':
            self.rig.rotate_y(angle)
        else:  # Por defecto rotación en Z
            self.rig.rotate_z(angle)

    def update(self):
        """Atualiza o movimento da seta"""
        current_pos = self.rig.local_position
        
        # Define the absolute stopping X-coordinate (moved further to allow arrows to pass through the ring)
        arrow_stop_x = 4.0
        
        # Only update position if the arrow hasn't reached the stopping point
        if current_pos[0] < arrow_stop_x:
            new_x = current_pos[0] + self.SPEED * self.direction
            # Ensure the arrow doesn't overshoot the arrow_stop_x
            new_x = min(new_x, arrow_stop_x)
            self.rig.set_position([new_x, current_pos[1], current_pos[2]])
        else:
            # Mark the arrow as not visible once it reaches or passes arrow_stop_x
            self.is_visible = False

    def get_rotation_angle(self):
        """Obtém o ângulo de rotação atual da seta em graus"""
        # Extrai a rotação Z da matriz de transformação
        rotation_z = math.atan2(self.rig._matrix[1][0], self.rig._matrix[0][0])
        # Converte de radianos para graus
        return math.degrees(rotation_z) % 360

    def set_speed(self, speed):
        """Define a velocidade da seta"""
        self.SPEED = speed
        
    def increment_speed(self, increment):
        """Incrementa a velocidade da seta"""
        self.SPEED += increment

    def set_reset_position(self, position):
        """Define a posição de reset da seta"""
        self.RESET_POSITION = position
        
    def isVisible(self):
        return self.is_visible
        
    def change_color(self, color):
        """Changes the color of both parts of the arrow"""
        # Change body color
        if hasattr(self, 'body_mesh') and self.body_mesh:
            # Update the existing material's color property using set_properties (note: plural)
            self.body_mesh.material.set_properties({"baseColor": color})
            
        # Change tip color
        if hasattr(self, 'tip_mesh') and self.tip_mesh:
            # Update the existing material's color property using set_properties (note: plural)
            self.tip_mesh.material.set_properties({"baseColor": color})


