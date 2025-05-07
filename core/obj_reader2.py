from typing import List, Tuple
import os # Adicionado para as novas funções

# Note: my_obj_reader2 is a simplified OBJ loader.
# It is primarily used for basic examples or testing and does not support materials or normals fully.
# For comprehensive OBJ loading with material and normal support, 
# prefer load_multimaterial_from_object found in this same file, which is used by the main project.
def my_obj_reader2(filename: str) -> Tuple[List, List]:
    """
    Get the vertices and texture coordinates from the file. (Simplified/Legacy Loader)
    """
    position_list = list()
    texture_list = list()
    vertices = list()
    tex_coords = list()

    with open(filename, 'r') as in_file:
        for line in in_file:
            if line.startswith('v '):
                point = [float(value) for value in line.strip().split()[1:]]
                vertices.append(point)
            elif line.startswith('vt '):
                tex = [float(value) for value in line.strip().split()[1:]]
                tex_coords.append(tex)
            elif line.startswith('f '):
                for elem in line.strip().split()[1:]:
                    indices = elem.split('/')
                    vertex_idx = int(indices[0]) - 1
                    position_list.append(vertices[vertex_idx])

                    if len(indices) > 1 and indices[1]:
                        tex_idx = int(indices[1]) - 1
                        texture_list.append(tex_coords[tex_idx])

    print(len(position_list))
    print(len(texture_list))
    return position_list, texture_list

def parse_mtl(mtl_filepath):
    """Analisa um ficheiro MTL e retorna um dicionário de materiais e suas texturas."""
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
                         # Se não encontrado, tenta assumir que é relativo a uma pasta padrão (ex: 'images/club')
                         # Pega apenas o nome do ficheiro
                         texture_filename = os.path.basename(texture_path_relative)
                         # Tenta encontrar na pasta 'images/club' relativa ao diretório de execução
                         potential_path_alt = os.path.join("images", "club", texture_filename)
                         if os.path.exists(potential_path_alt):
                              materials[current_material]['texture'] = potential_path_alt
                         else:
                              # Tenta encontrar na pasta do próprio ficheiro MTL (caso 'images/club' não exista lá)
                              potential_path_alt_2 = os.path.join(mtl_dir, texture_filename)
                              if os.path.exists(potential_path_alt_2):
                                   materials[current_material]['texture'] = potential_path_alt_2
                              else:
                                   # Se ainda não encontrado, guarda o caminho relativo original
                                   print(f"Warning: Texture '{texture_path_relative}' for material '{current_material}' not found directly. Using relative path: {texture_path_relative}")
                                   materials[current_material]['texture'] = texture_path_relative # Ou um caminho padrão?

    except FileNotFoundError:
        print(f"Warning: MTL file not found at {mtl_filepath}")
    except Exception as e:
        print(f"Error parsing MTL file {mtl_filepath}: {e}")
    return materials

