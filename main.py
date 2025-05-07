"""
Main entry point for the rhythm instrument game.
"""

from game import Game
from config import SCREEN_SIZE

if __name__ == "__main__":
    # Start the game with the configured screen size
    Game(screen_size=SCREEN_SIZE).run() 