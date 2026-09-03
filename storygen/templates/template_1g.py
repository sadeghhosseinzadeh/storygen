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
    draw_sizes_box)



def template_1g(photo_1, model_name, sizes, shop_name_en, brand):

    W, H = 1080, 1920

    # -------------------------
    # Colors
    # -------------------------
    photo_1_rem = remove_background(photo_1)

    main_color, second_color, saturated_color = extract_colors(photo_1_rem)

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
    font_bid = load_font("Segoe.UI.Bold_p30download.com.ttf", 60)
    font_brand = load_font("Segoe.UI.Semibold_p30download.com.ttf", 50)

    text_color = main_color

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
            font_size
        )

        bbox = font_big.getbbox(brand_text)
        brand_w = bbox[2] - bbox[0]

    brand_x = (W - brand_w) // 2

    draw.text(
        (brand_x, 240),
        brand_text,
        fill=second_color,
        font=font_big
    )

    # -------------------------
    # Model Name
    # -------------------------
    bbox = font_bid.getbbox(model_name)
    model_w = bbox[2] - bbox[0]

    model_x = (W - model_w) // 2

    draw.text(
        (model_x, 570),
        model_name,
        fill=second_color,
        font=font_bid
    )

    # -------------------------
    # Shop Name
    # -------------------------
    if shop_name_en:

        bbox = font_brand.getbbox(shop_name_en)

        shop_name_en_w = bbox[2] - bbox[0]
        shop_name_en_x = (W - shop_name_en_w) // 2

        draw.text(
            (shop_name_en_x, 645),
            shop_name_en,
            fill=second_color,
            font=font_brand
        )

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

        logo_pos = (160, 1550)

        sizes_box_x = W - 350 - 60

        shoe_angle = 30

        footer_angle = 31

    # -------------------------
    # Bottom Shape
    # -------------------------
    draw.polygon(
        bottom_shape_points,
        fill=saturated_color
    )

    # -------------------------
    # Brand Logo
    # -------------------------
    add_brand_logo(
        canvas,
        brand,
        variant=2,
        mode=0,
        pos=logo_pos,
        color=main_color,
        max_size=(200, 200)
    )

    # -------------------------
    # Shoe
    # -------------------------
    place_shoe(
        canvas,
        photo_1_rem,
        pos=(None, 1360),
        max_size=(850, 600),
        angle=shoe_angle,
        center_x=True
    )
    rect_color = lighten_color(main_color, 0.15)
    
    # -------------------------
    # Sizes Box
    # -------------------------
    if is_left:
        sizes_pos = (W - 200, 1550)   # right side
    else:
        sizes_pos = (200, 1550)       # left side

    draw_sizes_box(
        canvas,
        sizes=sizes,
        show_box=True,
        box_color=bg,
        pos=sizes_pos,            
        max_height=None,
        min_height=None,
        title_font_size=60,
        title_color=(220,0,0),
        size_font_size=45,
        size_color=(0,0,0),
        spacing=15 )


    # -------------------------
    # Footer Text
    # -------------------------
    rand_num = random.randint(100, 999)
    
    footer_text = f"برای اطلاعات بیشتر، {rand_num} رو دایرکت کن"
    
    if not is_left:
        footer_angle = -31
        footer_pos = (10, 1370)
    else:
        footer_angle = 31
        footer_pos = (10, 1070)
    
    temp_img = Image.new(
        "RGBA",
        (W, H),
        (255, 255, 255, 0)
    )
    
    temp_draw = ImageDraw.Draw(temp_img)
    
    temp_draw.text(
        footer_pos,
        footer_text,
        fill=rect_color,
        font=font_fid
    )
    
    rotated_text = temp_img.rotate(
        footer_angle,
        expand=True
    )
    
    canvas.paste(
        rotated_text,
        (0, 0),
        rotated_text
    )
    return canvas
