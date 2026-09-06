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

def draw_sizes_grid(
    canvas,
    sizes,
    pos=None,
    box_colors=((220,220,220), (180,180,180)),  # two alternating colors
    box_radius=12,

    # Grid limits
    max_rows=4,
    max_cols=3,

    # Auto shrink settings
    shrink_threshold=12,
    box_size=(160, 80),   # default box width, height
    font_path="Segoe.UI.Semibold_p30download.com.ttf",
    font_size=40,
    text_color=(0,0,0),

    # Padding inside each box
    padding_left=10,
    padding_right=10,
    padding_top=5,
    padding_bottom=5
):
    if not sizes:
        return

    draw = ImageDraw.Draw(canvas)
    W, H = canvas.size

    # Normalize sizes input
    if isinstance(sizes, str):
        sizes = [s.strip() for s in sizes.split(",") if s.strip()]

    # Auto shrink if too many sizes
    if len(sizes) >= shrink_threshold:
        box_w, box_h = box_size
        box_w = int(box_w * 0.85)
        box_h = int(box_h * 0.85)
        box_size = (box_w, box_h)
        font_size = max(20, font_size - 10)

    font = load_font(font_path, font_size)

    # Determine grid layout
    n = len(sizes)
    if n <= max_rows:
        rows = n
        cols = 1
    else:
        rows = min(max_rows, n)
        cols = (n + rows - 1) // rows
        cols = min(cols, max_cols)

    # Position anchor
    if pos is None:
        center_x = W // 2
        center_y = H // 2
    else:
        center_x, center_y = pos

    box_w, box_h = box_size

    # Total grid size
    grid_w = cols * box_w
    grid_h = rows * box_h

    x0 = center_x - grid_w // 2
    y0 = center_y - grid_h // 2

    # Draw boxes
    idx = 0
    for c in range(cols):
        for r in range(rows):
            if idx >= n:
                break

            s = sizes[idx]
            bx1 = x0 + c * box_w
            by1 = y0 + r * box_h
            bx2 = bx1 + box_w
            by2 = by1 + box_h

            # Alternate colors
            color = box_colors[idx % 2]

            # Draw box
            draw.rounded_rectangle([bx1, by1, bx2, by2], radius=box_radius, fill=color)

            # Measure text
            b = font.getbbox(s)
            tw = b[2] - b[0]
            th = b[3] - b[1]

            # Center text inside box with padding
            tx = bx1 + (box_w - tw) // 2
            ty = by1 + (box_h - th) // 2

            # Apply padding
            tx = max(bx1 + padding_left, tx)
            ty = max(by1 + padding_top, ty)

            draw.text((tx, ty), s, fill=text_color, font=font)

            idx += 1


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
    lighten = lighten_color(saturated_color, 0.90)
    protect_co = protect_color(lighten, sat_boost=1.5, darken_factor=0.25, threshold=230)
    
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
    draw_sizes_grid(
        canvas,
        sizes,
        pos=None,
        box_colors=((220,220,220), (180,180,180)),  # two alternating colors
        box_radius=12,
    
        # Grid limits
        max_rows=4,
        max_cols=3,
    
        # Auto shrink settings
        shrink_threshold=12,
        box_size=(160, 80),   # default box width, height
        font_path="Segoe.UI.Semibold_p30download.com.ttf",
        font_size=40,
        text_color=(0,0,0),
    
        # Padding inside each box
        padding_left=10,
        padding_right=10,
        padding_top=5,
        padding_bottom=5
    )

        
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
