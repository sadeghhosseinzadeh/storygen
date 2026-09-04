from PIL import Image, ImageDraw, ImageFont, ImageFilter
import random
import numpy as np
import colorsys
from pathlib import Path
import storygen

from storygen.utils import (
    lighten_color,
    load_font,
    remove_background,
    extract_colors,   
    draw_text,
    draw_scaled_text,
    draw_sizes_box3,
    add_brand_logo,
    add_user_logo,
    protect_color,
    detect_shoe_direction,
    place_shoe,
    to_english_digits
)



def motion_blur(img, length=80, angle=0):
    """
    True directional motion blur.
    Creates a streak instead of repeated shoes.
    """

    img = img.convert("RGBA")

    arr = np.array(img).astype(np.float32)

    theta = np.radians(angle)

    dx = np.cos(theta)
    dy = np.sin(theta)

    result = np.zeros_like(arr)

    for i in range(length):

        shift_x = int(round(dx * i))
        shift_y = int(round(dy * i))

        shifted = np.roll(arr, shift=(shift_y, shift_x), axis=(0, 1))

        weight = (length - i) / length

        result += shifted * weight

    result /= np.sum([(length - i) / length for i in range(length)])

    result = np.clip(result, 0, 255).astype(np.uint8)

    return Image.fromarray(result, "RGBA")



