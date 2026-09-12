from PIL import Image, ImageDraw, ImageFont
import cairo
import random
import numpy as np

from storygen.utils import (
    lighten_color,
    darken_color,
    draw_text,
    load_font,
    place_shoe2,
    remove_background,
    adjust_saturation,
    extract_colors,
    add_brand_logo2,
    detect_shoe_direction,
    draw_sizes_box3,
    to_english_digits,
    add_user_logo,
    protect_color)

def draw_brand_vertical(
        canvas,
        text,
        font_path="Future Friends Italic.ttf",
        top_y=200,
        bottom_y=1700,
        fill=(0,0,0),
        rotation=90,
        padding=40,
        safety_margin=20
    ):
        canvas_w, canvas_h = canvas.size
        target_height = bottom_y - top_y - 2*safety_margin  # strict band, minus margin
    
        best_img = None
    
        for size in range(800, 10, -5):
            font = load_font(font_path, size)
    
            bbox = font.getbbox(text)
            w = bbox[2] - bbox[0]
            h = bbox[3] - bbox[1]
    
            temp = Image.new("RGBA", (w + padding*2, h + padding*2), (0,0,0,0))
            td = ImageDraw.Draw(temp)
            td.text((padding, padding), text, fill=fill, font=font)
    
            rotated = temp.rotate(rotation, expand=True)
    
            arr = np.array(rotated)
            alpha = arr[:,:,3]
            ys, xs = np.where(alpha > 0)
            if len(xs) == 0 or len(ys) == 0:
                continue
    
            min_x, max_x = xs.min(), xs.max()
            min_y, max_y = ys.min(), ys.max()
    
            content = rotated.crop((min_x, min_y, max_x+1, max_y+1))
            content_w, content_h = content.size
    
            # strict fit check with safety margin
            if content_h + 2*safety_margin <= (bottom_y - top_y):
                best_img = content
                break
    
        if best_img is None:
            return
    
        final_w, final_h = best_img.size
    
        # center horizontally
        x = (canvas_w - final_w) // 2
    
        # center vertically inside band with safety margin
        band_h = bottom_y - top_y
        y = top_y + (band_h - final_h) // 2
    
        # clamp to ensure no overflow
        y = max(top_y + safety_margin, min(y, bottom_y - final_h - safety_margin))
    
        canvas.paste(best_img, (x, y), best_img)
        
