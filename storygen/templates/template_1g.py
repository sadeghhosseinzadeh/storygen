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
    add_brand_logo2,
    detect_shoe_direction,
    draw_sizes_box3,
    to_english_digits,
    add_user_logo,
    protect_color,
    draw_scaled_text)

def draw_sizes_grid(
    canvas,
    sizes,
    pos=(None, None),
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

    # --- NEW POSITION LOGIC ---
    pos_x, pos_y = pos

    box_w, box_h = box_size
    grid_w = cols * box_w
    grid_h = rows * box_h

    # Center if None
    if pos_x is None:
        pos_x = (W - grid_w) // 2
    else:
        pos_x = pos_x - grid_w // 2

    if pos_y is None:
        pos_y = (H - grid_h) // 2
    else:
        pos_y = pos_y - grid_h // 2

    x0 = pos_x
    y0 = pos_y
    # ---------------------------

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



def draw_text_auto(
    canvas,
    text,
    font_path,
    max_width,
    max_font_size=300,
    pos=(None, None),
    fill=(0,0,0),
    rotation=0
):
    W, H = canvas.size

    # Try largest font size downwards
    for size in range(max_font_size, 10, -2):
        font = load_font(font_path, size)

        bbox = font.getbbox(text)
        w = bbox[2] - bbox[0]
        h = bbox[3] - bbox[1]

        if w <= max_width:
            px, py = pos
            print("DEBUG brand text:",
                  "size:", size,
                  "w:", w,
                  "h:", h,
                  "pos:", (px, py),
                  "fill:", fill,
                  "canvas mode:", canvas.mode)

            if px is None:
                px = (W - w) // 2
            if py is None:
                py = (H - h) // 2

            temp = Image.new("RGBA", (w, h), (0,0,0,0))
            td = ImageDraw.Draw(temp)
            td.text((0, 0), text, fill=fill, font=font)

            rotated = temp.rotate(rotation, expand=True)

            # Correct RGBA conversion
            if canvas.mode != "RGBA":
                canvas = canvas.convert("RGBA")

            canvas.paste(rotated, (px, py), rotated)

            return font, w, h

    return None, 0, 0





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
    # Model Name
    # -------------------------
    draw_text(
        canvas,
        text=model_name,
        font_path_eng="Segoe.UI.Bold_p30download.com.ttf",
        font_size_eng=75,
        font_path_per="A Mitra 04.ttf",
        font_size_per=60,
        pos=(None, 225),
        rotation=0,
        fill=(0, 0, 0),
        padding_top=3,
        padding_bottom=5
    )

    # -------------------------
    # Shop Name
    # -------------------------
    draw_text(
        canvas,
        text=shop_name_en,
        font_path_eng="Segoe.UI.Semilight_p30download.com.ttf",
        font_size_eng=60,
        font_path_per="A Mitra 04.ttf",
        font_size_per=60,
        pos=(None, 285),
        rotation=0,
        fill=(0, 0, 0),
        padding_top=3,
        padding_bottom=5
    )
    

    # -------------------------
    # Brand Logo
    # -------------------------
    add_brand_logo2(
        canvas,
        brand,
        mode=0,
        variant=1,
        opacity=255,
        pos=(None, 115),
        color=lighten,
        max_size=(260, 200)
    )

    # -------------------------
    #  User logo 
    # -------------------------
    add_user_logo(
        canvas,
        logo_path=logo,
        pos=(None, 340),
        max_size=(120, 120),
        center_x=True,
        opacity=88
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
    # Brand Name
    # -------------------------
    brand_text = brand.upper()
    draw_scaled_text(
        draw,
        text=brand_text,
        font_path="fx-neofara-black-italic.otf",
        max_font_size=230,
        max_width=400,
        max_height=200,
        start_pos=(100, 220),
        fill=protect_co
    )
    # -------------------------
    # Sizes Box
    # -------------------------
    draw_sizes_grid(
        canvas,
        sizes,
        pos=(None, 1700),
        box_colors=(lighten, protect_co),  
        box_radius=12,
    
        # Grid limits
        max_rows=4,
        max_cols=3,
    
        # Auto shrink settings
        shrink_threshold=12,
        box_size=(260, 85),   # default box width, height
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
    # Footer Text (visual-center aligned, fixed position)
    # -------------------------
    rand_num = random.randint(100, 999)
    footer_main = "استعلام قیمت عدد"
    footer_number = f"({to_english_digits(str(rand_num))})"
    
    # Colors
    main_color_footer = (0, 0, 0)
    number_color_footer = (0, 0, 0)
    
    # Fonts
    font_main = load_font("Homa.ttf", 48)
    font_num  = load_font("Segoe.UI.Bold_p30download.com.ttf", 49)
    
    # --- Render each text separately to measure REAL pixel center ---
    def render_and_center(text, font, color):
        bbox = font.getbbox(text)
        w = bbox[2] - bbox[0]
        h = bbox[3] - bbox[1]
    
        temp = Image.new("RGBA", (w + 20, h + 20), (0,0,0,0))
        d = ImageDraw.Draw(temp)
        d.text((10, 10), text, font=font, fill=color)
    
        alpha = np.array(temp)[:,:,3]
    
        ys, xs = np.where(alpha > 0)
        top = ys.min()
        bottom = ys.max()
    
        visual_h = bottom - top
        center_offset = (visual_h // 2) + top
    
        return temp, w, visual_h, center_offset
    
    # Render both texts
    img_main, main_w, main_h, main_center = render_and_center(footer_main, font_main, main_color_footer)
    img_num,  num_w,  num_h,  num_center  = render_and_center(footer_number, font_num, number_color_footer)
    
    # Unified height
    max_h = max(main_h, num_h)
    
    # Align visual centers
    main_y = (max_h // 2) - main_center
    num_y  = (max_h // 2) - num_center
    
    # RTL order: number first
    gap = 20
    total_w = num_w + gap + main_w
    
    # Final footer image
    temp_img = Image.new("RGBA", (total_w + 40, max_h + 40), (0,0,0,0))
    
    # Paste number
    temp_img.paste(img_num, (10, num_y), img_num)
    
    # Paste Persian text
    temp_img.paste(img_main, (10 + num_w + gap, main_y), img_main)
    
    final_pos = (400, 1730)   # ← your original position
    
    canvas.paste(temp_img, final_pos, temp_img)





    return canvas
