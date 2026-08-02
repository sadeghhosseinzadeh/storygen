from importlib.resources import files
from PIL import ImageFont

def lighten_color(color, strength=0.15):
    """Blend main color with white at given strength."""
    return tuple(int(c * strength + 255 * (1 - strength)) for c in color)

def load_font(name: str, size: int):
    """Load a font from the bundled fonts folder."""
    font_path = files("storygen.fonts").joinpath(name)
    return ImageFont.truetype(str(font_path), size)
