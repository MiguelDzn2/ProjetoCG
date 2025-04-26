# Project Dependencies

This document outlines all dependencies required for the Computer Graphics project.

## Core Dependencies

- **NumPy**: Used for numerical operations and array handling
- **Python Standard Libraries**:
  - `math`: Mathematical functions
  - `pathlib`: File path handling
  - `sys`: System-specific parameters and functions
  - `enum`: Enumeration support

## Project-Specific Libraries

The project relies on custom modules organized in several packages:

### Core Package
- `core.base`: Base class for application management
- `core.attribute`: Attribute management
- `core.input`: Input handling
- `core.matrix`: Matrix operations for transformations
- `core.obj_reader2`: OBJ file format parser
- `core.uniform`: Uniform value handling for shaders
- `core.utils`: Utility functions

### Core Extensions
- `core_ext.camera`: Camera functionality
- `core_ext.mesh`: Mesh representation
- `core_ext.renderer`: Rendering pipeline
- `core_ext.scene`: Scene graph management
- `core_ext.texture`: Texture handling
- `core_ext.object3d`: 3D object base class
- `core_ext.group`: Object grouping

### Geometry
- Custom geometry classes for different instruments:
  - `geometry.miguelinstrument`: Miguel's instrument geometry
  - `geometry.zeinstrument`: Ze's instrument geometry
  - `geometry.anainstrument`: Ana's instrument geometry
  - `geometry.brandoninstrument`: Brandon's instrument geometry
- Basic geometric primitives:
  - `geometry.box`, `geometry.cylinder`, `geometry.sphere`, etc.
- `geometry.parametric`: Parametric surface generation

### Material
- `material.surface`: Surface material properties
- `material.texture`: Texture-based materials

### Extras
- `extras.axes`: Axes visualization helper
- `extras.grid`: Grid visualization helper
- `extras.movement_rig`: Movement controls for objects and camera

## External Resources
- OBJ model files (e.g., `geometry/miguelOBJ.obj`)
- Texture images (e.g., `images/miguelJPG.jpg`) 