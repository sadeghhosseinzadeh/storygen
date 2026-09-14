from PIL import Image, ImageFilter, ImageDraw
import numpy as np
from storygen.utils import detect_shoe_direction

def place_shoe_1c(
    canvas,
    img,
    pos=None,
    max_size=(800, 600),
    angle_left=20,
    angle_right=-20,
    center_x=True,
    center_y=False,
    shadow=True,
    shadow_offset=(0, 40),
    shadow_blur=35,

    # --- SHADOW TUNING ---
    toe_width=90,          # thicker front
    heel_width=20,         # thinner back
    shadow_length=0.55,    # % of shoe length that gets shadow
    shadow_alpha=150,      # darkness
    shadow_height=30       # vertical thickness
):
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

    # --- Alpha mask ---
    arr = np.array(rotated)
    alpha = arr[:, :, 3]
    ys, xs = np.where(alpha > 0)

    # Toe & heel detection
    if direction == "left":
        toe_x = xs.min()
        heel_x = xs.max()
    else:
        toe_x = xs.max()
        heel_x = xs.min()

    # Normalize ordering (IMPORTANT FIX)
    x_start = min(toe_x, heel_x)
    x_end   = max(toe_x, heel_x)

    # Sole line
    bottom_y = ys.max()

    # Midpoint for centering
    mid_x = int((toe_x + heel_x) / 2)

    # --- Target position ---
    if pos is None:
        target_x = W//2 if center_x else 0
        target_y = H//2 if center_y else H//2
    else:
        target_x, target_y = pos
        if center_x: target_x = W//2
        if center_y: target_y = H//2

    pos_x = target_x - mid_x
    pos_y = target_y - bottom_y

    # --- Shadow ---
    if shadow:
        shadow_layer = Image.new("RGBA", (rw, rh), (0,0,0,0))
        shadow_draw = ImageDraw.Draw(shadow_layer)

        # Shadow end (shorter)
        shadow_end_x = int(x_start + (x_end - x_start) * shadow_length)

        shadow_center_y = bottom_y + 10

        # Toe shadow (wide)
        shadow_draw.ellipse(
            [
                toe_x - toe_width,
                shadow_center_y - shadow_height//2,
                toe_x + toe_width,
                shadow_center_y + shadow_height//2,
            ],
            fill=(0,0,0,shadow_alpha)
        )

        # Mid band
        shadow_draw.rectangle(
            [
                x_start,
                shadow_center_y - shadow_height//2,
                shadow_end_x,
                shadow_center_y + shadow_height//2,
            ],
            fill=(0,0,0,shadow_alpha - 40)
        )

        # Heel shadow (small)
        shadow_draw.ellipse(
            [
                shadow_end_x - heel_width,
                shadow_center_y - shadow_height//2,
                shadow_end_x + heel_width,
                shadow_center_y + shadow_height//2,
            ],
            fill=(0,0,0,shadow_alpha - 80)
        )

        shadow_layer = shadow_layer.filter(ImageFilter.GaussianBlur(shadow_blur))

        canvas.paste(
            shadow_layer,
            (pos_x + shadow_offset[0], pos_y + shadow_offset[1]),
            shadow_layer
        )

    # --- Paste shoe ---
    canvas.paste(rotated, (pos_x, pos_y), rotated)

    return canvas
