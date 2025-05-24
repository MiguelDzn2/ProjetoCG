# Implementation Tutorial for Team Members

This tutorial explains how you can implement your part of the **Rhythm Instrument Game** project. Follow these steps to add your music, keyframes, and configure camera waypoints for your instrument.

## Overview

The project is a 3D rhythm game where each team member has their own instrument with:
- A custom 3D model (guitar, drums, etc.)
- A music track that plays during gameplay  
- A keyframe file that defines when arrows should spawn
- Camera waypoints that create cinematic camera movements during your song

## Project Structure

```
ProjetoCG/
├── music/                 # 🎵 Place your music files here
├── keyframes/             # 📋 Place your keyframe files here  
├── config.py              # ⚙️ Configure your music and keyframe selection here
├── geometry/              # 3D models (already implemented)
├── images/                # Textures (already implemented)
└── ...
```

## Step 1: Adding Your Music File

### 📁 **Folder Location**: `/music/`

1. **Place your music file** in the `music/` directory
   - Supported formats: `.mp3` (recommended)
   - Example: `music/your_song.mp3`

2. **File naming**: Use descriptive names without spaces
   - ✅ Good: `john_guitar_solo.mp3`, `sara_drum_beat.mp3`
   - ❌ Avoid: `my song (final version).mp3`

### ⚙️ **Configuration in config.py**

Open `config.py` and find the `INSTRUMENT_MUSIC_PATHS` section (around line 306):

```python
# Music and Keyframe Paths for Instruments
INSTRUMENT_MUSIC_PATHS = {
    "miguel": "music/Mike_Oldfield__Tubular_bells.mp3",
    "ze": "music/fitnessgram.mp3",        # 👈 Replace this line
    "ana": "music/fitnessgram.mp3",       # 👈 Replace this line  
    "brandon": "music/fitnessgram.mp3"    # 👈 Replace this line
}
```

**Replace the placeholder path** with your music file:
```python
"your_name": "music/your_song.mp3",
```

## Step 2: Creating Your Keyframe File

### 📁 **Folder Location**: `/keyframes/`

1. **Create a new JSON file** in the `keyframes/` directory
   - Example: `keyframes/your_name_keyframes.json`

2. **Keyframe file format**:
```json
[
    {
        "time": 2.5,
        "arrow_type": "up"
    },
    {
        "time": 4.0,
        "arrow_type": "left"
    },
    {
        "time": 5.5,
        "arrow_type": "down"
    }
]
```

**Keyframe Properties:**
- `"time"`: When the arrow should reach the target ring (in seconds from song start)
- `"arrow_type"`: Direction of the arrow
  - Valid values: `"up"`, `"down"`, `"left"`, `"right"`

**Tips for creating keyframes:**
- Listen to your song and note the beats where you want arrows to appear
- Start with fewer arrows and add more as you test
- Arrows spawn automatically before the target time to account for travel time

### ⚙️ **Configuration in config.py**

Find the `INSTRUMENT_KEYFRAME_PATHS` section (around line 313):

```python
INSTRUMENT_KEYFRAME_PATHS = {
    "miguel": "keyframes/keyframes_1.json",
    "ze": "keyframes/keyframes_1.json",     # 👈 Replace this line
    "ana": "keyframes/keyframes_1.json",    # 👈 Replace this line
    "brandon": "keyframes/keyframes_1.json" # 👈 Replace this line
}
```

**Replace with your keyframe file**:
```python
"your_name": "keyframes/your_name_keyframes.json",
```

## Step 3: Setting Up Camera Waypoints

Camera waypoints create cinematic camera movements during your song. The camera smoothly moves between different positions and angles as your music plays.

### 🎥 **Understanding Camera Waypoints**

Each waypoint defines:
- `"time"`: When to start moving toward this position (in seconds)
- `"position"`: 3D coordinates `[x, y, z]` where the camera should be
- `"rotation"`: Camera angles `[x_rotation, y_rotation, z_rotation]` in degrees

### 🎮 **How to Find Camera Positions (Using Debug Mode)**

1. **Run the game in debug mode**:
   ```bash
   python main.py -debug
   ```

2. **Navigate to your instrument** in the selection phase and press Enter

3. **Control the camera manually** using these keys:
   - **W/S**: Move forward/backward
   - **A/D**: Move left/right  
   - **Q/E**: Move up/down
   - **Arrow Keys**: Rotate camera
   - **I/J/K/L**: Fine rotation adjustments

4. **Note the camera position and rotation**:
   - The current position and rotation are displayed on screen
   - Write down positions you like at specific times in your song

5. **Test your music timing**:
   - Play your song and note the timestamp when you want the camera at each position
   - Example: "At 15 seconds, I want a close-up of the instrument"

### ⚙️ **Configuration in config.py**

