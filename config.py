import math

# Ring Configuration
RING_INNER_RADIUS = 0.55
RING_OUTER_RADIUS = 0.65
RING_SCALE = 1.0
RING_POSITION = [1, -0.02, 8]  # [x, z, y]

# Camera Configuration
CAMERA_INITIAL_POSITION = [0, 1.2, 7]  # X, Y, Z
CAMERA_INITIAL_ROTATION = [0, -90, 0]  # X, Y, Z rotations in degrees
CAMERA_FINAL_POSITION = [-3, 1.2, 12.5]
CAMERA_FINAL_ROTATION = [0, -45, 0]  # X, Y, Z rotations in degrees
CAMERA_TRANSITION_TIME = 4.0

# Camera waypoints configuration - visited after secondary position
# Each waypoint has:
# - time: at which the transition begins (in seconds of music time)
# - position: target XZY coordinates
# - rotation: target XYZ Euler angles (in degrees)
CAMERA_WAYPOINTS = [
    {
        "time": 6.0,
        "position": [0, 1.2, 7],
        "rotation": [0, -90, 0]  # Converted from math.pi/12, -math.pi/2
    },
   {
        "time": 8.0,
        "position": [-3, 1.2, 12.5],
        "rotation": [0, -45, 0]  # Converted from math.pi/12, -math.pi/2
    }, 
    {
        "time": 37.0,
        "position": [-3.8, 4.2, 16.4],
        "rotation": [-42.7, -40, 5.3]  # Converted from math.pi/12, -math.pi/2
    },
    {
        "time": 38.0,
        "position": [0.3, 6.6, 16.5],
        "rotation": [-45, 0, 0]  # Converted from math.pi/12, -math.pi/2
    },
    {
        "time": 39.0,
        "position": [-3.8, 4.2, 16.4],
        "rotation": [-42.7, -40, 5.3]  # Converted from math.pi/12, -math.pi/2
    },
    {
        "time": 40.0,
        "position": [0.3, 6.6, 16.5],
        "rotation": [-45, 0, 0]  # Converted from math.pi/12, -math.pi/2
    },
    {
        "time": 41.0,
        "position": [-3.8, 4.2, 16.4],
        "rotation": [-42.7, -40, 5.3]  # Converted from math.pi/12, -math.pi/2
    },
    {
        "time": 42.0,
        "position": [0.3, 6.6, 16.5],
        "rotation": [-45, 0, 0]  # Converted from math.pi/12, -math.pi/2
    },
    {
        "time": 43.0,
        "position": [0.3, 6.6, 16.5],
        "rotation": [-45, 0, 0]  # Converted from math.pi/12, -math.pi/2
    },
    {
        "time": 44.0,
        "position": [0.3, 6.6, 16.5],
        "rotation": [-45, 0, 0]  # Converted from math.pi/12, -math.pi/2
    }
]

# Movement Configuration
MOVE_AMOUNT_MULTIPLIER = 2
ROTATE_AMOUNT_MULTIPLIER = 1

# Arrow Configuration
ARROW_SPAWN_INTERVAL = 2.0
ARROW_START_POSITION = [-3, 0, 8]  # X, Y, Z
ARROW_UNITS_PER_SECOND = 4.0 # Placeholder value, adjust as needed

# Screen Configuration
SCREEN_SIZE = [1280, 720]

# Selection Phase Configuration
SELECTION_PHASE_OBJECTS_Y = 100  # Y coordinate for all objects in selection phase
SELECTION_PHASE_CAMERA_Y = 105   # Y coordinate for camera in selection phase
SELECTION_PHASE_CAMERA_POSITION = [0.5, SELECTION_PHASE_CAMERA_Y, 15]
SELECTION_PHASE_BACKGROUND_POSITION = [0.5, 105, -11.8] # [x, y, z]
SELECTION_PHASE_BACKGROUND_WIDTH = 55
SELECTION_PHASE_BACKGROUND_HEIGHT = 31
SELECTION_PHASE_BACKGROUND_IMAGE = "images/BGsummer1280x720.png"

