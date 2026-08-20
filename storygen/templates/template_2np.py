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
    draw_trapezoid, add_user_logo, draw_text, draw_sizes_box
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
    darken_co = darken_color(main_color, 0.55)
    # --- 3. Brand logo overlay ---
    add_brand_logo(canvas, brand, mode=0, variant=2, opacity=255, pos=(100, 635), color=(0,0,0), max_size=(200,200))

    # --- 4. Shoe photos ---
    place_shoe(canvas, photo_1_rem, pos=(320,530), max_size=(750,500), angle=0, center_x=False)
    place_shoe(canvas, photo_2_rem, pos=(80,1110), max_size=(630,450), angle=0, center_x=False)

    # --- 5. Model and BRAND name ---
    #  Big brand name text with limit 
    brand_text = brand.upper()
    
    draw_scaled_text(
        draw,
        text=brand_text,
        font_path="Lava Arabic v1.00.ttf",
        max_font_size=230,
        max_width=400,
        max_height=200,
        start_pos=(70, 220),
        fill=darken_co
    )
    # --- B. Subtext (top-right) ---
    draw_scaled_text(
        draw,
        text=model_name,
        font_path="Lava Arabic v1.00.ttf",
        max_font_size=150,
        max_width=600,
        max_height=200,
        start_pos=(450, 280),
        fill=darken_co
    )

    # --- 6. Shop name ---
    if shop_name_en and shop_name_en.strip():
        draw_text(canvas,
                   text=shop_name_en,
                   font_path_eng="Segoe.UI.Semibold_p30download.com.ttf",
                   font_size_eng=55,
                   font_path_per="A Mitra 04.ttf",
                   font_size_per=60,
                   pos=(70, 470),
                   rotation=0,
                   fill=(0,0,0))



    # --- 7. Sizes box ---
    draw_sizes_box(
        canvas,
        sizes=sizes,
        pos=(850, 1580),            
        show_box=False,
        max_height=None,
        min_height=None,
        title_font_size=60,
        title_color=(220,0,0),
        size_font_size=45,
        size_color=(0,0,0),
        spacing=15 )


    # --- 8. Footer text ---
    rand_num = random.randint(100, 999)

    footer_main = "استعلام قیمت عدد"
    footer_number = f"({rand_num})"

    # Base position
    base_x = 230
    base_y = 1580
    
    # Fonts
    font_main = load_font("Homa.ttf", 45)
    font_num = load_font("Homa.ttf", 62)

    
    # --- Draw main Persian text ---
    draw.text((base_x, base_y), footer_main, fill=(0,0,0), font=font_main)
    
    # Measure main text width
    bbox_main = font_main.getbbox(footer_main)
    main_w = bbox_main[2] - bbox_main[0]
    
    # Measure number width
    bbox_num = font_num.getbbox(footer_number)
    num_w = bbox_num[2] - bbox_num[0]
    num_h = bbox_num[3] - bbox_num[1]
    
    # --- Center number under the main text ---
    num_x = base_x + (main_w - num_w) // 2
    num_y = base_y + bbox_main[3] - bbox_main[1] + 10   
    
    draw.text((num_x, num_y), footer_number, fill=(220,0,0), font=font_num)
    

    # --- 9. User logo ---
    add_user_logo(canvas,
                  logo_path=logo,
                  pos=(None, 1300),
                  max_size=(180,180),
                  center_x=False)

    return canvas
