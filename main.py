"""
Main entry point for the rhythm instrument game.
"""

import argparse
from game import Game
from config import SCREEN_SIZE

if __name__ == "__main__":
    # Set up argument parser
    parser = argparse.ArgumentParser(description='Rhythm Instrument Game')
    parser.add_argument('-debug', '--debug', action='store_true', help='Enable debug mode')
    
    # Parse arguments
    args = parser.parse_args()
    
    # Start the game with the configured screen size and debug flag
    Game(screen_size=SCREEN_SIZE, debug_mode=args.debug).run() 