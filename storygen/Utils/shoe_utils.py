from PIL import Image, ImageFilter
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
    shadow_opacity=1.0,
    shadow_offset=(0, 0),
    toe_offset=(0, 0),
    flip_shadow_for_left=True,

    # Blend mode
    shadow_blend_mode="multiply",   # "darken" or "multiply"
    shadow_feather=25,              # blur radius for mask edges
):
    W, H = canvas.size

    # --- Resize shoe ---
    sw, sh = img.size
    ratio = min(max_size[0] / sw, max_size[1] / sh)
    shoe = img.resize((int(sw * ratio), int(sh * ratio)), Image.LANCZOS)

    # --- Detect direction ---
    direction = detect_shoe_direction(shoe)
    final_angle = angle_left if direction == "left" else angle_right

    # --- Rotate shoe ---
    rotated = shoe.rotate(final_angle, expand=True)
    arr = np.array(rotated)
    ys, xs = np.where(arr[:, :, 3] > 0)

    # Toe / heel / bottom
    toe_x = xs.min() if direction == "left" else xs.max()
    heel_x = xs.max() if direction == "left" else xs.min()
    bottom_y = ys.max()
    mid_x = int((toe_x + heel_x) / 2)

    # --- Position shoe ---
    if pos is None:
        target_x = W // 2 if center_x else 0
        target_y = H // 2 if center_y else H // 2
    else:
        target_x, target_y = pos
        if center_x: target_x = W // 2
        if center_y: target_y = H // 2

    pos_x = target_x - mid_x
    pos_y = target_y - bottom_y

    # -------------------------
    # Shadow PNG → feathered mask
    # -------------------------
    if shadow_png is not None:
        shadow = shadow_png.convert("RGBA")

        if flip_shadow_for_left and direction == "left":
            shadow = shadow.transpose(Image.FLIP_LEFT_RIGHT)

        if shadow_scale != 1.0:
            sw2, sh2 = shadow.size
            shadow = shadow.resize(
                (int(sw2 * shadow_scale), int(sh2 * shadow_scale)),
                Image.LANCZOS
            )

        if shadow_rotation != 0:
            shadow = shadow.rotate(shadow_rotation, expand=True)

        # Convert to grayscale
        gray = shadow.convert("L")

        # Invert → dark areas become strong mask
        mask = Image.eval(gray, lambda p: 255 - p)

        # Feather edges (THIS FIXES THE SHARP BORDER)
        mask = mask.filter(ImageFilter.GaussianBlur(shadow_feather))

        # Apply opacity
        mask_arr = np.array(mask).astype(np.float32) / 255.0
        mask_arr *= shadow_opacity

        # Shadow position
        sw2, sh2 = shadow.size
        if direction == "right":
            shadow_x = pos_x + toe_x - sw2 + toe_offset[0]
        else:
            shadow_x = pos_x + toe_x + toe_offset[0]

        shadow_y = pos_y + bottom_y + toe_offset[1]
        shadow_x += shadow_offset[0]
        shadow_y += shadow_offset[1]

        # Extract region from canvas
        region = canvas.crop((shadow_x, shadow_y, shadow_x + sw2, shadow_y + sh2)).convert("RGBA")
        region_arr = np.array(region).astype(np.float32)

        # Expand mask to 3 channels
        m = mask_arr[:, :, None]

        # --- Blend modes ---
        if shadow_blend_mode == "darken":
            # Darken only where mask is strong
            darkened = region_arr[:, :, :3] * (1.0 - m)
            blended_rgb = np.minimum(region_arr[:, :, :3], darkened)
        else:  # multiply
            factor = 1.0 - m
            blended_rgb = region_arr[:, :, :3] * factor

        blended_rgb = blended_rgb.clip(0, 255).astype(np.uint8)
        blended_alpha = region_arr[:, :, 3].astype(np.uint8)

        out = np.dstack([blended_rgb, blended_alpha])
        out_img = Image.fromarray(out, mode="RGBA")

        canvas.paste(out_img, (shadow_x, shadow_y), out_img)

    # --- Shoe on top ---
    canvas.paste(rotated, (pos_x, pos_y), rotated)

    return canvas