Find the `CAMERA_WAYPOINTS` section (around line 18):

```python
CAMERA_WAYPOINTS = {
    "miguel": [
        {
            "time": 0.0,
            "position": [-6.3, 6.2, 20],
            "rotation": [-28.9, -29, 0] 
        },
        {
            "time": 10.0,
            "position": [0, 1.7, 7],
            "rotation": [0, -90, 0]
        }
        # ... more waypoints
    ],
    "ze": [        # 👈 Replace this section
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
    ],
    # ... add your waypoints here
}
```

**Replace or add your waypoints**:
```python
"your_name": [
    {
        "time": 0.0,
        "position": [-6.3, 5.9, 20],     # Starting wide shot
        "rotation": [-28.9, -29, 0] 
    },
    {
        "time": 10.0,
        "position": [0, 1.2, 7],         # Move closer
        "rotation": [0, -90, 0]
    },
    {
        "time": 25.0,
        "position": [-2, 3, 12],         # Side angle
        "rotation": [-15, -45, 0]
    }
    # Add more waypoints as needed
]
```

## Step 4: Testing Your Implementation

1. **Save all your changes** to `config.py`

2. **Run the game**:
   ```bash
   python main.py
   ```

3. **Test your instrument**:
   - Navigate to your instrument in the selection screen
   - Press Enter to start gameplay
   - Your music should play with arrows spawning according to your keyframes
   - Camera should move according to your waypoints

4. **Debug mode testing**:
   ```bash
   python main.py -debug
   ```
   - Allows manual camera control to fine-tune waypoints
   - Displays current camera position and rotation

## Quick Reference

### File Locations Summary

| Element | Folder | Configuration |
|---------|--------|---------------|
| **Music Files** | `music/` | `INSTRUMENT_MUSIC_PATHS` in `config.py` |
| **Keyframe Files** | `keyframes/` | `INSTRUMENT_KEYFRAME_PATHS` in `config.py` |
| **Camera Waypoints** | N/A | `CAMERA_WAYPOINTS` in `config.py` |

### Debug Mode Commands

| Keys | Action |
|------|--------|
| `W/S` | Move camera forward/backward |
| `A/D` | Move camera left/right |
| `Q/E` | Move camera up/down |
| `Arrow Keys` | Rotate camera |
| `I/J/K/L` | Fine rotation adjustments |

### Valid Arrow Types
- `"up"` - Arrow pointing upward
- `"down"` - Arrow pointing downward  
- `"left"` - Arrow pointing left
- `"right"` - Arrow pointing right

## Common Issues and Solutions

### 🎵 **Music not playing**
- Check file path in `config.py` matches your file name exactly
- Ensure music file is in `.mp3` format
- Verify file isn't corrupted by playing it in a media player

### 🏹 **Arrows not spawning**
- Check keyframe JSON syntax (commas, brackets, quotes)
- Verify arrow types are exactly: `"up"`, `"down"`, `"left"`, `"right"`
- Ensure time values are numbers, not strings

### 📷 **Camera not moving**
- Check that your instrument name matches exactly in all three places:
  - `INSTRUMENT_MUSIC_PATHS`
  - `INSTRUMENT_KEYFRAME_PATHS` 
  - `CAMERA_WAYPOINTS`
- Verify waypoint times are in ascending order

### 🐛 **General debugging**
- Run with `-debug` flag to see console output
- Check console for error messages
- Ensure all file paths use forward slashes `/`

## Example Complete Implementation

Here's what your `config.py` entries should look like:

```python
# Music paths
INSTRUMENT_MUSIC_PATHS = {
    "miguel": "music/Mike_Oldfield__Tubular_bells.mp3",
    "ze": "music/fitnessgram.mp3",
    "ana": "music/piano_melody.mp3",           # Your music file
    "brandon": "music/rock_guitar.mp3"
}

# Keyframe paths  
INSTRUMENT_KEYFRAME_PATHS = {
    "miguel": "keyframes/keyframes_1.json",
    "ze": "keyframes/keyframes_1.json",
    "ana": "keyframes/ana_piano.json",         # Your keyframe file
    "brandon": "keyframes/brandon_rock.json"
}

# Camera waypoints
CAMERA_WAYPOINTS = {
    "miguel": [ /* existing waypoints */ ],
    "ze": [ /* existing waypoints */ ],
    "ana": [                                   # Your camera waypoints
        {
            "time": 0.0,
            "position": [-6.3, 5.9, 20],
            "rotation": [-28.9, -29, 0] 
        },
        {
            "time": 15.0,
            "position": [2, 2, 8],
            "rotation": [0, -120, 0]
        }
    ],
    "brandon": [ /* brandon's waypoints */ ]
}
```

Now you're ready to implement your part! Good luck! 🎮🎵 