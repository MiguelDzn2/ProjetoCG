# ProjetoCG - 3D Rhythm Instrument Game

A sophisticated 3D rhythm game built in Python using OpenGL, featuring custom instrument models, dynamic lighting with visual cone effects, and a comprehensive modular architecture. This project showcases advanced computer graphics techniques including scene graphs, custom shaders, and multi-phase game state management.

## 🎮 Game Overview

This rhythm game features three distinct phases where players can select from four unique 3D instruments (Miguel's, Ze's, Ana's, and Brandon's) and play along to synchronized music tracks with spawning arrows and visual feedback.

### Game Phases

1. **Selection Phase**: Choose from four custom 3D instrument models displayed in a lineup with colored spotlights
2. **Gameplay Phase**: Control your selected instrument while arrows spawn synchronized to music, aiming for a target ring
3. **End Screen Phase**: View final scores with options to replay or return to selection

## 🏗️ Architecture & Features

### Advanced Graphics Features
- **Custom 3D Models**: Each team member has a unique instrument model with dedicated textures
- **Dynamic Lighting System**: 
  - Ambient, directional, point, and spotlight implementations
  - Visual cone rendering for spotlights with transparency gradients
  - Color-synchronized spotlight cones during selection
- **Scene Graph Management**: Hierarchical object organization with transformation inheritance
- **Custom Shaders**: Specialized vertex and fragment shaders for cone visualization
- **Texture System**: Dynamic text rendering and image-based textures

### Modular Game Architecture
- **PhaseManager**: Handles game state transitions and scene configuration
- **AnimationManager**: Manages object rotations, jumps, and smooth animations
- **MusicSystem**: Synchronizes music playback with keyframe-based arrow spawning
- **UIManager**: Displays scores, streaks, collision feedback, and phase-specific UI
- **ArrowManager**: Handles arrow lifecycle, movement, and collision detection
- **InstrumentLoader**: Manages 3D model loading and material setup

### Technical Highlights
- **Frame-rate Independent Movement**: All animations scaled by delta_time
- **Additive Blending**: Transparent cone visualizations with proper depth handling
- **Camera Animation System**: Smooth waypoint-based camera movements
- **OBJ Model Loading**: Custom parser for 3D model files with texture support
- **Movement Rig System**: Unified control system for camera and object manipulation

## 📁 Project Structure

```
ProjetoCG/
├── core/                  # Core framework (Application, Matrix operations, OBJ parser)
├── core_ext/              # Extended functionality (Camera, Renderer, Scene, Mesh, Texture)
├── geometry/              # 3D models and geometric primitives
│   ├── *instrument.py     # Custom instrument models for each team member
│   ├── arrow.py           # Arrow geometry for gameplay
│   ├── ring.py            # Target ring geometry
│   ├── cone.py            # Cone geometry with transparency gradient
│   ├── nightClub.py       # Nightclub scene elements
│   └── *.obj              # 3D model files
├── material/              # Material definitions and texture handling
├── light/                 # Advanced lighting system
│   ├── ambient.py         # Ambient lighting
│   ├── directional.py     # Directional lighting
│   ├── spotlight.py       # Spotlight with visual cone implementation
│   └── point.py           # Point lighting
├── modules/               # Game logic modules
│   ├── animation.py       # Animation management
│   ├── instrument_loader.py # Model loading and setup
│   ├── music_system.py    # Music and keyframe processing
│   ├── phase_manager.py   # Game phase management
│   └── ui_manager.py      # UI and score management
├── extras/                # Utility components
│   ├── movement_rig.py    # Camera and object control system
│   ├── text_texture.py    # Dynamic text rendering
│   ├── axes.py            # Debug visualization helpers
│   └── grid.py            # Grid visualization
├── images/                # Texture assets and visual resources
├── music/                 # Music tracks for each instrument
├── keyframes/             # JSON files defining arrow spawn timing
├── config.py              # Centralized game configuration
├── game.py                # Main game class and logic integration
├── arrow_manager.py       # Arrow spawning and management
├── main.py                # Application entry point
└── requirements.txt       # Python dependencies
```

## 🎯 Controls

### Selection Phase
- **←/→ Arrow Keys**: Navigate between instruments
- **Enter**: Confirm selection and start gameplay

### Gameplay Phase
- **Camera**: Automatic cinematic movement (manual control in debug mode)
- **Instrument Control**:
  - **Q/W/E/R**: Rotate instrument along different axes
  - **T/Y**: Jump left/right
  - **Arrow Keys**: Interact with arrows during collisions

