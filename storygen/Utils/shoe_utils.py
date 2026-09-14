from PIL import Image, ImageDraw, ImageFilter
import numpy as np
from storygen.utils import detect_shoe_direction

def place_shoe_1c(
    canvas,
    img,
    pos=None,
    max_size=(800,600),
    angle_left=20,
    angle_right=-20,
    center_x=True,
    center_y=False,

    # Shadow tuning
    shadow_front_width=120,     # thickness under toe
    shadow_back_width=40,       # thickness under heel
    shadow_length=0.55,         # % of shoe length that gets shadow
    shadow_darkness=160,        # 0–255
    shadow_softness=45,         # blur radius
    shadow_offset=(0, 10),      # global offset (x,y)
):
    """
    Places rotated shoe centered using toe→heel midpoint.
    Generates a realistic procedural shadow under the shoe.
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

    # Lowest pixel inside rotated shoe
    bottom_y = ys.max()

    # Midpoint for centering
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

    pos_x = target_x - mid_x
    pos_y = target_y - bottom_y

    # --- Paste shoe ---
    canvas.paste(rotated, (pos_x, pos_y), rotated)

    # -------------------------
    # Procedural Shadow
    # -------------------------
    shadow_layer = Image.new("RGBA", (rw, rh), (0,0,0,0))
    draw = ImageDraw.Draw(shadow_layer)

    # Normalize toe/heel ordering
    x_start = min(toe_x, heel_x)
    x_end   = max(toe_x, heel_x)

    # Shadow end (shorter)
    shadow_end_x = int(x_start + (x_end - x_start) * shadow_length)

    # Vertical position: just below sole
    shadow_y = bottom_y + 5

    # --- Toe shadow (wide, strong) ---
    draw.ellipse(
        [
            toe_x - shadow_front_width,
            shadow_y - shadow_front_width//4,
            toe_x + shadow_front_width,
            shadow_y + shadow_front_width//4,
        ],
        fill=(0,0,0,shadow_darkness)
    )

    # --- Mid band ---
    draw.rectangle(
        [
            x_start,
            shadow_y - shadow_back_width//2,
            shadow_end_x,
            shadow_y + shadow_back_width//2,
        ],
        fill=(0,0,0,shadow_darkness - 40)
    )

    # --- Heel shadow (small, faded) ---
    draw.ellipse(
        [
            shadow_end_x - shadow_back_width,
            shadow_y - shadow_back_width//2,
            shadow_end_x + shadow_back_width,
            shadow_y + shadow_back_width//2,
        ],
        fill=(0,0,0,shadow_darkness - 80)
    )

    # Blur for realism
    shadow_layer = shadow_layer.filter(ImageFilter.GaussianBlur(shadow_softness))

    # Paste shadow under shoe
    canvas.paste(
        shadow_layer,
        (pos_x + shadow_offset[0], pos_y + shadow_offset[1]),
        shadow_layer
    )

    return canvas