def load_multimaterial_from_object(obj_filepath): # <--- NOME ALTERADO AQUI
    """Carrega um ficheiro OBJ com múltiplos materiais, retornando partes separadas."""
    vertices = []
    uvs = []
    normals = []

    material_groups = {}
    current_material = "default_material"
    material_groups[current_material] = {'faces': []}
    mtl_filename = None
    obj_dir = os.path.dirname(obj_filepath)

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
        material_textures = parse_mtl(mtl_filename) # Chama a função parse_mtl definida acima
        print(f"Parsed materials from MTL: {list(material_textures.keys())}") # Log mais conciso


    # Processar os grupos para criar dados de geometria "desenrolados" por material
    output_parts = []
    print("Processing material groups...")
    for material_name, group_data in material_groups.items():
        part_vertices = []
        part_uvs = []
        part_normals = [] # Se precisares de normais por vértice

        if not group_data['faces']:
             # print(f"  Skipping material '{material_name}': No faces assigned.") # Log opcional
             continue

        # print(f"  Processing material: {material_name} ({len(group_data['faces'])} triangles)") # Log opcional
        for face in group_data['faces']: # Cada 'face' aqui já é um triângulo
            for v_idx, uv_idx, n_idx in face:
                # Adiciona dados do vértice
                if 0 <= v_idx < len(vertices):
                     part_vertices.extend(vertices[v_idx])
                else:
                     print(f"Warning: Vertex index {v_idx+1} out of bounds for material {material_name}. Using [0,0,0].")
                     part_vertices.extend([0.0, 0.0, 0.0])

                # Adiciona dados de UV (se existirem)
                if 0 <= uv_idx < len(uvs):
                     part_uvs.extend(uvs[uv_idx])
                else:
                     # print(f"Warning: UV index {uv_idx+1} missing or out of bounds for vertex {v_idx+1} in material {material_name}. Using [0,0].") # Log muito verboso
                     part_uvs.extend([0.0, 0.0]) # UV por defeito

                # Adiciona dados normais (se existirem e precisares)
                if 0 <= n_idx < len(normals):
                    part_normals.extend(normals[n_idx])
                else:
                    # If normals are expected, provide a default or raise an error.
                    # For lighting, valid normals are crucial. A default like [0,0,0] is problematic.
                    # It might be better to ensure OBJs have normals or skip lighting if not.
                    # For now, let's add a default normal if missing, but log a warning.
                    # print(f"Warning: Normal index {n_idx+1} missing or out of bounds for vertex {v_idx+1} in material {material_name}. Using [0,1,0].") # Example default
                    part_normals.extend([0.0, 1.0, 0.0]) # Default normal (e.g., pointing up)

        texture_file = material_textures.get(material_name, {}).get('texture')
        if not texture_file:
             print(f"  Warning: No texture found in MTL for material '{material_name}'. This part might be untextured or use a default.")
             # Poderias atribuir uma textura padrão aqui se quisesses
             # texture_file = "images/default_white.png" # Exemplo

        # Só adiciona a parte se tiver vértices E uma textura associada (ou se permitires partes sem textura)
        if part_vertices and texture_file:
             # print(f"  Prepared part for material '{material_name}' with {len(part_vertices)//3} vertices and texture '{texture_file}'") # Log opcional
             output_parts.append({
                 'material_name': material_name,
                 'geometry_data': {
                      # Assegura que são listas planas de floats
                      'vertices': [float(v) for v in part_vertices],
                      'uvs': [float(uv) for uv in part_uvs],
                      'normals': [float(n) for n in part_normals]
                 },
                 'texture_path': texture_file
             })
        elif part_vertices: # If there are vertices but no texture file from MTL
             print(f"  Prepared part for material '{material_name}' with {len(part_vertices)//3} vertices but NO TEXTURE assigned in MTL. Adding with texture_path=None.")
             output_parts.append({
                 'material_name': material_name,
                 'geometry_data': {
                      'vertices': [float(v) for v in part_vertices],
                      'uvs': [float(uv) for uv in part_uvs],
                      'normals': [float(n) for n in part_normals]
                 },
                 'texture_path': None # Add part with texture_path as None
             })
             # Decide se queres adicionar partes sem textura (talvez com um material de cor?)
             # Por agora, vamos ignorá-las se não tiverem textura definida no MTL.
             # pass # Old behavior


    print(f"Finished processing OBJ. Generated {len(output_parts)} textured parts.")
    return output_parts


if __name__ == '__main__':
    f_in = input("File? ")
    # positions, textures = my_obj_reader(f_in) # Original function name might be my_obj_reader2
    # For testing load_multimaterial_from_object:
    parts = load_multimaterial_from_object(f_in)
    if parts:
        for i, part in enumerate(parts):
            print(f"Part {i} (Material: {part['material_name']}):")
            print(f"  Vertices: {len(part['geometry_data']['vertices']) // 3}")
            print(f"  UVs: {len(part['geometry_data']['uvs']) // 2}")
            # print(f"  Normals: {len(part['geometry_data']['normals']) // 3}") # When normals are added
            print(f"  Texture: {part['texture_path']}")
    # print("Vertex positions:", positions)
    # print("Texture coordinates:", textures)
    # Nota: O código original aqui chamava my_obj_reader, talvez precise de ajuste
    # se quiseres testar as novas funções diretamente.
    pass # Mantém como estava ou ajusta para testar as novas funções