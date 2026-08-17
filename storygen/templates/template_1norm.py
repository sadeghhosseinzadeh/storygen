from PIL import Image
import numpy as np
from storygen.utils import remove_background

def normalize_shoe(img, padding=50):
    img = img.convert("RGBA")
    data = np.array(img)
    alpha = data[:, :, 3]

    ys, xs = np.where(alpha > 0)
    if len(xs) == 0 or len(ys) == 0:
        return img

    x1, x2 = xs.min(), xs.max()
    y1, y2 = ys.min(), ys.max()

    cropped = img.crop((x1, y1, x2, y2))

    bg_pixels = data[alpha == 0][:, :3]
    if len(bg_pixels) > 0:
        bg_color = tuple(bg_pixels.mean(axis=0).astype(int))
    else:
        bg_color = (255, 255, 255)

    new_w = cropped.width + padding * 2
    new_h = cropped.height + padding * 2

    canvas = Image.new("RGBA", (new_w, new_h), bg_color + (255,))
    canvas.paste(cropped, (padding, padding), cropped)

    return canvas


def template_1norm(photo_1):
    # Step 1: remove background
    photo_1_rem = remove_background(photo_1)
    photo_1_rem = photo_1_rem.convert("RGBA")

    # Step 2: normalize
    photo_1_norm = normalize_shoe(photo_1_rem, padding=50)

    # Step 3: return final normalized shoe
    return photo_1_norm
