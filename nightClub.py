# In NightClub class constructor
# ... existing code ...
self.mesh_list.append(Mesh(
    geometry=geometry,
    material=PhongMaterial(
        num_lights=len(config.SCENE_LIGHTS),  # Changed from fixed number
        texture=texture
    ),
    position=[0, -1.5, 0]
))
# ... existing code ...