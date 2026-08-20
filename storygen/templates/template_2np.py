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
    for size in range(max_font_size, 10, -2):
        font = load_font(font_path, size)
        lines = []
        words = text.split()

        bbox = font.getbbox(text)
        w = bbox[2] - bbox[0]
        h = bbox[3] - bbox[1]

        if w <= max_width and h <= max_height:
            lines = [text]
        else:
            line = ""
            for word in words:
                test = line + " " + word if line else word
                bbox = font.getbbox(test)
                if (bbox[2] - bbox[0]) <= max_width:
                    line = test
                else:
                    lines.append(line)
                    line = word
            if line:
                lines.append(line)

            total_h = sum([font.getbbox(l)[3] - font.getbbox(l)[1] for l in lines]) + (len(lines)-1)*10
            if total_h > max_height:
                continue

        # Draw final lines
        y = start_pos[1]
        total_drawn_h = 0
        max_line_w = 0

        for l in lines:
            bbox = font.getbbox(l)
            lw = bbox[2] - bbox[0]
            lh = bbox[3] - bbox[1]

            draw.text((start_pos[0], y), l, fill=fill, font=font)

            y += lh + 10
            total_drawn_h += lh + 10
            max_line_w = max(max_line_w, lw)

        return total_drawn_h, max_line_w, font

    return 0, 0, None

        
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
    brand_text = brand.upper()
    
    # Draw first text and get its width
    brand_h, brand_w, brand_font = draw_scaled_text(
        draw,
        text=brand_text,
        font_path="Lava Arabic v1.00.ttf",
        max_font_size=230,
        max_width=400,
        max_height=200,
        start_pos=(100, 220),
        fill=darken_co
    )

    # Measure second text height BEFORE drawing
    test_font = load_font("Lava Arabic v1.00.ttf", 150)
    bbox = test_font.getbbox(model_name)
    model_h = bbox[3] - bbox[1]
    
    # Align bottoms
    second_y = 220 + (brand_h - model_h)
    # Now place second text EXACTLY 50px to the right of the first
    second_x = 100 + brand_w + 20

    
    draw_scaled_text(
        draw,
        text=model_name,
        font_path="Lava Arabic v1.00.ttf",
        max_font_size=150,
        max_width=600,
        max_height=200,
        start_pos=(second_x, second_y),
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
