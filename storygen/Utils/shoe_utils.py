from PIL import Image, ImageFilter, ImageDraw
import numpy as np
from storygen.utils import detect_shoe_direction

def place_shoe_1c(canvas, img, pos=None, max_size=(800,600),
                  angle_left=20, angle_right=-20,
                  center_x=True, center_y=False,
                  shadow=True, shadow_offset=(0, 40), shadow_blur=35):
    """
    Shoe placement for template 1c:
    - Centers AFTER rotation using toe→heel midpoint
    - Shadow is a flat horizontal ground shadow under the sole
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

    # Toe & heel detection (for length)
    if direction == "left":
        toe_x = xs.min(); heel_x = xs.max()
    else:
        toe_x = xs.max(); heel_x = xs.min()

    # Bottom of shoe (sole line)
    bottom_y = ys.max()

    # Midpoint between toe & heel (for centering)
    mid_x = int((toe_x + heel_x) / 2)

    # --- Target position ---
    if pos is None:
        target_x = W//2 if center_x else 0
        target_y = H//2 if center_y else H//2
    else:
        target_x, target_y = pos
        if center_x: target_x = W//2
        if center_y: target_y = H//2

    # Anchor shoe so toe→heel midpoint aligns to target
    pos_x = target_x - mid_x
    pos_y = target_y - bottom_y  # bottom of shoe sits at target_y

    # --- Shadow ---
    if shadow:
        shadow_layer = Image.new("RGBA", (rw, rh), (0,0,0,0))
        shadow_draw = ImageDraw.Draw(shadow_layer)

        # Shadow length: slightly wider than toe→heel
        shadow_left  = min(toe_x, heel_x) - 40
        shadow_right = max(toe_x, heel_x) + 40

        # Shadow vertical position: just below sole
        shadow_center_y = bottom_y + 10

        # Shadow thickness
        shadow_height = 35

        # Draw flat horizontal ellipse (ground shadow)
        shadow_draw.ellipse(
            [shadow_left,
             shadow_center_y - shadow_height//2,
             shadow_right,
             shadow_center_y + shadow_height//2],
            fill=(0,0,0,150)
        )

        shadow_layer = shadow_layer.filter(ImageFilter.GaussianBlur(shadow_blur))

        # Paste shadow under shoe, with optional offset
        canvas.paste(
            shadow_layer,
            (pos_x + shadow_offset[0], pos_y + shadow_offset[1]),
            shadow_layer
        )

    # --- Paste shoe ---
    canvas.paste(rotated, (pos_x, pos_y), rotated)

    return canvas
