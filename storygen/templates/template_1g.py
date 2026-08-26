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
    detect_shoe_direction)



def template_1g(photo_1, model_name, sizes, shop_name_en, brand):

    W, H = 1080, 1920

    # -------------------------
    # Colors
    # -------------------------
    photo_1_rem = remove_background(photo_1)

    main_color, second_color = extract_colors(photo_1_rem)

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
    font_brand = load_font("Segoe.UI.Semibold_p30download.com.ttf", 55)

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

        bbox = font_bid.getbbox(shop_name_en)

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
            (W, H),
            (0, H - 300),
            (W, H - 950)
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
        fill=second_color
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

    # -------------------------
    # Sizes Box
    # -------------------------
    if sizes:

        if isinstance(sizes, str):
            sizes = [
                s.strip()
                for s in sizes.split(",")
                if s.strip()
            ]

        rect_w = 350

        rect_x1 = sizes_box_x
        rect_y1 = 1550

        rect_color = lighten_color(main_color, 0.15)

        title_text = "Size:"

        bbox = font_mid.getbbox(title_text)

        title_w = bbox[2] - bbox[0]
        title_h = bbox[3] - bbox[1]

        line_spacing = 10

        sizes_heights = [
            font_mid.getbbox(s)[3] -
            font_mid.getbbox(s)[1]
            for s in sizes
        ]

        total_text_h = (
            title_h
            + sum(sizes_heights)
            + line_spacing * (len(sizes) - 1)
        )

        rect_h = total_text_h + 80

        rect_x2 = rect_x1 + rect_w
        rect_y2 = rect_y1 + rect_h

        draw.rounded_rectangle(
            [rect_x1, rect_y1, rect_x2, rect_y2],
            radius=15,
            fill=rect_color
        )

        title_x = rect_x1 + (rect_w - title_w) // 2

        title_y = rect_y1 + 20

        draw.text(
            (title_x, title_y),
            title_text,
            fill=second_color,
            font=font_mid
        )

        current_y = title_y + title_h + 20

        for size in sizes:

            bbox = font_mid.getbbox(size)

            size_w = bbox[2] - bbox[0]
            size_h = bbox[3] - bbox[1]

            size_x = rect_x1 + (rect_w - size_w) // 2

            draw.text(
                (size_x, current_y),
                size,
                fill=second_color,
                font=font_mid
            )

            current_y += size_h + line_spacing

    # -------------------------
    # Footer Text
    # -------------------------
    rand_num = random.randint(100, 999)

    footer_text = (
        f"برای اطلاعات بیشتر، {rand_num} رو دایرکت کن"
    )

    temp_img = Image.new(
        "RGBA",
        (W, H),
        (255, 255, 255, 0)
    )

    temp_draw = ImageDraw.Draw(temp_img)

    temp_draw.text(
        (10, 1370),
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
