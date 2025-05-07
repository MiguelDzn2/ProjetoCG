import pygame

from core_ext.texture import Texture

class TextTexture(Texture):
    """
    Define a text texture by using pygame
    """
    def __init__(self, text="Python graphics",
                 system_font_name="Arial",
                 font_file_name=None,
                 font_size=24,
                 font_color=(0, 0, 0),
                 background_color=(255, 255, 255),
                 transparent=False,
                 image_width=None,
                 image_height=None,
                 align_horizontal=0.0,
                 align_vertical=0.0,
                 image_border_width=0,
                 image_border_color=(0, 0, 0)):
        super().__init__()
        # Store parameters for later use in update_text
        self._system_font_name = system_font_name
        self._font_file_name = font_file_name
        self._font_size = font_size
        self._font_color = font_color
        self._background_color = background_color
        self._transparent = transparent
        self._image_width = image_width
        self._image_height = image_height
        self._align_horizontal = align_horizontal
        self._align_vertical = align_vertical
        self._image_border_width = image_border_width
        self._image_border_color = image_border_color
        
        # Create the initial texture
        self._create_texture(text)
        
    def _create_texture(self, text):
        # Set a default font
        font = pygame.font.SysFont(self._system_font_name, self._font_size)
        # The font can be overrided by loading font file
        if self._font_file_name is not None:
            font = pygame.font.Font(self._font_file_name, self._font_size)
        # Render text to (antialiased) surface
        font_surface = font.render(text, True, self._font_color)
        # Determine size of rendered text for alignment purposes
        (text_width, text_height) = font.size(text)
        # If image dimensions are not specified,
        # use the font surface size as default
        image_width = self._image_width if self._image_width is not None else text_width
        image_height = self._image_height if self._image_height is not None else text_height
        # Create a surface to store the image of text
        # (with the transparency channel by default)
        self._surface = pygame.Surface((image_width, image_height),
                                       pygame.SRCALPHA)
        # Set a background color used when not transparent
        if not self._transparent:
            self._surface.fill(self._background_color)
        # Attributes align_horizontal, align_vertical define percentages,
        # measured from top-left corner
        corner_point = (self._align_horizontal * (image_width - text_width),
                        self._align_vertical * (image_height - text_height))
        destination_rectangle = font_surface.get_rect(topleft=corner_point)
        # Add border (optionally)
        if self._image_border_width > 0:
            pygame.draw.rect(self._surface, self._image_border_color,
                             [0, 0, image_width, image_height], self._image_border_width)
        # Apply font_surface to a correct position on the final surface
        self._surface.blit(font_surface, destination_rectangle)
        self.upload_data()
        
    def update_text(self, text):
        """Update the text content of the texture"""
        self._create_texture(text)

