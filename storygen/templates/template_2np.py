import cairo
import random
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont, ImageFilter
import io
import cairosvg
import storygen

from storygen.utils import (
    remove_background, extract_colors, lighten_color, darken_color,
    adjust_saturation, load_font, add_brand_logo, place_shoe,
    draw_trapezoid, add_user_logo, draw_text
)

def draw_scaled_text(draw, text, font_path, max_font_size, max_width, max_height, start_pos, fill):
    # Try decreasing font size until it fits
    for size in range(max_font_size, 10, -2):
        font = load_font(font_path, size)
        lines = []
        words = text.split()

        # Try single line first
        bbox = font.getbbox(text)
        w = bbox[2] - bbox[0]
        h = bbox[3] - bbox[1]

        if w <= max_width and h <= max_height:
            lines = [text]
        else:
            # Multi-line fallback
            line = ""
            for word in words:
                test = line + " " + word if line else word
                bbox = font.getbbox(test)
                if (bbox[2]-bbox[0]) <= max_width:
                    line = test
                else:
                    lines.append(line)
                    line = word
            if line:
                lines.append(line)

            total_h = sum([font.getbbox(l)[3] - font.getbbox(l)[1] for l in lines]) + (len(lines)-1)*10
            if total_h > max_height:
                continue  # too tall → try smaller font

        # Draw final lines
        y = start_pos[1]
        for l in lines:
            bbox = font.getbbox(l)
            draw.text((start_pos[0], y), l, fill=fill, font=font)
            y += (bbox[3]-bbox[1]) + 10
        return
        
def template_2np(photo_1, photo_2, model_name, shop_name_en, sizes, brand, logo=None):
    W, H = 1080, 1920

    # --- 1. Background image ---
    # Load a background PNG/JPG from your folder
    package_root = Path(storygen.__file__).parent
    bg_path = package_root / "bg" / "template2np_bg.png"
    
    canvas = Image.open(bg_path).convert("RGBA").resize((W, H))
    draw = ImageDraw.Draw(canvas)
    
    # --- 2. Remove shoe backgrounds ---
    photo_1_rem = remove_background(photo_1)
    photo_2_rem = remove_background(photo_2)
    main_color, second_color = extract_colors(photo_1_rem)
    # --- 3. Brand logo overlay ---
    add_brand_logo(canvas, brand, mode=0, opacity=255, pos=(70, 500), color=main_color, max_size=(180,180))

    # --- 4. Shoe photos ---
    place_shoe(canvas, photo_1_rem, pos=(None,225), max_size=(700,480), angle=0, center_x=True)
    place_shoe(canvas, photo_2_rem, pos=(None,1310), max_size=(600,400), angle=0, center_x=True)

    # --- 5. Model and BRAND name ---
    # BRAND NAME (top-left)
    draw_scaled_text(
        draw,
        text=brand.upper(),
        font_path="Lava%20Arabic%20v1.00.ttf",
        max_font_size=180,
        max_width=450,
        max_height=260,
        start_pos=(50, 40),
        fill=(0,0,0)
    )
    
    # --- B. Subtext (top-right) ---
    draw_scaled_text(
        draw,
        text=model_name,
        font_path="Lava%20Arabic%20v1.00.ttf",
        max_font_size=80,
        max_width=450,
        max_height=200,
        start_pos=(580, 60),
        fill=(0,0,0)
    )

    # --- 6. Shop name ---
    if shop_name_en and shop_name_en.strip():
        draw_text(canvas,
                   text=shop_name_en,
                   font_path_eng="Segoe.UI.Semibold_p30download.com.ttf",
                   font_size_eng=55,
                   font_path_per="A Mitra 04.ttf",
                   font_size_per=60,
                   pos=(None, 845),
                   rotation=0,
                   fill=(0,0,0))



    # --- 7. Sizes box ---
    if sizes:
        if isinstance(sizes, str):
            sizes_list = [s.strip() for s in sizes.split(",") if s.strip()]
        else:
            sizes_list = sizes
    
        # Bigger + red title font
        font_title = load_font("Segoe.UI.Semibold_p30download.com.ttf", 60)
        title_text = "Size:"
        bbox_title = font_title.getbbox(title_text)
        title_w, title_h = bbox_title[2]-bbox_title[0], bbox_title[3]-bbox_title[1]
    
        rect_x1 = 50
        rect_y1 = 900
        rect_w = 400
    
        # Center the red title
        title_x = rect_x1 + (rect_w - title_w)//2
        title_y = rect_y1 + 20
        draw.text((title_x, title_y), title_text, fill=(220,0,0), font=font_title)
    
        # Sizes use your original font + logic
        font_mid = load_font("Segoe.UI.Semibold_p30download.com.ttf", 45)
    
        current_y = title_y + title_h + 30
        for size in sizes_list:
            bbox = font_mid.getbbox(size)
            size_w, size_h = bbox[2]-bbox[0], bbox[3]-bbox[1]
            size_x = rect_x1 + (rect_w - size_w)//2
            draw.text((size_x, current_y), size, fill=(0,0,0), font=font_mid)
            current_y += size_h + 15


    # --- 8. Footer text ---
    rand_num = random.randint(100, 999)

    footer_main = "استعلام قیمت "
    footer_number = str(rand_num)
    
    # Base position
    base_x = 20
    base_y = 1350
    
    # Fonts
    font_main = load_font("Homa.ttf", 40)
    font_num = load_font("Homa.ttf", 70)

    
    # --- Draw main Persian text ---
    draw.text((base_x, base_y), footer_main, fill=(0,0,0), font=font_main)
    
    # Measure main text width
    bbox_main = font_main.getbbox(footer_main)
    main_w = bbox_main[2] - bbox_main[0]
    
    # --- Draw red number next to it ---
    num_x = base_x + main_w + 10
    draw.text((num_x, base_y), footer_number, fill=(220,0,0), font=font_num)
    

    # --- 9. User logo ---
    add_user_logo(canvas,
                  logo_path=logo,
                  pos=(None, 1300),
                  max_size=(180,180),
                  center_x=False)

    return canvas
