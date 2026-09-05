from PIL import Image, ImageDraw, ImageFont
import cairo
import random
import numpy as np

from storygen.utils import (
    lighten_color,
    draw_text,
    load_font,
    place_shoe2,
    remove_background,
    extract_colors,
    add_brand_logo,
    detect_shoe_direction,
    draw_sizes_box3,
    to_english_digits,
    add_user_logo)

def draw_scaled_text2(
    draw,
    text,
    font_path,
    max_font_size,
    max_width,
    start_pos,
    fill,
    rotation=0  
):
    canvas_w, canvas_h = draw.im.size

    # Try from max size down to 10
    for size in range(max_font_size, 10, -2):
        font = load_font(font_path, size)

        # Measure text
        bbox = font.getbbox(text)
        w = bbox[2] - bbox[0]
        h = bbox[3] - bbox[1]

        # Fit check (only width matters)
        if w <= max_width:

            # Smart centering if None
            x = start_pos[0] if start_pos[0] is not None else (canvas_w - w) // 2
            y = start_pos[1] if start_pos[1] is not None else (canvas_h - h) // 2

            # Render text to temporary image
            temp = Image.new("RGBA", (w, h), (0,0,0,0))
            td = ImageDraw.Draw(temp)
            td.text((0, 0), text, fill=fill, font=font)

            # Rotate safely
            rotated = temp.rotate(rotation, expand=True)

            # Draw rotated image
            draw.bitmap((x, y), rotated)

            return h, w, font

    return 0, 0, None



def template_1g(photo_1, model_name, sizes, shop_name_en, brand, logo):

    W, H = 1080, 1920

    # -------------------------
    # Colors
    # -------------------------
    photo_1_rem = remove_background(photo_1)  
    main_color, second_color, saturated_color = extract_colors(
        photo_1_rem,
        include_saturated=True)

    # Lighten main color → protect from becoming white
    lighten = lighten_color(main_color, 0.65)
    bg = protect_color(lighten, sat_boost=1.5, darken_factor=0.25, threshold=230)
    
    canvas = Image.new("RGB", (W, H), (255,255,255))
    draw = ImageDraw.Draw(canvas)

    # -------------------------
    # Detect direction
    # -------------------------
    shoe_direction = detect_shoe_direction(photo_1_rem)
    is_left = shoe_direction == "left"
    
    # -------------------------
    # Brand Name
    # -------------------------
    brand_text = brand.upper()

    draw_scaled_text2(
        draw,
        text=brand_text,
        font_path="fx-neofara-black-italic.otf",
        max_font_size=550,
        max_width= 1000,
        start_pos=(None, 350),
        fill=bg,
        rotation=90
    )
    
    # -------------------------
    # Model Name
    # -------------------------
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

    # -------------------------
    # Shop Name
    # -------------------------
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
    

    # -------------------------
    # Brand Logo
    # -------------------------
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

    # -------------------------
    #  User logo 
    # -------------------------
    add_user_logo(
        canvas,
        logo_path=logo,
        pos=(100, 190),
        max_size=(180, 180),
        center_x=False,
        opacity=105
    )
    # -------------------------
    # Shoe
    # -------------------------
    place_shoe2(
        canvas, photo_1_rem,
        pos=(None, 1250),  
        max_size=(1000, 600),
        angle_left=23,
        angle_right=-23,
        center_x=True)
    

    # -------------------------
    # Sizes Box
    # -------------------------
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
        min_size_font=25)

        
    # -------------------------
    # Footer Text 
    # -------------------------
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




    return canvas
