from geometry.geometry import Geometry
import numpy as np
import os 

class NightClubGeometry(Geometry):
    def __init__(self, width=2, height=2, depth=1, vertices=[], uv_data=[]):
        super().__init__()
        # Esta inicialização pode não ser mais relevante se usares Geometry() diretamente
        # position_data = vertices
        # self.add_attribute("vec3", "vertexPosition", position_data)
        # self.add_attribute("vec2", "vertexUV", uv_data)
        # self.count_vertices()
        pass # Deixa vazio ou remove se não for usado


def parse_mtl(mtl_filepath):
    materials = {}
    current_material = None
    mtl_dir = os.path.dirname(mtl_filepath) # Diretório do arquivo MTL

    try:
        with open(mtl_filepath, 'r') as f:
            for line in f:
                parts = line.strip().split()
                if not parts:
                    continue
                if parts[0] == 'newmtl':
                    current_material = parts[1]
                    materials[current_material] = {}
                elif current_material and parts[0] == 'map_Kd':
                    # Constrói o caminho completo para a textura
                    texture_path_relative = " ".join(parts[1:]) # Pode conter espaços
                    # Remove barras invertidas e usa barras normais
                    texture_path_relative = texture_path_relative.replace("\\", "/")
                    # Tenta construir um caminho absoluto ou relativo ao projeto
                    # Primeiro, verifica se o caminho no MTL já é relativo ao diretório do MTL
                    potential_path = os.path.join(mtl_dir, texture_path_relative)
                    if os.path.exists(potential_path):
                         materials[current_material]['texture'] = potential_path
                    else:
                         # Se não encontrado, tenta assumir que é relativo à pasta 'images/club'
                         # Pega apenas o nome do ficheiro
                         texture_filename = os.path.basename(texture_path_relative)
                         potential_path_alt = os.path.join("images", "club", texture_filename)
                         # Verifica se este caminho alternativo existe
                         if os.path.exists(potential_path_alt):
                              materials[current_material]['texture'] = potential_path_alt
                         else:
                              # Se ainda não encontrado, guarda o caminho relativo original
                              # e espera que o projeto.py o encontre
                              print(f"Warning: Texture '{texture_path_relative}' for material '{current_material}' not found directly. Using relative path.")
                              materials[current_material]['texture'] = texture_path_relative # Ou um caminho padrão?

    except FileNotFoundError:
        print(f"Warning: MTL file not found at {mtl_filepath}")
    except Exception as e:
        print(f"Error parsing MTL file {mtl_filepath}: {e}")
    return materials

