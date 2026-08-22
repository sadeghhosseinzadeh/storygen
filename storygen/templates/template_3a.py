from PIL import Image, ImageDraw, ImageFont
import cairo
import random
from storygen.utils import lighten_color, draw_text, load_font, place_shoe, remove_background, extract_colors, add_brand_logo, protect_color

def template_3a(photo_1, photo_2, photo_3, model_name, sizes, shop_name_en, brand, logo=None):
    W, H = 1080, 1920

    # Background: 15% main color blended with white
    photo_1_rem = remove_background(photo_1)
    main_color, second_color = extract_colors(photo_1_rem)
    bg = lighten_color(main_color, 0.15)
    safe_second_color = protect_color(main_color)
    
    canvas = Image.new("RGB", (W, H), bg)
    draw = ImageDraw.Draw(canvas)


    


    # 2. Model name


    # 2.5 shop name


    # 3. Bottom polygon
    bottom_shape_points = [(0, H), (W, H), (W, H - 300), (0, H - 950)]
    draw.polygon(bottom_shape_points, fill=safe_main_color)

    # 3.5. brand logo
    add_brand_logo(canvas, brand, variant=2, mode=0, pos=(50, 100) , color=(0,0,0), max_size=(200,200))
    
    # 4. Shoe photo 
    place_shoe(canvas, photo_1_rem,
               pos=(300, 1360),  
               max_size=(850, 600),
               angle=-23,
               center_x=False)


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
