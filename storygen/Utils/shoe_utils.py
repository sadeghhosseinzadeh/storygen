from PIL import Image, ImageFilter, ImageDraw
import numpy as np
from storygen.utils import detect_shoe_direction

def place_shoe_1c(canvas, img, pos=None, max_size=(800,600),
               angle_left=20, angle_right=-20,
               center_x=True, center_y=False,
               shadow=True, shadow_offset=(60, 20), shadow_blur=25):
    """
    Improved shoe placement:
    - Centers AFTER rotation (true anchor)
    - Detects toe vs heel
    - Draws horizontal shadow band from toe→heel
    """

    W, H = canvas.size

    # --- Resize shoe ---
    sw, sh = img.size
    max_w, max_h = max_size
    ratio = min(max_w/sw, max_h/sh)
    new_w, new_h = int(sw * ratio), int(sh * ratio)
    shoe = img.resize((new_w, new_h), Image.LANCZOS)

    # --- Detect direction ---
    direction = detect_shoe_direction(shoe)
    final_angle = angle_left if direction == "left" else angle_right

    # --- Rotate shoe ---
    rotated = shoe.rotate(final_angle, expand=True)
    rw, rh = rotated.size

    # --- Compute bottom anchor AFTER rotation ---
    arr = np.array(rotated)
    alpha = arr[:,:,3]
    ys, xs = np.where(alpha > 0)
    bottom_y = ys.max()
    xs_bottom = xs[ys == bottom_y]
    bottom_mid_x = int((xs_bottom.min() + xs_bottom.max()) / 2)

    # --- Target position ---
    if pos is None:
        target_x = W//2 if center_x else 0
        target_y = H//2 if center_y else H//2
    else:
        target_x, target_y = pos
        if center_x: target_x = W//2
        if center_y: target_y = H//2

    # Anchor bottom to target_y
    pos_y = target_y - bottom_y
    pos_x = target_x - bottom_mid_x

    # --- Shadow ---
    if shadow:
        # Detect toe & heel
        if direction == "left":
            toe_x = xs.min(); heel_x = xs.max()
        else:
            toe_x = xs.max(); heel_x = xs.min()
        toe_y = int(ys[xs == toe_x].mean())
        heel_y = int(ys[xs == heel_x].mean())

        # Shadow layer
        shadow_layer = Image.new("RGBA", (rw, rh), (0,0,0,0))
        shadow_draw = ImageDraw.Draw(shadow_layer)

        shadow_color = (0,0,0,120)
        shadow_draw.rectangle([min(toe_x, heel_x),
                               min(toe_y, heel_y)-15,
                               max(toe_x, heel_x),
                               max(toe_y, heel_y)+15],
                              fill=shadow_color)

        shadow_layer = shadow_layer.filter(ImageFilter.GaussianBlur(shadow_blur))

        # Paste shadow with offset
        canvas.paste(shadow_layer, (pos_x + shadow_offset[0], pos_y + shadow_offset[1]), shadow_layer)

    # --- Paste shoe ---
    canvas.paste(rotated, (pos_x, pos_y), rotated)

    return canvas