def draw_sizes_grid(
    canvas,
    sizes,
    pos=(None, None),

    # Colors for alternating rows
    box_colors=((220,220,220), (180,180,180)),

    box_radius=12,

    # Grid limits
    max_rows=3,
    max_cols=4,
    max_sizes=12,   # NEW: hard limit

    # Auto shrink settings
    shrink_threshold=12,
    box_size=(160, 80),
    font_path="Segoe.UI.Semibold_p30download.com.ttf",
    font_size=40,

    # Text colors auto-detected
    dark_threshold=140,   # avg RGB < this → use white text
    light_threshold=200,  # avg RGB > this → use black text

    # Padding inside each box
    padding_left=10,
    padding_right=10,
    padding_top=5,
    padding_bottom=5,

    # Spacing between boxes
    h_spacing=20,
    v_spacing=20
):
    if not sizes:
        return

    # Limit sizes
    sizes = sizes[:max_sizes]

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
    rows = min(max_rows, n)
    cols = min(max_cols, (n + rows - 1) // rows)

    pos_x, pos_y = pos
    box_w, box_h = box_size

    # Total grid size including spacing
    grid_w = cols * box_w + (cols - 1) * h_spacing
    grid_h = rows * box_h + (rows - 1) * v_spacing

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

    # --- SMART COLOR CYCLING ---
    # Row-based alternating colors, but columns continue pattern
    # Example:
    # col0 rows: A B A
    # col1 rows: B A B
    # col2 rows: A B A
    # etc.
    def get_box_color(col, row):
        # shift pattern based on column index
        idx = (row + col) % len(box_colors)
        return box_colors[idx]

    # --- SMART TEXT COLOR ---
    def auto_text_color(rgb):
        avg = sum(rgb) / 3
        if avg < dark_threshold:
            return (255, 255, 255)  # white
        if avg > light_threshold:
            return (0, 0, 0)        # black
        # mid-range → choose best contrast
        return (255, 255, 255) if avg < 160 else (0, 0, 0)

    # Draw boxes
    idx = 0
    for r in range(rows):
        for c in range(cols):
            if idx >= n:
                break

            s = sizes[idx]

            bx1 = x0 + c * (box_w + h_spacing)
            by1 = y0 + r * (box_h + v_spacing)
            bx2 = bx1 + box_w
            by2 = by1 + box_h

            color = get_box_color(c, r)
            draw.rounded_rectangle([bx1, by1, bx2, by2], radius=box_radius, fill=color)

            # Measure text
            b = font.getbbox(s)
            tw = b[2] - b[0]
            th = b[3] - b[1]

            # Center text inside box with padding
            tx = bx1 + (box_w - tw) // 2
            ty = by1 + (box_h - th) // 2

            tx = max(bx1 + padding_left, tx)
            ty = max(by1 + padding_top, ty)

            # Auto text color
            tcolor = auto_text_color(color)

            draw.text((tx, ty), s, fill=tcolor, font=font)

            idx += 1




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
        font_path_eng="calibrib.ttf",
        font_size_eng=69,
        font_path_per="A Mitra 04.ttf",
        font_size_per=60,
        pos=(None, 225),
        rotation=0,
        fill=(0, 0, 0),
        padding_top=3,
        padding_bottom=5)

    # -------------------------
    # Shop Name
    # -------------------------
    draw_text(
        canvas,
        text=shop_name_en,
        font_path_eng="calibrili.ttf",
        font_size_eng=50,
        font_path_per="A Mitra 04.ttf",
        font_size_per=60,
        pos=(None, 320),
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
        opacity=255,
        pos=(None, 60),
        color=lighten,
        max_size=(260, 200))

    
    # -------------------------
    #  User logo 
    # -------------------------
    add_user_logo(
        canvas,
        logo_path=logo,
        pos=(None, 380),
        max_size=(110, 110),
        center_x=True,
        opacity=150)
    
    # -------------------------
    # Brand Name
    # -------------------------
    draw_brand_vertical(
        canvas,
        text=brand.upper(),
        font_path="Future Friends Italic.ttf",
        top_y=430,
        bottom_y=1600,
        fill=protect_co,
        rotation=90,
        padding=130,
        safety_margin=20
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

    first = adjust_saturation(darken_color(saturated_color, 0.35), 1.25)
    fourth = adjust_saturation(lighten_color(saturated_color, 0.55), 1.1)

    draw_sizes_grid(
        canvas,
        sizes,
        pos=(None, 1780),
        box_colors=(first, fourth),  
        box_radius=12,
    
        # Grid limits
        max_rows=3,
        max_cols=4,
        max_sizes=12,

        font_path="Segoe.UI.Semibold_p30download.com.ttf",
        font_size=37,
        box_size=(220, 65),
        
        # Text colors auto-detected
        dark_threshold=140,   
        light_threshold=200,
        
        # Padding inside each box
        padding_left=0,
        padding_right=0,
        padding_top=0,
        padding_bottom=5,
        h_spacing=35,
        v_spacing=10)

    # -------------------------
    # Footer Text
    # -------------------------
    rand_num = random.randint(100, 999)
    footer_main = "استعلام قیمت عدد"
    footer_number = f"({to_english_digits(str(rand_num))})"
    
    # Colors
    main_color_footer = (0, 0, 0)
    number_color_footer = (255, 140, 0)
    
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
    
    final_pos = (275, 1620)   
    
    canvas.paste(temp_img, final_pos, temp_img)



    return canvas
