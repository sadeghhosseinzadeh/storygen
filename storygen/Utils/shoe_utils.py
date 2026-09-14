from PIL import Image, ImageFilter, ImageDraw
import numpy as np
from storygen.utils import detect_shoe_direction

def place_shoe_1c(
    canvas,
    img,
    shadow_png,
    pos=None,
    max_size=(800,600),
    angle_left=20,
    angle_right=-20,
    center_x=True,
    center_y=False,

    # Shadow PNG controls
    shadow_offset=(0, 40),   # move shadow up/down/left/right
    shadow_rotation=0,       # rotate shadow PNG
    shadow_scale=1.0,        # scale shadow PNG
    flip_shadow=True         # auto flip when shoe faces left
):
    """
    Places rotated shoe centered using toe→heel midpoint,
    detects lowest point of shoe,
    pastes external shadow PNG under the shoe.
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

    # --- Alpha mask analysis ---
    arr = np.array(rotated)
    alpha = arr[:,:,3]
    ys, xs = np.where(alpha > 0)

    # Toe & heel detection
    if direction == "left":
        toe_x = xs.min()
        heel_x = xs.max()
    else:
        toe_x = xs.max()
        heel_x = xs.min()

    # Bottom of shoe (lowest pixel)
    bottom_y = ys.max()

    # Midpoint between toe & heel (for centering)
    mid_x = int((toe_x + heel_x) / 2)

    # --- Target position ---
    if pos is None:
        target_x = W//2 if center_x else 0
        target_y = H//2 if center_y else H//2
    else:
        target_x, target_y = pos
        if center_x:
            target_x = W//2
        if center_y:
            target_y = H//2

    # Anchor shoe so toe→heel midpoint aligns to target
    pos_x = target_x - mid_x
    pos_y = target_y - bottom_y

    # -------------------------
    # Shadow PNG
    # -------------------------
    if shadow_png is not None:

        # Load shadow PNG
        shadow = shadow_png.convert("RGBA")

        # Flip if shoe faces left
        if flip_shadow and direction == "left":
            shadow = shadow.transpose(Image.FLIP_LEFT_RIGHT)

        # Scale shadow
        if shadow_scale != 1.0:
            sw, sh = shadow.size
            shadow = shadow.resize(
                (int(sw * shadow_scale), int(sh * shadow_scale)),
                Image.LANCZOS
            )

        # Rotate shadow
        if shadow_rotation != 0:
            shadow = shadow.rotate(shadow_rotation, expand=True)

        # Shadow placement:
        # Shadow should sit at the bottom of the shoe
        shadow_x = pos_x + shadow_offset[0]
        shadow_y = pos_y + bottom_y + shadow_offset[1]

        canvas.paste(shadow, (shadow_x, shadow_y), shadow)

    # -------------------------
    # Paste shoe
    # -------------------------
    canvas.paste(rotated, (pos_x, pos_y), rotated)

    return canvas
