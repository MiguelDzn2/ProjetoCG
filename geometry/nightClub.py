import os
from core.obj_reader2 import load_multimaterial_from_object
from extras.movement_rig import MovementRig
from core_ext.mesh import Mesh
from core_ext.texture import Texture
from material.phong import PhongMaterial
from geometry.geometry import Geometry
from light.ambient import AmbientLight
from light.directional import DirectionalLight
from light.point import PointLight
import config

class NightClub:
    def __init__(self, scene, obj_file_path="geometry/nightClub.obj", position=[0, -2.5, 10], scale_factor=3,num_lights=None):
        """
        Carrega o modelo 3D do nightclub com materiais PhongMaterial realistas,
        configura iluminação adequada e o adiciona à cena.
        """
        #print("Initializing NightClub object with realistic Phong materials...")
        self.rig = MovementRig()
        self.scene = scene
        self.lights = []  # Armazenar referências das luzes criadas

        # Verifica se o ficheiro OBJ existe
        if not os.path.exists(obj_file_path):
            return

        # Não configurar iluminação própria, usar as luzes do sistema principal
        # self._setup_nightclub_lighting()

        # Adiciona o rig à cena ANTES de carregar as partes
        self.scene.add(self.rig)

        # Chama a função de carregamento multi-material
        nightclub_parts = load_multimaterial_from_object(obj_file_path)

        if not nightclub_parts:
            #print(f"Error: Could not load nightclub parts from {obj_file_path}.")
            if self.rig in self.scene.descendant_list:
                self.scene.remove(self.rig)
            return
        else:
            parts_loaded_successfully = 0
            # Ajustar para o número total de luzes do sistema
            # 1 Ambient + 1 Directional + 2 SpotLights = 4 luzes
            num_light_sources = config.NUM_SCENE_LIGHTS
            
            for part_data in nightclub_parts:
                try:
                    material_name = part_data.get('material_name', 'Unknown')
                    texture_path = part_data.get('texture_path')
                    geometry_data = part_data.get('geometry_data')

                    if not geometry_data:
                        #print(f"  Warning: Skipping part '{material_name}' due to missing geometry data.")
                        continue

                    # Criar Geometria para esta parte
                    geometry = Geometry()
                    geometry.add_attribute("vec3", "vertexPosition", geometry_data['vertices'])
                    geometry.add_attribute("vec2", "vertexUV", geometry_data['uvs'])
                    
                    # Adicionar normais se disponíveis
                    if 'normals' in geometry_data and geometry_data['normals']:
                        geometry.add_attribute("vec3", "vertexNormal", geometry_data['normals'])

                    if geometry.vertex_count == 0:
                        #print(f"    Warning: Geometry for material '{material_name}' has 0 vertices. Skipping mesh part.")
                        continue

                    # Criar Material PhongMaterial realista
                    if texture_path and os.path.exists(texture_path):
                        # Material com textura
                        texture = Texture(file_name=texture_path)
                        num_light_sources = config.NUM_SCENE_LIGHTS

                        material = PhongMaterial(
                            number_of_light_sources=num_light_sources,
                            texture=texture,
                            property_dict=config.NIGHTCLUB_MATERIAL_PROPERTIES.copy()
                        )
                        #print(f"    Created textured Phong material for '{material_name}' with texture: {texture_path}")
                    else:
                        # Material sem textura (cor base)
                        material_properties = config.NIGHTCLUB_MATERIAL_PROPERTIES.copy()
                        material_properties["baseColor"] = self._get_material_color(material_name)
                        material = PhongMaterial(
                            number_of_light_sources=num_light_sources,  # Primeiro
                            property_dict=material_properties           # Segundo (sem textura)
                        )
                        #print(f"    Created colored Phong material for '{material_name}' (no texture)")

                    # Criar Mesh e adicioná-lo ao Rig do nightclub
                    mesh = Mesh(geometry, material)
                    self.rig.add(mesh)
                    parts_loaded_successfully += 1

                except Exception as e:
                    #print(f"  Error processing part for material {part_data.get('material_name', 'Unknown')}: {e}")
                    import traceback
                    traceback.print_exc()

            if parts_loaded_successfully > 0:
                # Configurar a posição/escala do rig completo
                self.rig.set_position(position)
                self.rig.scale(scale_factor)
                #print(f"NightClub setup complete with realistic Phong materials. {parts_loaded_successfully} parts added with {num_light_sources} light sources.")
            else:
               # print("Nightclub setup failed: No parts were loaded successfully.")
                if self.rig in self.scene.descendant_list:
                    self.scene.remove(self.rig)
                # Remover luzes se não há partes
                self._remove_nightclub_lighting()

    def _get_material_color(self, material_name):
        """
        Retorna uma cor apropriada baseada no nome do material.
        """
        material_name_lower = material_name.lower()
        
        # Cores específicas baseadas no tipo de material
        if "floor" in material_name_lower:
            return [0.3, 0.2, 0.1]  # Marrom escuro para o chão
        elif "wall" in material_name_lower:
            return [0.6, 0.5, 0.4]  # Bege para paredes
        elif "bar" in material_name_lower:
            return [0.4, 0.2, 0.1]  # Madeira escura para o bar
        elif "speaker" in material_name_lower:
            return [0.1, 0.1, 0.1]  # Preto para colunas
        elif "light" in material_name_lower:
            return [0.9, 0.9, 0.7]  # Amarelo claro para luzes
        elif "door" in material_name_lower:
            return [0.3, 0.2, 0.1]  # Madeira escura para portas
        elif "table" in material_name_lower:
            return [0.5, 0.3, 0.2]  # Madeira média para mesas
        elif "bench" in material_name_lower or "seat" in material_name_lower:
            return [0.2, 0.1, 0.4]  # Roxo escuro para assentos
        elif "dj" in material_name_lower:
            return [0.1, 0.1, 0.1]  # Preto para equipamento DJ
        elif "glass" in material_name_lower:
            return [0.8, 0.9, 1.0]  # Azul claro para vidro
        else:
            return [0.5, 0.5, 0.5]  # Cinza neutro para materiais desconhecidos

    def get_rig(self):
        """Retorna o rig principal do nightclub para manipulação externa."""
        return self.rig

    def get_lights(self):
        """Retorna a lista de luzes criadas para o nightclub."""
        return self.lights.copy()
