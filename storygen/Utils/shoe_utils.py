from PIL import Image, ImageFilter, ImageDraw
import numpy as np
from storygen.utils import detect_shoe_direction

def place_shoe_1c(canvas, img, pos=None, max_size=(800,600),
               angle_left=20, angle_right=-20,
               center_x=True, center_y=False,
               shadow=True, shadow_offset=(80, 40), shadow_blur=35):
    """
    Perfect centering + toe→heel shadow:
    - Centers AFTER rotation using toe→heel midpoint
    - Shadow sits directly under the shoe
    - Shadow is wider at toe, narrower at heel, fading naturally
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
        toe_x = xs.min(); heel_x = xs.max()
    else:
        toe_x = xs.max(); heel_x = xs.min()

    toe_y = int(ys[xs == toe_x].mean())
    heel_y = int(ys[xs == heel_x].mean())

    # Midpoint between toe & heel
    mid_x = int((toe_x + heel_x) / 2)
    mid_y = int((toe_y + heel_y) / 2)

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
    pos_y = target_y - mid_y

    # --- Shadow ---
    if shadow:
        shadow_layer = Image.new("RGBA", (rw, rh), (0,0,0,0))
        shadow_draw = ImageDraw.Draw(shadow_layer)

        # Shadow width: toe wider, heel narrower
        toe_width  = 60
        heel_width = 25

        # Draw toe shadow (wide)
        shadow_draw.ellipse(
            [toe_x - toe_width, toe_y - 10,
             toe_x + toe_width, toe_y + 10],
            fill=(0,0,0,120)
        )

        # Draw heel shadow (narrow)
        shadow_draw.ellipse(
            [heel_x - heel_width, heel_y - 8,
             heel_x + heel_width, heel_y + 8],
            fill=(0,0,0,100)
        )

        # Connect toe→heel with a fading band
        shadow_draw.rectangle(
            [min(toe_x, heel_x), mid_y - 8,
             max(toe_x, heel_x), mid_y + 8],
            fill=(0,0,0,90)
        )

        shadow_layer = shadow_layer.filter(ImageFilter.GaussianBlur(shadow_blur))

        # Paste shadow directly under shoe
        canvas.paste(
            shadow_layer,
            (pos_x + shadow_offset[0], pos_y + shadow_offset[1]),
            shadow_layer
        )

    # --- Paste shoe ---
    canvas.paste(rotated, (pos_x, pos_y), rotated)

    return canvas
