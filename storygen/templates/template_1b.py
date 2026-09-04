from PIL import Image, ImageDraw, ImageFont
import cairo
import random
import numpy as np

from storygen.utils import (
    lighten_color,
    draw_text,
    load_font,
    place_shoe,
    remove_background,
    extract_colors,
    add_brand_logo,
    detect_shoe_direction,
    draw_sizes_box3,
    to_english_digits,
    add_user_logo)



def template_1b(photo_1, model_name, sizes, shop_name_en, brand, logo):

    W, H = 1080, 1920

    # -------------------------
    # Colors
    # -------------------------
    photo_1_rem = remove_background(photo_1)

    main_color, second_color, saturated_color = extract_colors(photo_1_rem, include_saturated=True)

    bg = lighten_color(main_color, 0.15)

    canvas = Image.new("RGB", (W, H), bg)
    draw = ImageDraw.Draw(canvas)

    # -------------------------
    # Detect direction
    # -------------------------
    shoe_direction = detect_shoe_direction(photo_1_rem)

    is_left = shoe_direction == "left"

    # -------------------------
    # Fonts
    # -------------------------
    font_mid = load_font("Segoe.UI_p30download.com.ttf", 35)
    font_fid = load_font("Homa.ttf", 38)
    font_bid = load_font("Segoe.UI.Semibold_p30download.com.ttf", 52)
    font_brand = load_font("Segoe.UI.Bold_p30download.com.ttf", 65)

    text_color = saturated_color

    # -------------------------
    # Brand Name
    # -------------------------
    brand_text = brand.upper()

    font_size = 300
    font_big = load_font("Segoe.UI.Bold_p30download.com.ttf", font_size)

    bbox = font_big.getbbox(brand_text)
    brand_w = bbox[2] - bbox[0]

    max_width = 900

    while brand_w > max_width and font_size > 50:
        font_size -= 10
        font_big = load_font(
            "Segoe.UI.Bold_p30download.com.ttf",
            font_size)

        bbox = font_big.getbbox(brand_text)
        brand_w = bbox[2] - bbox[0]

    brand_x = (W - brand_w) // 2

    draw.text(
        (brand_x, 240),
        brand_text,
        fill=saturated_color,
        font=font_big)

    # -------------------------
    # Model Name
    # -------------------------
    bbox = font_brand.getbbox(model_name)
    model_w = bbox[2] - bbox[0]

    model_x = (W - model_w) // 2

    draw.text(
        (model_x, 570),
        model_name,
        fill=saturated_color,
        font=font_brand)

    # -------------------------
    # Shop Name
    # -------------------------
    if shop_name_en:

        bbox = font_bid.getbbox(shop_name_en)

        shop_name_en_w = bbox[2] - bbox[0]
        shop_name_en_x = (W - shop_name_en_w) // 2

        draw.text(
            (shop_name_en_x, 670),
            shop_name_en,
            fill=saturated_color,
            font=font_bid)

    # -------------------------
    # Mirrored Layout Settings
    # -------------------------

    if not is_left:

        # ORIGINAL TEMPLATE
        bottom_shape_points = [
            (0, H),
            (W, H),
            (W, H - 300),
            (0, H - 950)
        ]

        logo_pos = (720, 1590)
        user_logo_pos = (800, 615)
        sizes_box_x = 60
        shoe_angle = -30
        footer_angle = -31

    else:

        # MIRRORED TEMPLATE

        bottom_shape_points = [
            (0, H),
            (0, H - 300),
            (W, H - 950),
            (W, H)
        ]

        logo_pos = (160, 1590)
        user_logo_pos = (100, 615)
        sizes_box_x = W - 350 - 60

        shoe_angle = 30

        footer_angle = 31

    # -------------------------
    # Bottom Shape
    # -------------------------
    draw.polygon(
        bottom_shape_points,
        fill=saturated_color)

    # -------------------------
    # Brand Logo
    # -------------------------
    add_brand_logo(
        canvas,
        brand,
        variant=2,
        mode=0,
        pos=logo_pos,
        color=bg,
        max_size=(200, 200))

    # -------------------------
    #  User logo 
    add_user_logo(
        canvas,
        logo_path=logo,
        pos=user_logo_pos,
        max_size=(180, 180),
        center_x=False,
        opacity=105)
    # -------------------------
    # Shoe
    # -------------------------
    place_shoe(
        canvas,
        photo_1_rem,
        pos=(None, 1360),
        max_size=(860, 600),
        angle=shoe_angle,
        center_x=True)
    
    rect_color = lighten_color(main_color, 0.15)
    # -------------------------
    # Sizes Box
    # -------------------------
    if is_left:
        sizes_pos = (W - 300, 1670)   # right side
    else:
        sizes_pos = (300, 1670)       # left side


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
    # Footer Text (visual-center aligned)
    # -------------------------
    rand_num = random.randint(100, 999)
    footer_main = "استعلام قیمت عدد"
    footer_number = f"({to_english_digits(str(rand_num))})"
    
    # Colors
    main_color_footer = rect_color
    number_color_footer = (255, 140, 0)
    
    # Fonts
    font_main = load_font("Homa.ttf", 48)
    font_num  = load_font("Segoe.UI.Bold_p30download.com.ttf", 49)
    
    # --- Render each text separately to measure REAL pixel center ---
    def render_and_center(text, font, color):
        # Render text to a temporary image
        bbox = font.getbbox(text)
        w = bbox[2] - bbox[0]
        h = bbox[3] - bbox[1]
    
        temp = Image.new("RGBA", (w + 20, h + 20), (0,0,0,0))
        d = ImageDraw.Draw(temp)
        d.text((10, 10), text, font=font, fill=color)
    
        # Convert to alpha mask
        alpha = np.array(temp)[:,:,3]
    
        ys, xs = np.where(alpha > 0)
        top = ys.min()
        bottom = ys.max()
    
        # True visual height
        visual_h = bottom - top
    
        # Visual center offset
        center_offset = (visual_h // 2) + top
    
        return temp, w, visual_h, center_offset
    
    # Render both texts
    img_main, main_w, main_h, main_center = render_and_center(footer_main, font_main, main_color_footer)
    img_num,  num_w,  num_h,  num_center  = render_and_center(footer_number, font_num, number_color_footer)
    
    # Compute unified visual height
    max_h = max(main_h, num_h)
    
    # Compute Y offsets so their visual centers match
    main_y = (max_h // 2) - main_center
    num_y  = (max_h // 2) - num_center
    
    # RTL order: number first
    total_w = num_w + 20 + main_w
    
    # Final footer image
    temp_img = Image.new("RGBA", (total_w + 40, max_h + 40), (0,0,0,0))
    
    # Paste number
    temp_img.paste(img_num, (10, num_y), img_num)
    
    # Paste Persian text
    temp_img.paste(img_main, (10 + num_w + 20, main_y), img_main)
    
    # Rotation logic
    if not is_left:
        footer_angle = -31
        footer_pos = (250, 1178)
    else:
        footer_angle = 31
        footer_pos = (333, 1227)
    
    rotated_text = temp_img.rotate(footer_angle, expand=True)
    canvas.paste(rotated_text, footer_pos, rotated_text)




    return canvas
