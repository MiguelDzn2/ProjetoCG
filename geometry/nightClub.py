import os
from core.obj_reader2 import load_multimaterial_from_object # Importa a função de carregamento
from extras.movement_rig import MovementRig
from core_ext.mesh import Mesh
from core_ext.texture import Texture
from material.texture import TextureMaterial
from geometry.geometry import Geometry # Necessário para criar as geometrias das partes

# Remove ou comenta a classe NightClubGeometry se não for mais necessária
# class NightClubGeometry(Geometry):
#     def __init__(self, width=2, height=2, depth=1, vertices=[], uv_data=[]):
#         super().__init__()
#         pass

class NightClub:
    def __init__(self, scene, obj_file_path="geometry/nightClub.obj", position=[0, -2.5, 10], scale_factor=3):
        """
        Carrega o modelo 3D do nightclub, configura seus materiais e texturas,
        e o adiciona à cena na posição e escala especificadas.
        """
        print("Initializing NightClub object...")
        self.rig = MovementRig() # Cria o rig principal para o nightclub
        self.scene = scene

        # Verifica se o ficheiro OBJ existe
        if not os.path.exists(obj_file_path):
            #print(f"Error: NightClub OBJ file not found at {os.path.abspath(obj_file_path)}")
            # Não adiciona o rig à cena se o ficheiro não for encontrado
            return # Interrompe a inicialização

        # Adiciona o rig à cena ANTES de carregar as partes
        self.scene.add(self.rig)

        # Chama a função de carregamento multi-material
        nightclub_parts = load_multimaterial_from_object(obj_file_path)

        if not nightclub_parts:
            print(f"Error: Could not load nightclub parts from {obj_file_path}.")
            # Remove o rig da cena se não houver partes
            if self.rig in self.scene.descendant_list:
                self.scene.remove(self.rig)
            return # Interrompe a inicialização
        else:
            #print(f"Loaded {len(nightclub_parts)} parts for the nightclub.")
            parts_loaded_successfully = 0
            for part_data in nightclub_parts:
                try:
                    material_name = part_data.get('material_name', 'Unknown')
                    texture_path = part_data.get('texture_path')
                    geometry_data = part_data.get('geometry_data')

                    if not texture_path or not geometry_data:
                        print(f"  Warning: Skipping part '{material_name}' due to missing texture or geometry data.")
                        continue

                    #print(f"  Processing part with material: {material_name}")

                    # Verificar se o ficheiro de textura existe
                    if not os.path.exists(texture_path):
                        print(f"    Warning: Texture file not found at {os.path.abspath(texture_path)}. Skipping mesh part.")
                        continue # Saltar esta parte se a textura não existe

                    # Criar Geometria para esta parte
                    geometry = Geometry()
                    geometry.add_attribute("vec3", "vertexPosition", geometry_data['vertices'])
                    geometry.add_attribute("vec2", "vertexUV", geometry_data['uvs'])
                    # Vertex count is handled by add_attribute

                    if geometry.vertex_count == 0:
                        print(f"    Warning: Geometry for material '{material_name}' has 0 vertices. Skipping mesh part.")
                        continue

                    # Criar Material e Textura para esta parte
                    #print(f"    Loading texture: {texture_path}")
                    material = TextureMaterial(texture=Texture(file_name=texture_path), property_dict={"doubleSide": True})

                    # Criar Mesh e adicioná-lo ao Rig do nightclub
                    mesh = Mesh(geometry, material)
                    self.rig.add(mesh) # Adiciona a mesh ao rig do nightclub
                    #print(f"    Added mesh part for material {material_name} to rig.")
                    parts_loaded_successfully += 1

                except Exception as e:
                    print(f"  Error processing part for material {part_data.get('material_name', 'Unknown')}: {e}")
                    import traceback
                    traceback.print_exc()

            if parts_loaded_successfully > 0:
                # Configurar a posição/escala do rig completo
                self.rig.set_position(position)
                self.rig.scale(scale_factor)
                print(f"NightClub setup complete. {parts_loaded_successfully} parts added.")
            else:
                print("Nightclub setup failed: No parts were loaded successfully.")
                # Remove o rig da cena se nenhuma parte foi carregada
                if self.rig in self.scene.descendant_list:
                    self.scene.remove(self.rig)

    def get_rig(self):
        """Retorna o rig principal do nightclub para manipulação externa."""
        return self.rig