def load_nightclub_multimaterial(obj_filepath):
    vertices = []
    uvs = []
    normals = [] # Lendo normais, embora não usadas diretamente na geometria final aqui

    material_groups = {} # {material_name: {'faces': []}} <- Armazena apenas índices das faces
    current_material = "default_material" # Material padrão inicial
    material_groups[current_material] = {'faces': []}
    mtl_filename = None
    obj_dir = os.path.dirname(obj_filepath) # Diretório do arquivo OBJ

    print(f"Loading OBJ file: {obj_filepath}")
    try:
        with open(obj_filepath, 'r') as f:
            for line in f:
                parts = line.strip().split()
                if not parts:
                    continue
                elif parts[0] == 'mtllib':
                    # Constrói o caminho completo para o MTL
                    mtl_rel_path = " ".join(parts[1:])
                    mtl_filename = os.path.abspath(os.path.join(obj_dir, mtl_rel_path))
                    print(f"Found MTL reference: {mtl_rel_path} -> Resolved to: {mtl_filename}")
                elif parts[0] == 'v':
                    vertices.append(list(map(float, parts[1:4])))
                elif parts[0] == 'vt':
                    uvs.append(list(map(float, parts[1:3])))
                elif parts[0] == 'vn':
                    normals.append(list(map(float, parts[1:4])))
                elif parts[0] == 'usemtl':
                    current_material = parts[1]
                    if current_material not in material_groups:
                        material_groups[current_material] = {'faces': []}
                    # print(f"Switching to material: {current_material}") # Log opcional
                elif parts[0] == 'f':
                    if current_material is None: # Segurança, embora tenhamos um padrão
                         print("Warning: Face defined before 'usemtl'. Assigning to default.")
                         current_material = "default_material"
                         if current_material not in material_groups:
                              material_groups[current_material] = {'faces': []}

                    # Processa a face (v/vt/vn or v//vn or v/vt)
                    face_vertex_data = [] # Armazena tuplas (v_idx, uv_idx, n_idx) para esta face
                    for part in parts[1:]:
                        indices = part.split('/')
                        v_idx = int(indices[0]) - 1 if indices[0] else -1
                        uv_idx = int(indices[1]) - 1 if len(indices) > 1 and indices[1] else -1
                        n_idx = int(indices[2]) - 1 if len(indices) > 2 and indices[2] else -1
                        face_vertex_data.append((v_idx, uv_idx, n_idx))

                    # Triangula faces com mais de 3 vértices (se necessário)
                    if len(face_vertex_data) == 3:
                         material_groups[current_material]['faces'].append(face_vertex_data)
                    elif len(face_vertex_data) == 4:
                         # Triangulação simples (assume convexo): 0,1,2 e 0,2,3
                         material_groups[current_material]['faces'].append([face_vertex_data[0], face_vertex_data[1], face_vertex_data[2]])
                         material_groups[current_material]['faces'].append([face_vertex_data[0], face_vertex_data[2], face_vertex_data[3]])
                    else:
                         # Ignora ou tenta triangulação mais complexa para polígonos maiores
                         print(f"Warning: Skipping face with {len(face_vertex_data)} vertices (only 3 or 4 supported).")


    except FileNotFoundError:
         print(f"Error: OBJ file not found at {obj_filepath}")
         return []
    except Exception as e:
         print(f"Error reading OBJ file {obj_filepath}: {e}")
         return []


    if not mtl_filename or not os.path.exists(mtl_filename):
        print(f"Warning: MTL file '{mtl_filename}' not found or not specified. Object might render without textures.")
        material_textures = {} # Sem texturas
    else:
        # Parsear o arquivo MTL
        print(f"Parsing MTL file: {mtl_filename}")
        material_textures = parse_mtl(mtl_filename)
        print(f"Parsed materials from MTL: {material_textures}")


    # Processar os grupos para criar dados de geometria "desenrolados" por material
    output_parts = []
    print("Processing material groups...")
    for material_name, group_data in material_groups.items():
        part_vertices = []
        part_uvs = []
        # part_normals = [] # Se precisares de normais por vértice

        if not group_data['faces']:
             print(f"  Skipping material '{material_name}': No faces assigned.")
             continue

        print(f"  Processing material: {material_name} ({len(group_data['faces'])} triangles)")
        for face in group_data['faces']: # Cada 'face' aqui já é um triângulo
            for v_idx, uv_idx, n_idx in face:
                # Adiciona dados do vértice
                if v_idx < len(vertices):
                     part_vertices.extend(vertices[v_idx])
                else:
                     print(f"Warning: Vertex index {v_idx+1} out of bounds for material {material_name}. Using [0,0,0].")
                     part_vertices.extend([0.0, 0.0, 0.0])

                # Adiciona dados de UV (se existirem)
                if uv_idx != -1 and uv_idx < len(uvs):
                     part_uvs.extend(uvs[uv_idx])
                else:
                     # print(f"Warning: UV index {uv_idx+1} missing or out of bounds for vertex {v_idx+1} in material {material_name}. Using [0,0].") # Log muito verboso
                     part_uvs.extend([0.0, 0.0]) # UV por defeito

                # Adiciona dados normais (se existirem e precisares)
                # if n_idx != -1 and n_idx < len(normals):
                #     part_normals.extend(normals[n_idx])
                # else:
                #     part_normals.extend([0.0, 0.0, 0.0]) # Normal por defeito

        texture_file = material_textures.get(material_name, {}).get('texture')
        if not texture_file:
             print(f"  Warning: No texture found in MTL for material '{material_name}'. This part might be untextured or use a default.")
             # Poderias atribuir uma textura padrão aqui se quisesses
             # texture_file = "images/default_white.png" # Exemplo

        # Só adiciona a parte se tiver vértices E uma textura associada (ou se permitires partes sem textura)
        if part_vertices and texture_file:
             print(f"  Prepared part for material '{material_name}' with {len(part_vertices)//3} vertices and texture '{texture_file}'")
             output_parts.append({
                 'material_name': material_name,
                 'geometry_data': {
                      # Assegura que são listas planas de floats
                      'vertices': [float(v) for v in part_vertices],
                      'uvs': [float(uv) for uv in part_uvs]
                 },
                 'texture_path': texture_file
             })
        elif part_vertices:
             print(f"  Prepared part for material '{material_name}' with {len(part_vertices)//3} vertices but NO TEXTURE assigned in MTL.")
             # Decide se queres adicionar partes sem textura (talvez com um material de cor?)
             # Por agora, vamos ignorá-las se não tiverem textura definida no MTL.
             pass


    print(f"Finished processing. Generated {len(output_parts)} textured parts.")
    return output_parts
