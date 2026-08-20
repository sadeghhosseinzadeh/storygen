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
    add_brand_logo(canvas, brand, mode=0, variant=2, opacity=255, pos=(70, 600), color=main_color, max_size=(180,180))

    # --- 4. Shoe photos ---
    place_shoe(canvas, photo_1_rem, pos=(600,500), max_size=(750,500), angle=0, center_x=False)
    place_shoe(canvas, photo_2_rem, pos=(80,1110), max_size=(650,450), angle=0, center_x=False)

    # --- 5. Model and BRAND name ---
    #  Big brand name text with limit 
    brand_text = brand.upper()
    
    # Start with a base font size
    font_size = 300
    font_big = load_font("Lava%20Arabic%20v1.00.ttf", font_size)
    # Measure width
    bbox = font_big.getbbox(brand_text)
    brand_w = bbox[2] - bbox[0]
     # Define max allowed width (e.g. 900 pixels)
    max_width = 300   
    # Reduce font size until it fits
    while brand_w > max_width and font_size > 50:  
        font_size -= 10
        font_big = load_font("Lava%20Arabic%20v1.00.ttf", font_size)
        bbox = font_big.getbbox(brand_text)
        brand_w = bbox[2] - bbox[0]
    # Center and draw
    brand_x = (W - brand_w) // 2
    draw.text((brand_x, 240), brand_text, fill=second_color, font=font_big)
    '''
    # --- B. Subtext (top-right) ---
    draw_scaled_text(
        draw,
        text=model_name,
        font_path="Lava%20Arabic%20v1.00.ttf",
        max_font_size=200,
        max_width=600,
        max_height=200,
        start_pos=(580, 60),
        fill=(0,0,0)
    )
'''
    # --- 6. Shop name ---
    if shop_name_en and shop_name_en.strip():
        draw_text(canvas,
                   text=shop_name_en,
                   font_path_eng="Segoe.UI.Semibold_p30download.com.ttf",
                   font_size_eng=55,
                   font_path_per="A Mitra 04.ttf",
                   font_size_per=60,
                   pos=(None, 400),
                   rotation=0,
                   fill=main_color)



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
    
        rect_x1 = 600
        rect_y1 = 1500
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
    base_x = 120
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
    num_y = base_y + bbox_main[3] - bbox_main[1] + 10   # 10px below main text
    
    draw.text((num_x, num_y), footer_number, fill=(220,0,0), font=font_num)
    

    # --- 9. User logo ---
    add_user_logo(canvas,
                  logo_path=logo,
                  pos=(None, 1300),
                  max_size=(180,180),
                  center_x=False)

    return canvas
