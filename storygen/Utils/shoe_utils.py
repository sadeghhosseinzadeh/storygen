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
    flip_shadow_for_left=True,
):
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

    # Lowest pixel inside rotated shoe
    bottom_y = ys.max()

    # Midpoint for centering
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

    pos_x = target_x - mid_x
    pos_y = target_y - bottom_y

    # -------------------------
    # Shadow PNG (simple paste + darken blend)
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

        # --- Premultiply alpha + opacity (fix checkerboard) ---
        s_arr = np.array(shadow).astype(np.float32)
        alpha = s_arr[:, :, 3:4] / 255.0
        s_arr[:, :, :3] *= alpha
        s_arr[:, :, 3] *= shadow_opacity
        shadow = Image.fromarray(s_arr.astype(np.uint8), mode="RGBA")

        s_w, s_h = shadow.size

        # --- Horizontal toe alignment (same as your old logic) ---
        if direction == "right":
            shadow_x = pos_x + toe_x - s_w + toe_offset[0]
        else:
            shadow_x = pos_x + toe_x + toe_offset[0]

        # --- PERFECT vertical alignment (lowest point of shoe) ---
        shoe_bottom_canvas_y = pos_y + bottom_y
        shadow_y = shoe_bottom_canvas_y + toe_offset[1]

        # Apply global offset
        shadow_x += shadow_offset[0]
        shadow_y += shadow_offset[1]

        # --- DARKEN blend mode (Photoshop-style) ---
        region = canvas.crop((shadow_x, shadow_y, shadow_x + s_w, shadow_y + s_h)).convert("RGBA")
        region_arr = np.array(region)
        shadow_arr = np.array(shadow)

        blended_rgb = np.minimum(region_arr[:, :, :3], shadow_arr[:, :, :3])
        blended_alpha = shadow_arr[:, :, 3]

        out = np.dstack([blended_rgb, blended_alpha])
        out_img = Image.fromarray(out, mode="RGBA")

        canvas.paste(out_img, (shadow_x, shadow_y), out_img)

    # -------------------------
    # Paste shoe ON TOP
    # -------------------------
    canvas.paste(rotated, (pos_x, pos_y), rotated)

    return canvas
