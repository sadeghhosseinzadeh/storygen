from PIL import Image, ImageDraw, ImageFont
import cairo
import random

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
    to_english_digits)



def template_1g(photo_1, model_name, sizes, shop_name_en, brand):

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
    font_bid = load_font("Segoe.UI.Bold_p30download.com.ttf", 55)
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
            (shop_name_en_x, 645),
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

        logo_pos = (720, 1550)
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

        logo_pos = (160, 1700)

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
        sizes_pos = (W - 300, 1600)   # right side
    else:
        sizes_pos = (300, 1600)       # left side


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
    # Footer Text (single line, RTL correct)
    # -------------------------
    rand_num = random.randint(100, 999)
    footer_main = "استعلام قیمت عدد"
    footer_number = f"({to_english_digits(str(rand_num))})"
    
    # Colors
    main_color_footer = rect_color
    number_color_footer = (255, 140, 0)   # orange
    
    # Fonts
    font_main = load_font("Homa.ttf", 45)      # Persian font
    font_num  = font_bid                       # English font
    
    # Measure both parts
    bbox_main = font_main.getbbox(footer_main)
    main_w = bbox_main[2] - bbox_main[0]
    
    bbox_num = font_num.getbbox(footer_number)
    num_w = bbox_num[2] - bbox_num[0]
    
    # RTL order: number goes BEFORE Persian text visually
    # So layout = [number] [gap] [persian text]
    
    total_w = num_w + 20 + main_w
    total_h = max(
        bbox_main[3] - bbox_main[1],
        bbox_num[3] - bbox_num[1])
    
    # Transparent layer
    temp_img = Image.new("RGBA", (total_w + 20, total_h + 20), (0,0,0,0))
    temp_draw = ImageDraw.Draw(temp_img)
    
    # Draw number on RIGHT side (RTL)
    num_x = 10
    temp_draw.text((num_x, 10), footer_number, fill=number_color_footer, font=font_num)
    
    # Draw Persian text on LEFT side (RTL)
    main_x = num_x + num_w + 20
    temp_draw.text((main_x, 10), footer_main, fill=main_color_footer, font=font_main)
    
    # Rotation logic
    if not is_left:
        footer_angle = -31
        footer_pos = (10, 1070)
    else:
        footer_angle = 31
        footer_pos = (-20, 1070)
    
    rotated_text = temp_img.rotate(footer_angle, expand=True)
    
    canvas.paste(rotated_text, footer_pos, rotated_text)


    return canvas
