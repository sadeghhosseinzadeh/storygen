from PIL import Image, ImageDraw, ImageFont, ImageFilter
import random
import numpy as np
import colorsys
from pathlib import Path
import storygen

from storygen.utils import (
    lighten_color,
    load_font,
    place_shoe,
    remove_background,
    extract_colors,   
    draw_text,
    draw_scaled_text,
    draw_sizes_box,
    add_brand_logo,
    add_user_logo,
    protect_color
)

def motion_blur(img, radius=25, angle=-30):
    # Rotate → blur → rotate back
    rotated = img.rotate(angle, expand=True)
    blurred = rotated.filter(ImageFilter.GaussianBlur(radius))
    return blurred.rotate(-angle, expand=True)
    

def template_1a(photo_1, model_name, shop_name_en, sizes, brand, logo=None):
    W, H = 1080, 1920

    # --- 1. Remove background ---
    photo_1_rem = remove_background(photo_1)
    blurred_photo_1 = motion_blur(photo_1_rem, radius=25, angle=-30)
    
    # --- 2. Extract colors (safe version) ---
    main_color, second_color, saturated_color = extract_colors(
        photo_1_rem,
        include_saturated=True
    )

    # --- 3. Background color ---
    # Lighten main color → protect from becoming white
    bg = lighten_color(main_color, 0.35)
    #bg = protect_color(lighten)

    canvas = Image.new("RGB", (W, H), bg)
    draw = ImageDraw.Draw(canvas)

    # --- 4. Big brand text (centered) ---
    brand_text = brand.upper()

    draw_scaled_text(
        draw,
        text=brand_text,
        font_path="GILSANUB.TTF",
        max_font_size=300,
        max_width=1000,
        max_height=400,
        start_pos=(None, 200),
        fill=(255, 255, 255),
        allow_multiline=True
    )


    # --- 5. Model name (rotated) ---
    draw_text(
        canvas,
        text=model_name,
        font_path_eng="GILLUBCD.TTF",
        font_size_eng=55,
        font_path_per="A Mitra 04.ttf",
        font_size_per=60,
        pos=(None, 350),
        rotation=22,
        fill=(255, 255, 255)
    )

    # --- 6. Shop name ---
    if shop_name_en and shop_name_en.strip():
        draw_text(
            canvas,
            text=shop_name_en,
            font_path_eng="GILLUBCD.TTF",
            font_size_eng=50,
            font_path_per="A Mitra 04.ttf",
            font_size_per=60,
            pos=(100, 470),
            rotation=0,
            fill=((255, 255, 255)
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

    place_shoe(canvas, blurred_photo_1,
               pos=(1, 220),  
               max_size=(850, 600),
               angle=-25,
               center_x=False)

    place_shoe(canvas, blurred_photo_1,
               pos=(1030, 1800),  
               max_size=(850, 600),
               angle=0,
               center_x=False)
    
    # --- 6.5 Dotted overlay PNG ---

    package_root = Path(storygen.__file__).parent
    overlay_path = package_root / "bg" / "template1a_bg.png"
    
    overlay = Image.open(overlay_path).convert("RGBA").resize((W, H))
    canvas.paste(overlay, (0, 0), overlay)

    # --- 7. Sizes box ---
    draw_sizes_box(
        canvas,
        sizes=sizes,
        pos=(200, 1550),
        show_box=True,
        max_height=None,
        min_height=None,
        title_font_size=55,
        title_color=(220, 0, 0),
        size_font_size=40,
        size_color=(0, 0, 0),
        spacing=5
    )

    # --- 8. Footer text ---
    rand_num = random.randint(100, 999)
    footer_main = "استعلام قیمت عدد"
    footer_number = f"({rand_num})"

    base_x = 500
    base_y = 1700

    font_main = load_font("Homa.ttf", 45)
    font_num = load_font("Homa.ttf", 62)

    draw.text((base_x, base_y), footer_main, fill=(0, 0, 0), font=font_main)

    bbox_main = font_main.getbbox(footer_main)
    main_w = bbox_main[2] - bbox_main[0]

    bbox_num = font_num.getbbox(footer_number)
    num_w = bbox_num[2] - bbox_num[0]

    num_x = base_x + (main_w - num_w) // 2
    num_y = base_y + bbox_main[3] - bbox_main[1] + 10

    draw.text((num_x, num_y), footer_number, fill=(220, 0, 0), font=font_num)

    # --- 9. User logo ---
    add_user_logo(
        canvas,
        logo_path=logo,
        pos=(None, 1300),
        max_size=(180, 180),
        center_x=True
    )

    place_shoe(canvas, photo_1_rem,
               pos=(None, 1360),  
               max_size=(850, 600),
               angle=30,
               center_x=True)

    return canvas
