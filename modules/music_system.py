"""
Music system module for handling music playback and keyframe management.
"""

import time
import json
import pygame

class MusicSystem:
    """
    Manages music playback and keyframe processing for the game.
    """
    
    def __init__(self, arrow_manager):
        """
        Initialize the music system.
        
        Parameters:
            arrow_manager: The arrow manager instance to spawn arrows
        """
        self.arrow_manager = arrow_manager
        self.music_loaded = False
        self.music_playing = False
        self.music_start_time = 0
        self.music_file = None
        self.keyframes = []
        self.current_keyframe_index = 0
        self.timing_adjustment = 0.9  # Default timing adjustment
        self.arrow_travel_time = 0.0  # To be calculated later
        
        # Initialize pygame mixer
        try:
            pygame.mixer.init()
            print("Pygame mixer initialized successfully")
        except Exception as e:
            print(f"Error initializing pygame mixer: {e}")
            
        # Define instrument tracks
        self.INSTRUMENT_TRACKS = {
            0: {  # Miguel's instrument
                "music": "music/fitnessgram.mp3",
                "keyframes": "keyframes/keyframes_1.json"
            },
            1: {  # Ze's instrument
                "music": "music/track2.mp3",
                "keyframes": "keyframes/keyframes_2.json"
            },
            2: {  # Ana's instrument
                "music": "music/track3.mp3",
                "keyframes": "keyframes/keyframes_3.json"
            },
            3: {  # Brandon's instrument
                "music": "music/track4.mp3",
                "keyframes": "keyframes/keyframes_4.json"
            }
        }
    
    def set_arrow_travel_time(self, time_value):
        """Set the time it takes for arrows to travel from spawn to target"""
        self.arrow_travel_time = time_value
        print(f"Arrow travel time set to: {self.arrow_travel_time:.2f} seconds")
        
    def load_music(self, music_file):
        """
        Load a specific music file.
        
        Parameters:
            music_file: Path to the music file
            
        Returns:
            True if successful, False otherwise
        """
        try:
            print(f"Attempting to load music file: {music_file}")
            pygame.mixer.music.load(music_file)
            pygame.mixer.music.set_volume(0.2)  # Set volume to 20%
            self.music_loaded = True
            self.music_file = music_file
            print(f"Successfully loaded music file: {music_file}")
            return True
        except pygame.error as e:
            print(f"Error loading music '{music_file}': {e}")
            self.music_loaded = False
            self.music_file = None
            return False
            
    def play_music(self):
        """
        Start music playback and record start time.
        
        Returns:
            True if successful, False otherwise
        """
        if self.music_loaded:
            try:
                print(f"Attempting to play music: {self.music_file}")
                pygame.mixer.music.play()
                self.music_playing = True
                self.music_start_time = time.time()
                self.current_keyframe_index = 0
                print(f"Music playback started. Start time: {self.music_start_time}")
                return True
            except Exception as e:
                print(f"Error playing music: {e}")
                return False
        print("Music not loaded, cannot play.")
        return False

    def load_keyframes(self, keyframe_file):
        """
        Load keyframe data from JSON file.
        
        Parameters:
            keyframe_file: Path to the keyframe JSON file
            
        Returns:
            True if successful, False otherwise
        """
        try:
            with open(keyframe_file, 'r') as file:
                keyframes_data = json.load(file)
            
            # Validate and process keyframes
            self.keyframes = []
            valid_arrow_types = ["up", "down", "left", "right"]
            
            for i, keyframe in enumerate(keyframes_data):
                if 'time' not in keyframe:
                    raise ValueError(f"Keyframe {i} in '{keyframe_file}' missing 'time' field.")
                if 'arrow_type' not in keyframe:
                    # Making arrow_type a required field
                    raise ValueError(f"Keyframe {i} in '{keyframe_file}' missing 'arrow_type' field.")
                if not isinstance(keyframe['arrow_type'], str) or keyframe['arrow_type'].lower() not in valid_arrow_types:
                    valid_types = ", ".join(valid_arrow_types)
                    raise ValueError(f"Keyframe {i} in '{keyframe_file}' has invalid 'arrow_type': '{keyframe['arrow_type']}'. Valid types are: {valid_types}.")
                
                # Store the original string type for now, will be resolved at creation
                self.keyframes.append({'time': float(keyframe['time']), 'arrow_type': keyframe['arrow_type']})
                   
            # Sort keyframes by time
            self.keyframes.sort(key=lambda k: k['time'])
            self.current_keyframe_index = 0 # Reset index when new keyframes are loaded
            print(f"Keyframes from '{keyframe_file}' loaded and sorted successfully ({len(self.keyframes)} keyframes).")
            return True
        except FileNotFoundError:
            print(f"Error loading keyframes: File '{keyframe_file}' not found.")
            self.keyframes = [] # Ensure keyframes list is empty on error
            return False
        except json.JSONDecodeError as e:
            print(f"Error loading keyframes: JSON decoding error in '{keyframe_file}': {e}")
            self.keyframes = []
            return False
        except ValueError as e: # Catch our custom validation errors
            print(f"Error loading keyframes: Data validation error in '{keyframe_file}': {e}")
            self.keyframes = []
            return False
        except Exception as e:
            print(f"Error loading keyframes from '{keyframe_file}': {e}")
            self.keyframes = []
            return False

    def calibrate_timing(self, adjustment_seconds):
        """
        Adjust arrow timing by specified amount in seconds.
        
        Parameters:
            adjustment_seconds: Seconds to adjust timing by
        """
        self.timing_adjustment = adjustment_seconds
        print(f"Timing adjustment set to: {self.timing_adjustment} seconds")
           
    def get_music_time(self):
        """
        Get current music playback position in seconds with calibration adjustment.
        
        Returns:
            Current music time in seconds
        """
        if not self.music_playing or not hasattr(self, 'music_start_time'):
            return 0
        
        # Calculate raw music time
        current_raw_time = time.time() - self.music_start_time
        
        # Apply calibration adjustment
        adjusted_time = current_raw_time + self.timing_adjustment
        return adjusted_time

    def load_track_for_instrument(self, instrument_index):
        """
        Load music and keyframes for the selected instrument.
        
        Parameters:
            instrument_index: Index of the selected instrument
            
        Returns:
            True if successful, False otherwise
        """
        track_info = self.INSTRUMENT_TRACKS.get(instrument_index)
        
        if track_info:
            # First load the music and keyframes
            music_loaded = self.load_music(track_info["music"])
            keyframes_loaded = self.load_keyframes(track_info["keyframes"])
            
            if music_loaded and keyframes_loaded:
                print(f"Loaded music track and keyframes for instrument {instrument_index}")
                return True
            else:
                print(f"Failed to load music or keyframes for instrument {instrument_index}")
                
                # Set up simulation mode if loading failed
                self.music_playing = True
                self.music_start_time = time.time()
                print(f"Music playback SIMULATED. music_playing: {self.music_playing}, music_start_time: {self.music_start_time:.2f}")
                return False
        else:
            print(f"No track information found for instrument {instrument_index}")
            return False
            
    def update_keyframe_arrows(self, create_arrow_callback):
        """
        Check if it's time to spawn arrows according to keyframes and music time.
        
        Parameters:
            create_arrow_callback: Function to create and return an arrow
        """
        if not self.keyframes or self.current_keyframe_index >= len(self.keyframes):
            return # No keyframes loaded or all keyframes processed

        if not hasattr(self, 'arrow_travel_time') or self.arrow_travel_time <= 0:
            print("Error: arrow_travel_time not properly set. Cannot spawn keyframe arrows accurately.")
            return

        current_music_time = self.get_music_time()

        # Process all keyframes that should have spawned by now
        while (self.current_keyframe_index < len(self.keyframes) and
               current_music_time >= (self.keyframes[self.current_keyframe_index]['time'] - self.arrow_travel_time)):
            
            keyframe = self.keyframes[self.current_keyframe_index]
            arrow_type_to_spawn = keyframe.get('arrow_type') # Already validated in load_keyframes

            print(f"Spawning arrow for keyframe {self.current_keyframe_index}: time {keyframe['time']:.2f}s, type '{arrow_type_to_spawn}', music_time: {current_music_time:.2f}s")
            
            # Call the provided callback to create an arrow
            new_arrow = create_arrow_callback(arrow_type_to_spawn)
            
            self.current_keyframe_index += 1 