# Selection phase positions configuration
SELECTION_FIRST_INSTRUMENT_X = -10  # X position of the first instrument
SELECTION_INSTRUMENT_SPACING = 7   # Spacing between each instrument
SELECTION_PHASE_Z_VALUES = [0, 0, 0, 1.5]  # Z values can still be customized per instrument

# Selection phase positions for each instrument - calculated dynamically
SELECTION_PHASE_POSITIONS = [
    [SELECTION_FIRST_INSTRUMENT_X + (i * SELECTION_INSTRUMENT_SPACING), 
     SELECTION_PHASE_OBJECTS_Y, 
     SELECTION_PHASE_Z_VALUES[i]] for i in range(4)
]

# Spotlight configuration for selection phase
SELECTION_PHASE_SPOTLIGHT_Y_OFFSET = 8
SELECTION_PHASE_SPOTLIGHT_COLORS = [
    [1.0, 1.0, 1.0],  # White for Miguel's spotlight
    [1.0, 1.0, 1.0],  # White for Ze's spotlight
    [1.0, 1.0, 1.0],  # White for Ana's spotlight
    [1.0, 1.0, 1.0]   # White for Brandon's spotlight 
]
SELECTION_PHASE_SPOTLIGHT_BRIGHTNESS_MULTIPLIER = 1.5  # For highlighted object

# Gameplay Phase Configuration
# Position of the selected instrument in gameplay phase based on which instrument is selected
GAMEPLAY_SELECTED_INSTRUMENT_POSITIONS = [
    [0, 0, 0],    # Position for Miguel's instrument when selected [y, Z, X]
    [0, 0.5, 0],  # Position for Ze's instrument when selected [y, Z, X]    
    [0, 0, 0.5],  # Position for Ana's instrument when selected [y, Z, X]
    [0.5, 0, 0]   # Position for Brandon's instrument when selected [y, Z, X]
]

# Default position (kept for backward compatibility)
GAMEPLAY_SELECTED_INSTRUMENT_POSITION = [0, 0, 0]  # Default center position [y, Z, X]

# Positions when each instrument is selected (format: [miguel_pos, ze_pos, ana_pos, brandon_pos])
# Where None is used for the selected instrument (which will be at GAMEPLAY_SELECTED_INSTRUMENT_POSITION)
GAMEPLAY_PHASE_POSITIONS = [
    # Positions when Miguel's instrument (index 0) is selected
    [
        None,                   # No position for Miguel (selected) 
        [10, -0.17, 10.5],      # Position for Ze's instrument [x,z,y]
        [12, -0.60, 7.2],       # Position for Ana's instrument
        [10, -0.5, 4]           # Position for Brandon's instrument
    ],
    # Positions when Ze's instrument (index 1) is selected
    [
        [10, -0.45, 10.5],      # Position for Miguel's instrument
        None,                   # No position for Ze (selected)
        [12, -0.60, 7.2],       # Position for Ana's instrument
        [10, -0.5, 4]           # Position for Brandon's instrument
    ],
    # Positions when Ana's instrument (index 2) is selected
    [
        [10, -0.45, 10.5],      # Position for Miguel's instrument
        [12, 0.2, 7.2],       # Position for Ze's instrument [x,z,y]
        None,                   # No position for Ana (selected)
        [10, -0.5, 4]           # Position for Brandon's instrument
    ],
    # Positions when Brandon's instrument (index 3) is selected
    [
        [10, -0.45, 10.5],      # Position for Miguel's instrument
        [12, 0.2, 7.2],       # Position for Ze's instrument [x,z,y]
        [10, -0.8, 4],          # Position for Ana's instrument
        None                    # No position for Brandon (selected)
    ]
]

