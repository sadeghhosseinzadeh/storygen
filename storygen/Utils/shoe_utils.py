from PIL import Image, ImageDraw, ImageFilter
import numpy as np
from storygen.utils import detect_shoe_direction

def place_shoe_1c(
    canvas,
    img,
    shadow_png,
    pos=None,
    max_size=(800, 600),
    angle_left=20,
    angle_right=-20,
    center_x=True,
    center_y=False,

    # Shadow controls
    shadow_scale=1.0,
    shadow_rotation=0,
    shadow_opacity=1.0,        # 0.0–1.0
    shadow_offset=(0, 0),      # global offset (x, y)
    toe_offset=(0, 0),         # fine offset from toe (x, y)
    flip_shadow_for_left=True
):
    """
    Places rotated shoe centered using toe→heel midpoint.
    Detects toe of shoe and aligns shadow PNG edge to toe.
    """

    W, H = canvas.size

    # --- Resize shoe ---
    sw, sh = img.size
    max_w, max_h = max_size
    ratio = min(max_w / sw, max_h / sh)
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
    alpha = arr[:, :, 3]
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
        target_x = W // 2 if center_x else 0
        target_y = H // 2 if center_y else H // 2
    else:
        target_x, target_y = pos
        if center_x:
            target_x = W // 2
        if center_y:
            target_y = H // 2

    # Anchor shoe so toe→heel midpoint aligns to target
    pos_x = target_x - mid_x
    pos_y = target_y - bottom_y

    # -------------------------
    # Shadow PNG
    # -------------------------
    if shadow_png is not None:
        shadow = shadow_png.convert("RGBA")

        # Flip for left-facing shoe
        if flip_shadow_for_left and direction == "left":
            shadow = shadow.transpose(Image.FLIP_LEFT_RIGHT)

        # Scale
        if shadow_scale != 1.0:
            s_w, s_h = shadow.size
            shadow = shadow.resize(
                (int(s_w * shadow_scale), int(s_h * shadow_scale)),
                Image.LANCZOS
            )

        # Rotate
        if shadow_rotation != 0:
            shadow = shadow.rotate(shadow_rotation, expand=True)

        # Opacity
        if shadow_opacity < 1.0:
            s_arr = np.array(shadow)
            s_arr[:, :, 3] = (s_arr[:, :, 3].astype(np.float32) * shadow_opacity).astype(np.uint8)
            shadow = Image.fromarray(s_arr, mode="RGBA")

        s_w, s_h = shadow.size

        # Align shadow edge to toe
        if direction == "right":
            # Right edge of shadow to toe
            shadow_x = pos_x + toe_x - s_w + toe_offset[0]
        else:
            # Left edge of shadow to toe
            shadow_x = pos_x + toe_x + toe_offset[0]

        # Vertical: start from bottom of shoe
        shadow_y = pos_y + bottom_y + toe_offset[1]

        # Apply global offset
        shadow_x += shadow_offset[0]
        shadow_y += shadow_offset[1]

        canvas.paste(shadow, (shadow_x, shadow_y), shadow)

    # -------------------------
    # Paste shoe
    # -------------------------
    canvas.paste(rotated, (pos_x, pos_y), rotated)

    return canvas