def place_shoe2(canvas, img, pos=None, max_size=(800,600),
               angle_left=20, angle_right=-20,
               center_x=True, center_y=False, shadow=True):
    """
    Smart version:
    - Detects shoe direction (left/right)
    - Uses angle_left for left-facing shoes
    - Uses angle_right for right-facing shoes
    """
    W, H = canvas.size

    # --- Resize shoe ---
    sw, sh = img.size
    max_w, max_h = max_size
    ratio = min(max_w/sw, max_h/sh)
    if ratio > 1:
        ratio = min(max_w/sw, max_h/sh)

    new_w, new_h = int(sw * ratio), int(sh * ratio)
    shoe = img.resize((new_w, new_h), Image.LANCZOS)

    # ============================================================
    #  AUTO DIRECTION DETECTION
    # ============================================================
    direction = detect_shoe_direction(shoe)

    if direction == "left":
        final_angle = angle_left
    else:
        final_angle = angle_right

    # ============================================================
    #  MODE 1: OLD BEHAVIOR (final_angle == 0)
    # ============================================================
    if final_angle == 0:
        if pos is None:
            pos_x = (W - new_w) // 2 if center_x else 0
            pos_y = (H - new_h) // 2 if center_y else 0
        else:
            pos_x, pos_y = pos
            if center_x:
                pos_x = (W - new_w) // 2
            if center_y:
                pos_y = (H - new_h) // 2

        if shadow:
            sh_img = shoe.convert("RGBA")
            shadow_data = [(0,0,0,int(px[3]*0.5)) for px in sh_img.getdata()]
            sh_img.putdata(shadow_data)
            sh_img = sh_img.filter(ImageFilter.GaussianBlur(10))
            canvas.paste(sh_img, (pos_x + 5, pos_y + 20), sh_img)

        canvas.paste(shoe, (pos_x, pos_y), shoe)
        return canvas

    # ============================================================
    #  MODE 2: NEW BEHAVIOR (final_angle != 0)
    # ============================================================

    # --- Find bottom-middle pixel ---
    arr = np.array(shoe)
    alpha = arr[:,:,3]

    ys, xs = np.where(alpha > 0)
    bottom_y = ys.max()
    xs_bottom = xs[ys == bottom_y]
    bottom_mid_x = int((xs_bottom.min() + xs_bottom.max()) / 2)

    # --- Determine target position ---
    if pos is None:
        pos_x = (W - new_w) // 2 if center_x else 0
        target_y = (H // 2) if center_y else (H // 2)
    else:
        user_x, target_y = pos
    
        if center_x:
            pos_x = (W - new_w) // 2
        else:
            pos_x = user_x

    
    # --- Initial placement BEFORE rotation ---
    pos_y = target_y - bottom_y

    # --- Rotate AFTER placement ---
    rotated = shoe.rotate(final_angle, expand=True)
    rw, rh = rotated.size

    # Recompute bottom-middle after rotation
    arr2 = np.array(rotated)
    alpha2 = arr2[:,:,3]
    ys2, xs2 = np.where(alpha2 > 0)
    new_bottom_y = ys2.max()
    xs2_bottom = xs2[ys2 == new_bottom_y]
    new_bottom_mid_x = int((xs2_bottom.min() + xs2_bottom.max()) / 2)

    # Re-anchor bottom-middle to target_y
    pos_y = target_y - new_bottom_y

    # Re-center horizontally only when requested
    if center_x:
        pos_x = (W - rw) // 2

    shoe = rotated

    # --- SHADOW ---
    if shadow:
        sh_img = shoe.convert("RGBA")
        shadow_data = [(0,0,0,int(px[3]*0.5)) for px in sh_img.getdata()]
        sh_img.putdata(shadow_data)
        sh_img = sh_img.filter(ImageFilter.GaussianBlur(10))
        canvas.paste(sh_img, (pos_x + 5, pos_y + 20), sh_img)

    # --- Paste shoe ---
    canvas.paste(shoe, (pos_x, pos_y), shoe)

    return canvas



def template_1a(photo_1, model_name, shop_name_en, sizes, brand, logo=None):
    W, H = 1080, 1920

    # --- 1. Remove background ---
    photo_1_rem = remove_background(photo_1)
    blurred_photo_1 = motion_blur(
        photo_1_rem,
        length=70,
        angle=160
    )
    
    blurred_photo_2 = motion_blur(
        photo_1_rem,
        length=70,
        angle=-20
    )
    direction = detect_shoe_direction(photo_1_rem)
    
    # --- 2. Extract colors (safe version) ---
    main_color, second_color, saturated_color = extract_colors(
        photo_1_rem,
        include_saturated=True
    )

    # --- 3. Background color ---
    # Lighten main color → protect from becoming white
    lighten = lighten_color(main_color, 0.65)
    bg = protect_color(lighten, sat_boost=1.5, darken_factor=0.25, threshold=230)

    canvas = Image.new("RGB", (W, H), bg)
    draw = ImageDraw.Draw(canvas)

    # --- 4. Big brand text (centered) ---
    brand_text = brand.upper()

    draw_scaled_text(
        draw,
        text=brand_text,
        font_path="GILSANUB.TTF",
        max_font_size=300,
        max_width= W-200,
        max_height=400,
        start_pos=(None, 550),
        fill=(255, 255, 255),
        allow_multiline=True
    )

    
    # Force top shoe LEFT and bottom shoe RIGHT
    # --------------------------------------------------
    
    # Top shoe (always LEFT)
    blurred_top = blurred_photo_1
    if direction != "left":
        blurred_top = blurred_top.transpose(Image.FLIP_LEFT_RIGHT)
    
    # Bottom shoe (always RIGHT)
    blurred_bottom = blurred_photo_2
    if direction != "right":
        blurred_bottom = blurred_bottom.transpose(Image.FLIP_LEFT_RIGHT)
    
    place_shoe2(
        canvas,
        blurred_top,
        pos=(-400, 270),
        max_size=(850, 600),
        angle_left=-25,
        angle_right=-25,
        center_x=False,
        center_y=False,
        shadow=False)
    
    place_shoe2(
        canvas,
        blurred_bottom,
        pos=(730, 2000),
        max_size=(850, 600),
        angle_left=-15,
        angle_right=-15,
        center_x=False,
        center_y=False,
        shadow=False)

        # --- 9. User logo ---
    add_user_logo(
        canvas,
        logo_path=logo,
        pos=(100, 190),
        max_size=(180, 180),
        center_x=False,
        opacity=105
    )
    
    # --- 6.5 Dotted overlay PNG ---

    package_root = Path(storygen.__file__).parent
    overlay_path = package_root / "bg" / "template1a_bg.png"
    
    overlay = Image.open(overlay_path).convert("RGBA").resize((W, H))
    canvas.paste(overlay, (0, 0), overlay)

    
    add_brand_logo(
                canvas,
                brand,
                mode=0,
                variant=2,
                opacity=255,
                pos=(800, 190),
                color=saturated_color,
                max_size=(200, 200)
            )
    
    # --- 7. Sizes box ---
    if direction == "left":
        sizes_pos = (800, 1500)   # shoe points left → box on right
    else:
        sizes_pos = (300, 1500)   # shoe points right → box on left
    
    draw_sizes_box3(
        canvas,
        sizes=sizes,
        pos=sizes_pos,
        show_box=True,
        box_radius=18,
        max_height=700,
        min_height=None,
        title_font_size=50,
        title_color=(0, 0, 0),
        size_font_size=40,
        size_color=(0, 0, 0),

        padding_left=40,
        padding_right=40,
        padding_top=10,
        padding_bottom=20,
        gap_title_to_sizes=25,  # space under "Size:" 
        spacing=10,              # space between sizes
        max_sizes_before_shrink=8,
        min_size_font=25
    )

    

    # --- 8. Footer text ---
    rand_num = random.randint(100, 999)
    footer_main = "استعلام قیمت عدد"
    footer_number = f"({to_english_digits(str(rand_num))})"
    
    base_x = 400
    base_y = 1730
    
    font_main = load_font("Homa.ttf", 45)          # Persian font
    font_num  = load_font("Segoe.UI.Bold_p30download.com.ttf", 55)      # English font
    
    draw.text((base_x, base_y), footer_main, fill=(0, 0, 0), font=font_main)
    
    bbox_main = font_main.getbbox(footer_main)
    main_w = bbox_main[2] - bbox_main[0]
    
    bbox_num = font_num.getbbox(footer_number)
    num_w = bbox_num[2] - bbox_num[0]
    
    num_x = base_x + (main_w - num_w) // 2
    num_y = base_y + bbox_main[3] - bbox_main[1] + 10
    
    draw.text((num_x, num_y), footer_number, fill=(0,0,0), font=font_num)



    place_shoe2(canvas, photo_1_rem,
               pos=(None, 1250),  
               max_size=(1000, 600),
               angle_left=23,
               angle_right=-23,
               center_x=True)

    
    # --- 6. Shop name ---
    if shop_name_en and shop_name_en.strip():
        font_eng = load_font("GILLUBCD.TTF", 60)
        bbox = font_eng.getbbox(shop_name_en)
        text_w = bbox[2] - bbox[0]
        text_h = bbox[3] - bbox[1]
    
        # Fixed anchor logic
        if direction == "left":
            # left side → keep 100px margin from left edge
            text_x = 100
        else:
            # right side → keep 100px margin from right edge
            text_x = W - text_w - 100
    
        text_y = 1465
    
        draw.text((text_x, text_y), shop_name_en, fill=(255, 255, 255), font=font_eng)
    

    # --- 5. Model name  ---
    draw_text(
        canvas,
        text=model_name,
        font_path_eng="GILLUBCD.TTF",
        font_size_eng=75,
        font_path_per="A Mitra 04.ttf",
        font_size_per=60,
        pos=(100, 470),
        rotation=0,
        fill=(255, 255, 255),
        padding_top=3,
        padding_bottom=5
    )


    return canvas
