
from PIL import Image, ImageDraw, ImageFont, ImageFilter
import random
import numpy as np
import colorsys
from pathlib import Path
import storygen

from storygen.utils import (
    lighten_color,
    darken_color,
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
    place_shoe2,
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



def template_1d(photo_1, model_name, shop_name_en, sizes, brand, logo=None):
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

    second = lighten_color(saturated_color, 0.45)
    third = darken_color(saturated_color, 0.20)

    canvas = Image.new("RGB", (W, H), bg)
    draw = ImageDraw.Draw(canvas)


    # ---  overlay PNG ---

    package_root = Path(storygen.__file__).parent
    overlay_path = package_root / "bg" / "template1e_bg.png"
    
    overlay = Image.open(overlay_path).convert("RGBA").resize((W, H))
    canvas.paste(overlay, (0, 0), overlay)

  
    draw_circle(
        canvas,
        diameter=180,
        pos=(big_pos_x, big_pos_y),
        color=third,
        shadow_color=(0,0,0),
        shadow_intensity=0.45,
        shadow_friction=0.30,
        light_dir=shadow_vec
        )
  
    # -------------------------
    # Model Name
    # -------------------------
    model_text = model_name.upper()
    
    draw_text(
        canvas,
        text=model_text,
        font_path_eng="calibrib.ttf",
        font_size_eng=68,
        font_path_per="A Mitra 04.ttf",
        font_size_per=60,
        pos=(None, 240),
        rotation=0,
        fill=(0, 0, 0),
        padding_top=3,
        padding_bottom=5)

    
    # -------------------------
    # Brand Logo
    # -------------------------
    add_brand_logo2(
        canvas,
        brand,
        mode=0,
        variant=1,
        opacity=245,
        pos=(None, 65),
        color=lighten,
        max_size=(260, 152))

    # --- 4. Big brand text (centered) ---
    brand_text = brand.upper()

    draw_scaled_text(
        draw,
        text=brand_text,
        font_path="Future Friends.ttf",
        max_font_size=440,
        max_width= W-200,
        max_height=400,
        start_pos=(None, 350),
        fill=second,
        allow_multiline=True,
        align="center",         
        opacity=4.0
    )
      draw_scaled_text(
        draw,
        text=brand_text,
        font_path="Future Friends.ttf",
        max_font_size=440,
        max_width= W-200,
        max_height=300,
        start_pos=(None, 550),
        fill=second,
        allow_multiline=True,
        align="center",         
        opacity=1.0
    )
    draw_scaled_text(
        draw,
        text=brand_text,
        font_path="Future Friends.ttf",
        max_font_size=440,
        max_width= W-200,
        max_height=400,
        start_pos=(None, 600),
        fill=second,
        allow_multiline=True,
        align="center",         
        opacity=4.0
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
        pos=(250, 800),
        max_size=(110, 110),
        center_x=False,
        opacity=190
    )
    
    
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
    
    # --- 7. Sizes box --
    
    draw_sizes_box3(
        canvas,
        sizes=sizes,
        pos=(700,1500),
        show_box=False,
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

    
    draw_trapezoid(
        ctx,
        x_left=W-25,
        y_top=0,
        x_right=W,
        y_top_right=0,
        y_bottom_left=H,
        y_bottom_right=H,
        color=normalize_color(third),
        radius=0
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

    # -------------------------
    # Shop Name
    # -------------------------
    draw_text(
        canvas,
        text=shop_name_en,
        font_path_eng="calibrili.ttf",
        font_size_eng=47,
        font_path_per="A Mitra 04.ttf",
        font_size_per=60,
        pos=(250, 850),
        rotation=0,
        fill=(0, 0, 0),
        padding_top=3,
        padding_bottom=5)
    
    
    # -------------------------
    #  User logo 
    # -------------------------
    add_user_logo(
        canvas,
        logo_path=logo,
        pos=(250, 800),
        max_size=(110, 110),
        center_x=True,
        opacity=200)

    return canvas