### End Screen Phase
- **R**: Restart current level
- **C**: Return to selection phase

### Debug Mode Controls
- **WASD**: Move camera forward/left/backward/right
- **Q/E**: Move camera up/down
- **Arrow Keys**: Rotate camera
- **I/J/K/L**: Fine rotation adjustments

## 🚀 Installation & Setup

### Prerequisites
- Python 3.11 or higher
- OpenGL support
- Audio support for music playback

### Option 1: Using Poetry (Recommended)
```bash
# Clone the repository
git clone <repository-url>
cd ProjetoCG

# Install dependencies using Poetry
poetry install

# Run the application
poetry run python main.py

# Run in debug mode for manual camera control
poetry run python main.py --debug
```

### Option 2: Using pip
```bash
# Clone the repository
git clone <repository-url>
cd ProjetoCG

# Create virtual environment (recommended)
python -m venv venv
# Windows:
.\venv\Scripts\activate
# macOS/Linux:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Run the application
python main.py

# Run in debug mode
python main.py --debug
```

## 📦 Dependencies

- **PyOpenGL** (3.1.9): OpenGL bindings for Python
- **PyOpenGL-accelerate** (3.1.9): Acceleration support for PyOpenGL
- **numpy** (2.2.3): Numerical computing and matrix operations
- **pygame** (2.6.1): Audio playback and system integration

## 🎵 Customization Guide

### Adding Your Own Instrument
1. **3D Model**: Add your `.obj` model file to `/geometry/`
2. **Texture**: Add texture images to `/images/`
3. **Music**: Place your music file in `/music/`
4. **Keyframes**: Create a JSON file in `/keyframes/` defining arrow spawn timing
5. **Camera Path**: Define waypoints in `config.py` for cinematic camera movement
6. **Configuration**: Update paths in `config.py`

### Keyframe Format Example
```json
[
    {
        "time": 2.5,
        "arrow_type": "up"
    },
    {
        "time": 4.0,
        "arrow_type": "left"
    }
]
```

### Camera Waypoint Example
```python
"your_instrument": [
    {
        "time": 0.0,
        "position": [-6.3, 5.9, 20],
        "rotation": [-28.9, -29, 0]
    },
    {
        "time": 10.0,
        "position": [0, 1.2, 7],
        "rotation": [0, -90, 0]
    }
]
```

## 🛠️ Development Features

### Coding Standards
- PEP 8 compliance with 4-space indentation
- Comprehensive docstrings for all classes and functions
- Type hinting for function parameters and return values
- Modular architecture with single responsibility principle
- Frame-rate independent animations

### Advanced Graphics Implementation
- **Shader Programs**: Custom GLSL shaders for cone visualization
- **Blending Modes**: Additive blending for transparent effects
- **Transformation Hierarchy**: Scene graph with proper matrix inheritance
- **Material System**: Unified material handling with uniform management
- **Texture Mapping**: Both static images and dynamic text rendering

### Performance Optimizations
- Efficient scene graph traversal
- Proper resource cleanup and management
- Optimized rendering pipeline with depth testing
- Frame-rate independent movement calculations

## 📚 Additional Documentation

The project includes comprehensive documentation:
- `USAGE_COLLEAGUES.md`: Detailed tutorial for team members
- `arrow_implementation.md`: Arrow system documentation
- `phase_explanation.md`: Game phase system details
- `uniform_explanation.md`: Shader uniform system
- `analysis.md`: Project analysis and architecture

## 🤝 Team Members

- **Miguel**: Guitar instrument model and texture implementation
- **Ze**: Drum instrument model and music integration
- **Ana**: Keyboard instrument model and UI design
- **Brandon**: Bass instrument model and lighting system

## 🎓 Educational Value

This project demonstrates advanced computer graphics concepts:
- 3D transformations and matrix mathematics
- Shader programming with GLSL
- Scene graph architecture
- Lighting models and visual effects
- Real-time rendering techniques
- Game state management
- Audio-visual synchronization
- Modular software architecture

## 🐛 Troubleshooting

### Common Issues
1. **Audio not playing**: Ensure pygame is properly installed and audio drivers are working
2. **Graphics performance**: Update graphics drivers and ensure OpenGL support
3. **Model loading errors**: Verify OBJ file format and texture file paths
4. **Module import errors**: Ensure all dependencies are installed and Python path is correct

### Debug Mode
Run with `--debug` flag to enable:
- Manual camera control
- Performance metrics display
- Enhanced error reporting
- Position/rotation display

## 📄 License

This project is developed as part of a Computer Graphics course assignment. 