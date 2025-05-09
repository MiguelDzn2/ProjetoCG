"""
Instrument loader module for handling the loading and setup of instrument models.
"""

from core_ext.mesh import Mesh
from extras.movement_rig import MovementRig
from core_ext.texture import Texture
from material.phong import PhongMaterial
from core.obj_reader2 import load_multimaterial_from_object
import config

class InstrumentLoader:
    """
    Manages the loading and setup of instrument models in the game.
    """
    
    def __init__(self, scene):
        """
        Initialize the InstrumentLoader.
        
        Parameters:
            scene: The scene to add instruments to
        """
        self.scene = scene
        self.object_rigs = []
        self.object_meshes = []
        
    def load_instruments(self, debug_mode=False):
        """
        Load all instrument models and add them to the scene.
        
        Returns:
            A tuple of (object_rigs, object_meshes)
        """
        # Load textures for each instrument
        miguel_texture = Texture(file_name=config.INSTRUMENT_TEXTURE_PATHS["miguel"])
        ze_texture = Texture(file_name=config.INSTRUMENT_TEXTURE_PATHS["ze"])
        ana_texture = Texture(file_name=config.INSTRUMENT_TEXTURE_PATHS["ana"])
        brandon_texture = Texture(file_name=config.INSTRUMENT_TEXTURE_PATHS["brandon"])

        # Define common Phong material properties from config
        phong_properties = config.INSTRUMENT_MATERIAL_PROPERTIES
        
        # Number of light sources: 1 Ambient + 1 Directional + 4 SpotLights = 7
        num_light_sources = 7

        # Create Phong materials for each instrument
        miguel_material = PhongMaterial(texture=miguel_texture, number_of_light_sources=num_light_sources, property_dict=phong_properties)
        ze_material = PhongMaterial(texture=ze_texture, number_of_light_sources=num_light_sources, property_dict=phong_properties)
        ana_material = PhongMaterial(texture=ana_texture, number_of_light_sources=num_light_sources, property_dict=phong_properties)
        brandon_material = PhongMaterial(texture=brandon_texture, number_of_light_sources=num_light_sources, property_dict=phong_properties)
        
        # Import necessary geometry classes at function level to avoid circular imports
        from geometry.miguelinstrument import MiguelGeometry
        from geometry.zeinstrument import ZeGeometry
        from geometry.anainstrument import AnaGeometry
        from geometry.brandoninstrument import BrandonGeometry

        # Configurations for loading instrument models from config
        instrument_configs = [
            {
                "name": "miguel", 
                "obj_path": config.INSTRUMENT_OBJECT_PATHS["miguel"], 
                "geom_class": MiguelGeometry, 
                "material": miguel_material, 
                "pos": config.INSTRUMENT_INITIAL_POSITIONS["miguel"], 
                "geom_args": (
                    config.INSTRUMENT_GEOMETRIES["miguel"]["width"],
                    config.INSTRUMENT_GEOMETRIES["miguel"]["height"],
                    config.INSTRUMENT_GEOMETRIES["miguel"]["depth"]
                )
            },
            {
                "name": "ze", 
                "obj_path": config.INSTRUMENT_OBJECT_PATHS["ze"], 
                "geom_class": ZeGeometry, 
                "material": ze_material, 
                "pos": config.INSTRUMENT_INITIAL_POSITIONS["ze"], 
                "geom_args": (
                    config.INSTRUMENT_GEOMETRIES["ze"]["width"],
                    config.INSTRUMENT_GEOMETRIES["ze"]["height"],
                    config.INSTRUMENT_GEOMETRIES["ze"]["depth"]
                )
            },
            {
                "name": "ana", 
                "obj_path": config.INSTRUMENT_OBJECT_PATHS["ana"], 
                "geom_class": AnaGeometry, 
                "material": ana_material, 
                "pos": config.INSTRUMENT_INITIAL_POSITIONS["ana"], 
                "geom_args": (
                    config.INSTRUMENT_GEOMETRIES["ana"]["width"],
                    config.INSTRUMENT_GEOMETRIES["ana"]["height"],
                    config.INSTRUMENT_GEOMETRIES["ana"]["depth"]
                )
            },
            {
                "name": "brandon", 
                "obj_path": config.INSTRUMENT_OBJECT_PATHS["brandon"], 
                "geom_class": BrandonGeometry, 
                "material": brandon_material, 
                "pos": config.INSTRUMENT_INITIAL_POSITIONS["brandon"], 
                "geom_args": (
                    config.INSTRUMENT_GEOMETRIES["brandon"]["width"],
                    config.INSTRUMENT_GEOMETRIES["brandon"]["height"],
                    config.INSTRUMENT_GEOMETRIES["brandon"]["depth"]
                )
            },
        ]

        # Load instrument models
        for config_item in instrument_configs:
            rig = self._load_instrument_model(
                name=config_item["name"],
                obj_path=config_item["obj_path"],
                geometry_class=config_item["geom_class"],
                material_instance=config_item["material"],
                initial_pos=config_item["pos"],
                geom_constructor_args=config_item["geom_args"]
            )
            if rig:
                self.object_rigs.append(rig)
        
        return self.object_rigs, self.object_meshes

    def _load_instrument_model(self, name, obj_path, geometry_class, material_instance, initial_pos, geom_constructor_args):
        """
        Loads an instrument model from an OBJ file, creates its geometry and mesh,
        and sets up its movement rig.
        
        Parameters:
            name: Name of the instrument
            obj_path: Path to the OBJ file
            geometry_class: Class to use for geometry creation
            material_instance: Material to apply to the mesh
            initial_pos: Initial position [x, y, z]
            geom_constructor_args: Arguments for geometry constructor (width, height, depth)
            
        Returns:
            The created MovementRig instance, or None on failure.
        """
        print(f"Loading {name}'s object from {obj_path}...")
        parts = load_multimaterial_from_object(obj_path)

        if not parts:
            print(f"Error: Could not load {name}'s instrument from {obj_path}.")
            return None

        all_positions = []
        all_uvs = []
        all_normals = []

        for part_data in parts:
            geom_data = part_data['geometry_data']
            all_positions.extend(geom_data['vertices'])
            all_uvs.extend(geom_data['uvs'])
            all_normals.extend(geom_data['normals'])
        
        try:
            width, height, depth = geom_constructor_args
            geometry_instance = geometry_class(
                width, height, depth, 
                positions=all_positions, 
                uvs=all_uvs, 
                vertex_normals=all_normals
            )
        except Exception as e:
            print(f"Error instantiating geometry for {name}: {e}")
            return None

        mesh_instance = Mesh(geometry_instance, material_instance)
        self.object_meshes.append(mesh_instance)

        object_rig_instance = MovementRig()
        object_rig_instance.add(mesh_instance)
        object_rig_instance.set_position(initial_pos)
        self.scene.add(object_rig_instance)
        
        print(f"Successfully loaded and set up {name}'s instrument.")
        return object_rig_instance 