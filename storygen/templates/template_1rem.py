
from PIL import Image
from rembg import remove
from io import BytesIO

# 1. Remove background
def remove_background(path: str, margin: int = 0):
    # Step 1: Remove background
    with open(path, "rb") as f:
        input_bytes = f.read()
    output_bytes = remove(input_bytes)
    img = Image.open(BytesIO(output_bytes)).convert("RGBA")

    # Step 2: Get bounding box of non-transparent pixels
    bbox = img.getbbox()
    if bbox:
        x1, y1, x2, y2 = bbox

        # Step 3: Expand bounding box by margin
        x1 = max(0, x1 - margin)
        y1 = max(0, y1 - margin)
        x2 = min(img.width, x2 + margin)
        y2 = min(img.height, y2 + margin)

        # Step 4: Crop to expanded bounding box
        img = img.crop((x1, y1, x2, y2))

    return img
    
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
