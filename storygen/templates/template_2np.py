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
    adjusted_color = adjust_saturation(main_color, 0.25)
    # --- 3. Brand logo overlay ---
    add_brand_logo(canvas, brand, mode=0, variant=2, opacity=255, pos=(80, 675), color=adjusted_color, max_size=(200,200))

    # --- 4. Shoe photos ---
    place_shoe(canvas, photo_1_rem, pos=(320,530), max_size=(750,500), angle=0, center_x=False)
    place_shoe(canvas, photo_2_rem, pos=(80,1110), max_size=(630,450), angle=0, center_x=False)

    # --- 5. Model and BRAND name ---
    #  Big brand name text with limit 
    brand_text = brand.upper()
    
    # Start with a base font size
    font_size = 300
    font_big = load_font("Lava Arabic v1.00.ttf", font_size)
    # Measure width
    bbox = font_big.getbbox(brand_text)
    brand_w = bbox[2] - bbox[0]
     # Define max allowed width (e.g. 900 pixels)
    max_width = 650   
    # Reduce font size until it fits
    while brand_w > max_width and font_size > 50:  
        font_size -= 10
        font_big = load_font("Lava Arabic v1.00.ttf", font_size)
        bbox = font_big.getbbox(brand_text)
        brand_w = bbox[2] - bbox[0]
    # Center and draw

    draw.text((70, 240), brand_text, fill=second_color, font=font_big)
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
    draw_sizes_box(
        canvas,
        sizes=sizes,
        pos=(900, 1580),            
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
