from PIL import Image
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
    shadow_blend_mode="multiply",  # "darken" or "multiply"
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

    if direction == "left":
        toe_x = xs.min()
        heel_x = xs.max()
    else:
        toe_x = xs.max()
        heel_x = xs.min()

    bottom_y = ys.max()
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
    # Shadow PNG
    # -------------------------
    if shadow_png is not None:
        shadow = shadow_png.convert("RGBA")

        if flip_shadow_for_left and direction == "left":
            shadow = shadow.transpose(Image.FLIP_LEFT_RIGHT)

        if shadow_scale != 1.0:
            s_w, s_h = shadow.size
            shadow = shadow.resize(
                (int(s_w * shadow_scale), int(s_h * shadow_scale)),
                Image.LANCZOS
            )

        if shadow_rotation != 0:
            shadow = shadow.rotate(shadow_rotation, expand=True)

        s_arr = np.array(shadow).astype(np.float32)
        s_w, s_h = shadow.size

        # Grayscale shadow (no color tint)
        gray = s_arr[:, :, :3].mean(axis=2)  # 0–255
        gray_norm = gray / 255.0            # 0–1

        # Alpha from darkness: white bg -> 0, dark -> 1
        alpha_mask = (1.0 - gray_norm) * shadow_opacity  # 0–1

        # Horizontal toe alignment
        if direction == "right":
            shadow_x = pos_x + toe_x - s_w + toe_offset[0]
        else:
            shadow_x = pos_x + toe_x + toe_offset[0]

        # Vertical alignment (lowest point)
        shoe_bottom_canvas_y = pos_y + bottom_y
        shadow_y = shoe_bottom_canvas_y + toe_offset[1]

        shadow_x += shadow_offset[0]
        shadow_y += shadow_offset[1]

        region = canvas.crop((shadow_x, shadow_y, shadow_x + s_w, shadow_y + s_h)).convert("RGBA")
        region_arr = np.array(region).astype(np.float32)

        # Expand alpha_mask to (h, w, 1)
        a = alpha_mask[:, :, None]

        if shadow_blend_mode == "darken":
            # Darken: result = min(bg, bg * (1 - a))
            darkened = region_arr[:, :, :3] * (1.0 - a)
            blended_rgb = np.minimum(region_arr[:, :, :3], darkened)
        else:  # "multiply" (Photoshop-style on white bg)
            # Multiply: white (gray_norm=1) -> no change, dark -> darken
            factor = 1.0 - a  # 1 for white, <1 for dark
            blended_rgb = region_arr[:, :, :3] * factor

        blended_rgb = blended_rgb.clip(0, 255).astype(np.uint8)
        blended_alpha = region_arr[:, :, 3].astype(np.uint8)

        out = np.dstack([blended_rgb, blended_alpha])
        out_img = Image.fromarray(out, mode="RGBA")

        canvas.paste(out_img, (shadow_x, shadow_y), out_img)

    # --- Paste shoe on top ---
    canvas.paste(rotated, (pos_x, pos_y), rotated)

    return canvas
