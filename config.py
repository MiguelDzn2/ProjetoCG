import math

# Ring Configuration
RING_INNER_RADIUS = 0.55
RING_OUTER_RADIUS = 0.65
RING_SCALE = 1.0
RING_POSITION = [1, -0.02, 8]  # [x, z, y]

# Camera Configuration
CAMERA_INITIAL_POSITION = [0, 1.2, 7]  # X, Y, Z
CAMERA_INITIAL_ROTATION = [0, -math.pi/2, 0]  # X, Y, Z rotations in radians
CAMERA_FINAL_POSITION = [-3, 1.2, 12.5]
CAMERA_FINAL_ROTATION = [0, -math.pi/4, 0]
CAMERA_TRANSITION_TIME = 4.0

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
SELECTION_SPACING = 3.0 # Spacing between objects in selection phase

# SSAO Settings
SSAO_KERNEL_SIZE = 64
SSAO_RADIUS = 1.0
SSAO_BIAS = 0.01
SSAO_POWER = 1.0
SSAO_NOISE_TEXTURE_SIZE = 4 # e.g., 4x4 noise texture 