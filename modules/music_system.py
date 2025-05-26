"""
Music system module for handling music playback and keyframe management.
"""

import time
import json
import pygame
from config import INSTRUMENT_MUSIC_PATHS, INSTRUMENT_KEYFRAME_PATHS, SELECTION_MUSIC_PATH

class MusicSystem:
    """
    Manages music playback and keyframe processing for the game.
    """
    
    def __init__(self, arrow_manager, game_instance=None):
        """
        Initialize the music system.
        
        Parameters:
            arrow_manager: The arrow manager instance to spawn arrows
            game_instance: Reference to the Game instance for recalculating travel time
        """
        self.arrow_manager = arrow_manager
        self.game_instance = game_instance  # Store reference to game instance
        self.music_loaded = False
        self.music_playing = False
        self.music_start_time = 0
        self.music_file = None
        self.keyframes = []
        self.current_keyframe_index = 0
        self.timing_adjustment = 0.0 # Initial value before dynamic calculation
        self.arrow_travel_time = 0.0  # To be calculated dynamically
        self.selection_music_playing = False
        
        # Initialize pygame mixer
        try:
            pygame.mixer.init()
            print("Pygame mixer initialized successfully")
        except Exception as e:
            print(f"Error initializing pygame mixer: {e}")
            
        # Define instrument tracks using config values
        self.INSTRUMENT_TRACKS = {
            0: {  # Miguel's instrument
                "music": INSTRUMENT_MUSIC_PATHS["miguel"],
                "keyframes": INSTRUMENT_KEYFRAME_PATHS["miguel"]
            },
            1: {  # Ze's instrument
                "music": INSTRUMENT_MUSIC_PATHS["ze"],
                "keyframes": INSTRUMENT_KEYFRAME_PATHS["ze"]
            },
            2: {  # Ana's instrument
                "music": INSTRUMENT_MUSIC_PATHS["ana"],
                "keyframes": INSTRUMENT_KEYFRAME_PATHS["ana"]
            },
            3: {  # Brandon's instrument
                "music": INSTRUMENT_MUSIC_PATHS["brandon"],
                "keyframes": INSTRUMENT_KEYFRAME_PATHS["brandon"]
            }
        }
        
        # Define selection music from config
        self.SELECTION_MUSIC = SELECTION_MUSIC_PATH
    
    def set_arrow_travel_time(self, time_value):
        """Set the time it takes for arrows to travel from spawn to target"""
        # time_value is the calculated nominal travel time (e.g., Distance / Speed)
        # Logs show arrows arriving ~0.21s earlier than this nominal time.
        # Adjust the travel time used for spawning to this observed actual travel time.
        observed_discrepancy = 0.21  # Seconds, from TIMING LOG Diff values being consistently around -0.21s
        self.arrow_travel_time = time_value - observed_discrepancy
        #print(f"Nominal arrow travel time calculated: {time_value:.2f} seconds")
        #print(f"Adjusted arrow travel time for spawning (actual observed): {self.arrow_travel_time:.2f} seconds")
        
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

            self.music_loaded = True
            self.music_file = music_file
            print(f"Successfully loaded music file: {music_file}")
            return True
        except pygame.error as e:
            print(f"Error loading music '{music_file}': {e}")
            self.music_loaded = False
            self.music_file = None
            return False
            
    def play_music(self, loop=False):
        """
        Start music playback and record start time.
        
        Parameters:
            loop: Whether to loop the music (default: False)
            
        Returns:
            True if successful, False otherwise
        """
        if self.music_loaded:
            try:
                print(f"Attempting to play music: {self.music_file}")
                # Set loop count (-1 for infinite loop, 0 for no loop)
                loop_count = -1 if loop else 0
                pygame.mixer.music.play(loops=loop_count)
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

    def load_selection_music(self):
        """
        Load the selection menu background music.
        
        Returns:
            True if successful, False otherwise
        """
        result = self.load_music(self.SELECTION_MUSIC)
        if result:
            # Stop any previously playing music first
            if self.music_playing:
                self.stop_music()
            # Mark that we're not playing gameplay music
            self.music_playing = False
        return result
    
    def play_selection_music(self):
        """
        Play the selection menu background music in a loop.
        
        Returns:
            True if successful, False otherwise
        """
        success = self.play_music(loop=True)
        if success:
            self.selection_music_playing = True
        return success
    
    def stop_music(self):
        """
        Stop any currently playing music.
        
        Returns:
            True if successful, False otherwise
        """
        try:
            pygame.mixer.music.stop()
            self.music_playing = False
            self.selection_music_playing = False
            print("Music playback stopped.")
            return True
        except Exception as e:
            print(f"Error stopping music: {e}")
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
        # Stop any selection music that might be playing
        if self.selection_music_playing:
            self.stop_music()
            self.selection_music_playing = False
            
        track_info = self.INSTRUMENT_TRACKS.get(instrument_index)
        
        if track_info:
            # First load the music and keyframes
            music_loaded = self.load_music(track_info["music"])
            keyframes_loaded = self.load_keyframes(track_info["keyframes"])
            
            # Se for o instrumento do Brandon (índice 3), aumentar o volume
            if music_loaded and instrument_index == 3:  # Brandon's instrument
                pygame.mixer.music.set_volume(3)  
                print(f"Volume aumentado para o instrumento do Brandon: x3")
            
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
        Process keyframes and trigger arrow creation based on music time.
        Adjusts spawn time based on arrow_travel_time.

        Parameters:
            create_arrow_callback: Function to call when an arrow needs to be created.
                                   This callback should accept an 'arrow_type' string and return the created arrow.
        """
        if not self.music_playing or self.selection_music_playing or not self.keyframes: # Added selection_music_playing
            return

        # Recalculate arrow travel time based on current camera and pivot position
        self.update_arrow_travel_time()
        
        current_music_time = self.get_music_time()

        while self.current_keyframe_index < len(self.keyframes):
            keyframe = self.keyframes[self.current_keyframe_index]
            
            # Calculate the actual time an arrow needs to be spawned
            # so it arrives at the ring at keyframe['time']
            spawn_trigger_time = keyframe['time'] - self.arrow_travel_time
            
            if current_music_time >= spawn_trigger_time:
                # Log the timing details for debugging
                # Ensure all float values are formatted to 3 decimal places for consistent logging.
                print(f"TIMING LOG: MusicTime={current_music_time:.3f}, "
                      f"KeyframeTargetTime={keyframe['time']:.3f}, "
                      f"ArrowTravelTime={self.arrow_travel_time:.3f}, "
                      f"SpawnTriggerTime={spawn_trigger_time:.3f}, "
                      f"Diff={(current_music_time - spawn_trigger_time):.3f}")

                arrow_type_to_spawn = keyframe['arrow_type']
                
                if callable(create_arrow_callback):
                    new_arrow = create_arrow_callback(arrow_type_str=arrow_type_to_spawn)
                    if new_arrow:
                        # Store the original intended arrival time on the arrow for potential use
                        # in scoring or debugging.
                        new_arrow.keyframe_target_time = keyframe['time']
                
                self.current_keyframe_index += 1
            else:
                # Keyframes are sorted by time, so no need to check further
                # if the current music time hasn't reached the spawn_trigger_time
                # for the current keyframe.
                break 

    def update_arrow_travel_time(self):
        """Recalculate arrow travel time dynamically based on current camera and pivot position"""
        if self.game_instance is not None:
            # Request a fresh calculation from the game instance
            new_travel_time = self.game_instance.calculate_arrow_travel_time()
            
            # Update the arrow travel time if calculation successful
            if new_travel_time > 0:
                # Keep track of the old travel time for logging purposes
                old_travel_time = self.arrow_travel_time
                self.arrow_travel_time = new_travel_time
                
                # Log the change
                #print(f"Arrow travel time updated dynamically: {old_travel_time:.2f}s -> {self.arrow_travel_time:.2f}s")
                
                # Adjust the timing based on observed discrepancy, if applicable
                observed_discrepancy = 0.21  # Seconds, hardcoded to match existing adjustment
                self.arrow_travel_time = new_travel_time - observed_discrepancy
                
                return True
        
        return False
        
    def is_music_finished(self):
        """
        Check if the currently playing music track has finished.
        
        Returns:
            True if music has finished or is not playing, False otherwise
        """
        if not self.music_playing:
            return True
            
        # Check if pygame is playing the music
        if pygame.mixer.music.get_busy():
            return False
        else:
            # Music has finished playing
            self.music_playing = False
            print("Music track has finished playing")