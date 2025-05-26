import pygame
import sys

from core.input import Input
from core.utils import Utils


class Base:
    def __init__(self, screen_size=(512, 512), fullscreen=False, fullscreen_resolution=None):
        # Initialize all pygame modules
        pygame.init()
        # Indicate rendering details
        display_flags = pygame.DOUBLEBUF | pygame.OPENGL

        # Add fullscreen flag if requested
        if fullscreen:
            display_flags |= pygame.FULLSCREEN

        # Initialize buffers to perform antialiasing
        pygame.display.gl_set_attribute(pygame.GL_MULTISAMPLEBUFFERS, 1)
        pygame.display.gl_set_attribute(pygame.GL_MULTISAMPLESAMPLES, 4)
        # Use a core OpenGL profile for cross-platform compatibility
        pygame.display.gl_set_attribute(pygame.GL_CONTEXT_PROFILE_MASK, pygame.GL_CONTEXT_PROFILE_CORE)

        # Determine the resolution to use
        if fullscreen and fullscreen_resolution is not None:
            # Use specified fullscreen resolution
            resolution = fullscreen_resolution
        elif fullscreen:
            # Use native desktop resolution
            info = pygame.display.Info()
            resolution = (info.current_w, info.current_h)
        else:
            # Use windowed mode with specified screen_size
            resolution = screen_size

        # Create and display the window
        self._screen = pygame.display.set_mode(resolution, display_flags)

        # Store actual screen dimensions for use by the application
        self._actual_screen_size = self._screen.get_size()
        # Set the text that appears in the title bar of the window
        pygame.display.set_caption("Graphics Window")
        # Determine if main loop is active
        self._running = True
        # Manage time-related data and operations
        self._clock = pygame.time.Clock()
        # Manage user input
        self._input = Input()
        # number of seconds application has been running
        self._time = 0
        # Print the system information
        Utils.print_system_info()

    @property
    def delta_time(self):
        return self._delta_time

    @property
    def input(self):
        return self._input

    @property
    def time(self):
        return self._time

    @time.setter
    def time(self, value):
        self._time = value

    def initialize(self):
        """ Implement by extending class """
        pass

    def update(self):
        """ Implement by extending class """
        pass

    @property
    def actual_screen_size(self):
        return self._actual_screen_size

    def toggle_fullscreen(self):
        """Toggle between fullscreen and windowed mode"""
        # Get current display flags
        current_flags = self._screen.get_flags()

        if current_flags & pygame.FULLSCREEN:
            # Currently fullscreen, switch to windowed
            display_flags = pygame.DOUBLEBUF | pygame.OPENGL
            # Use the original screen size for windowed mode
            resolution = (1280, 720)  # Default windowed size
        else:
            # Currently windowed, switch to fullscreen
            display_flags = pygame.DOUBLEBUF | pygame.OPENGL | pygame.FULLSCREEN
            # Use native desktop resolution
            info = pygame.display.Info()
            resolution = (info.current_w, info.current_h)

        # Recreate the display
        self._screen = pygame.display.set_mode(resolution, display_flags)
        self._actual_screen_size = self._screen.get_size()

        return self._actual_screen_size


    def run(self):
        # Startup #
        self.initialize()
        # main loop #
        while self._running:
            # process input #
            self._input.update()
            if self._input.quit:
                self._running = False
            # seconds since iteration of run loop
            self._delta_time = self._clock.get_time() / 1000
            # Increment time application has been running
            self._time += self._delta_time
            # Update #
            self.update()
            # Render #
            # Display image on screen
            pygame.display.flip()
            # Pause if necessary to achieve 60 FPS
            self._clock.tick(60)
        # Shutdown #
        pygame.quit()
        sys.exit()