# Rotations when each instrument is selected (format: [miguel_rot, ze_rot, ana_rot, brandon_rot])
# Where None is used for the selected instrument (which will have no rotation)
GAMEPLAY_PHASE_ROTATIONS = [
    # Rotations when Miguel's instrument (index 0) is selected
    [
        None,                            # No rotation for Miguel (selected)
        #[math.pi/4, math.pi/6, 0],       # Rotation for Ze's instrument
        [0, 0, 0], # Ze
        [math.pi/10, math.pi/2, 0],      # Rotation for Ana's instrument
        [-math.pi/4, -math.pi/8, -math.pi/4]  # Rotation for Brandon's instrument
    ],
    # Rotations when Ze's instrument (index 1) is selected
    [
        [math.pi/4, math.pi/6, 0],       # Rotation for Miguel's instrument
        None,                            # No rotation for Ze (selected)
        [math.pi/10, math.pi/2, 0],      # Rotation for Ana's instrument
        [-math.pi/4, -math.pi/8, -math.pi/4]  # Rotation for Brandon's instrument
    ],
    # Rotations when Ana's instrument (index 2) is selected
    [
        [math.pi/4, math.pi/6, 0],       # Rotation for Miguel's instrument
        [math.pi/4, math.pi/6, 0],       # Rotation for Ze's instrument
        None,                            # No rotation for Ana (selected)
        [-math.pi/4, -math.pi/8, -math.pi/4]  # Rotation for Brandon's instrument
    ],
    # Rotations when Brandon's instrument (index 3) is selected
    [
        [math.pi/4, math.pi/6, 0],       # Rotation for Miguel's instrument
        [math.pi/4, math.pi/6, 0],       # Rotation for Ze's instrument
        [math.pi/10, math.pi/2, 0],      # Rotation for Ana's instrument
        None                             # No rotation for Brandon (selected)
    ]
]

# Object Model Paths
INSTRUMENT_OBJECT_PATHS = {
    "miguel": "geometry/miguelOBJ.obj",
    "ze": "geometry/zeOBJ.obj",
    "ana": "geometry/anaOBJ.obj",
    "brandon": "geometry/brandonOBJ.obj"
}

# Texture Paths
INSTRUMENT_TEXTURE_PATHS = {
    "miguel": "images/miguelJPG.jpg",
    "ze": "images/zeJPG.jpg",
    "ana": "images/anaPNG.png",
    "brandon": "images/brandonPNG.png"
}

# Instrument Geometry Configuration
INSTRUMENT_GEOMETRIES = {
    "miguel": {
        "width": 1,
        "height": 1,
        "depth": 1
    },
    "ze": {
        "width": 1,
        "height": 1,
        "depth": 1
    },
    "ana": {
        "width": 1,
        "height": 1,
        "depth": 1
    },
    "brandon": {
        "width": 2,
        "height": 2,
        "depth": 1
    }
}

# Material Properties
INSTRUMENT_MATERIAL_PROPERTIES = {
    "baseColor": [1.0, 1.0, 1.0],
    "specularStrength": 3.0,
    "shininess": 80
}

# Initial Instrument Positions in Gameplay Phase
INSTRUMENT_INITIAL_POSITIONS = {
    "miguel": [-3, 0, 0],
    "ze": [-1, 0, 0],
    "ana": [1, 0, 0],
    "brandon": [3, 0, 0]
}

# NightClub Configuration
NIGHTCLUB_OBJECT_PATH = "geometry/nightClub.obj"
NIGHTCLUB_POSITION = [0, -2.5, 10]
NIGHTCLUB_SCALE_FACTOR = 3

# Music and Keyframe Paths for Instruments
INSTRUMENT_MUSIC_PATHS = {
    "miguel": "music/fitnessgram.mp3",
    "ze": "music/track2.mp3",
    "ana": "music/track3.mp3",
    "brandon": "music/track4.mp3"
}

INSTRUMENT_KEYFRAME_PATHS = {
    "miguel": "keyframes/keyframes_1.json",
    "ze": "keyframes/keyframes_2.json",
    "ana": "keyframes/keyframes_3.json",
    "brandon": "keyframes/keyframes_4.json"
}

# Selection Phase Music
SELECTION_MUSIC_PATH = "music/selection.mp3" 