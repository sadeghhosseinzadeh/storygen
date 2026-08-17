
from PIL import Image
import numpy as np
from storygen.utils import remove_background

def normalize_shoe(img, padding=50):
    """
    Normalize shoe image by:
    - detecting shoe edges (non-transparent pixels)
    - cropping tightly
    - adding fixed padding on all sides
    - recreating background using average background color
    """

    # Ensure RGBA
    img = img.convert("RGBA")

    # Convert to numpy for pixel analysis
    data = np.array(img)
    alpha = data[:, :, 3]

    # Detect non-transparent pixels (shoe)
    ys, xs = np.where(alpha > 0)

    if len(xs) == 0 or len(ys) == 0:
        # No shoe detected, return original
        return img

    # Bounding box of the shoe
    x1, x2 = xs.min(), xs.max()
    y1, y2 = ys.min(), ys.max()

    # Crop tightly
    cropped = img.crop((x1, y1, x2, y2))

    # Compute average background color from transparent pixels
    bg_pixels = data[alpha == 0][:, :3]
    if len(bg_pixels) > 0:
        bg_color = tuple(bg_pixels.mean(axis=0).astype(int))
    else:
        bg_color = (255, 255, 255)  # fallback

    # Create new canvas with padding
    new_w = cropped.width + padding * 2
    new_h = cropped.height + padding * 2

    canvas = Image.new("RGBA", (new_w, new_h), bg_color + (255,))

    # Paste shoe centered with padding
    canvas.paste(cropped, (padding, padding), cropped)

    return canvas



def template_1norm(photo_1):
    """
    This version ONLY removes the background of the given photo
    and returns the cleaned image.
    """
    photo_1_norm = normalize_shoe(photo_1)
    '''
    # Remove background using your existing utility
    photo_1_rem = remove_background(photo_1)
    if photo_1_rem.mode != "RGBA":
        photo_1_rem = photo_1_rem.convert("RGBA")
    '''
  
    return photo_1_norm
