"""
Main entry point for the rhythm instrument game.
"""

import argparse
from game import Game
from config import SCREEN_SIZE, FULLSCREEN_ENABLED, FULLSCREEN_RESOLUTION

if __name__ == "__main__":
    # Set up argument parser
    parser = argparse.ArgumentParser(description='Rhythm Instrument Game')
    parser.add_argument('-debug', '--debug', action='store_true', help='Enable debug mode')

    parser.add_argument('-fullscreen', '--fullscreen', action='store_true', help='Enable fullscreen mode')
    parser.add_argument('-windowed', '--windowed', action='store_true', help='Force windowed mode (overrides config)')

    # Parse arguments
    args = parser.parse_args()

    # Determine fullscreen mode
    fullscreen_mode = FULLSCREEN_ENABLED
    if args.fullscreen:
        fullscreen_mode = True
    elif args.windowed:
        fullscreen_mode = False

    # Start the game with the configured screen size and options
    Game(
        screen_size=SCREEN_SIZE,
        debug_mode=args.debug,
        fullscreen=fullscreen_mode,
        fullscreen_resolution=FULLSCREEN_RESOLUTION
    ).run()