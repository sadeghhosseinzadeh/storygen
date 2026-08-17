from PIL import Image
from storygen.utils import remove_background

def template_1rem(photo_1):
    """
    This version ONLY removes the background of the given photo
    and returns the cleaned image.
    """

    # Remove background using your existing utility
    photo_1_rem = remove_background(photo_1)

    # Ensure output is RGBA (transparent background)
    if photo_1_rem.mode != "RGBA":
        photo_1_rem = photo_1_rem.convert("RGBA")

    return photo_1_rem
