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

def draw_sizes_box2(
    canvas,
    sizes,
    pos=None,
    show_box=True,
    box_color=None,
    box_radius=15,
    max_height=None,
    min_height=None,
    title_text="Size:",
    title_font_path="Segoe.UI.Semibold_p30download.com.ttf",
    title_font_size=55,
    title_color=(220,0,0),
    size_font_path="Segoe.UI.Semibold_p30download.com.ttf",
    size_font_size=45,
    size_color=(0,0,0),
    padding_x=40,
    padding_y=20,
    spacing=10
):
    # Skip if no sizes
    if not sizes:
        return

    # Normalize sizes input
    if isinstance(sizes, str):
        sizes = [s.strip() for s in sizes.split(",") if s.strip()]

    draw = ImageDraw.Draw(canvas)
    W, H = canvas.size

    # Load fonts
    font_title = load_font(title_font_path, title_font_size)
    font_size = load_font(size_font_path, size_font_size)

    # Baseline correction (fixes weird top/bottom padding)
    TITLE_OFFSET_Y = -8
    SIZE_OFFSET_Y = -6

    # Measure title
    bbox_title = font_title.getbbox(title_text)
    title_w = bbox_title[2] - bbox_title[0]
    title_h = bbox_title[3] - bbox_title[1]

    # Measure sizes
    size_heights = []
    size_widths = []
    for s in sizes:
        b = font_size.getbbox(s)
        size_widths.append(b[2] - b[0])
        size_heights.append(b[3] - b[1])

    total_sizes_h = sum(size_heights) + spacing * (len(sizes) - 1)

    # Total block size
    block_w = max(title_w, max(size_widths)) + padding_x * 2
    block_h = title_h + total_sizes_h + padding_y * 2

    # Apply height limits
    if max_height and block_h > max_height:
        block_h = max_height
    if min_height and block_h < min_height:
        block_h = min_height

    # Determine position
    if pos is None:
        center_x = W // 2
        center_y = H // 2
    else:
        center_x, center_y = pos

    # Top-left corner of block
    x1 = center_x - block_w // 2
    y1 = center_y - block_h // 2
    x2 = x1 + block_w
    y2 = y1 + block_h

    # Draw background box
    if show_box:
        if box_color is None:
            box_color = (240, 240, 240)
        draw.rounded_rectangle([x1, y1, x2, y2], radius=box_radius, fill=box_color)

    # Draw title
    title_x = center_x - title_w // 2
    title_y = y1 + padding_y + TITLE_OFFSET_Y
    draw.text((title_x, title_y), title_text, fill=title_color, font=font_title)

    # Draw sizes
    EXTRA_TITLE_GAP = 25
    current_y = title_y + title_h + EXTRA_TITLE_GAP

    for s in sizes:
        b = font_size.getbbox(s)
        sw = b[2] - b[0]
        sh = b[3] - b[1]
        sx = center_x - sw // 2
        draw.text((sx, current_y + SIZE_OFFSET_Y), s, fill=size_color, font=font_size)
        current_y += sh + spacing

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
    rect_color = lighten_color(main_color, 0.15)
    # # -------------------------
    # # Sizes Box
    # # -------------------------
    # if sizes:
    #     if isinstance(sizes, str):
    #         sizes = [
    #             s.strip()
    #             for s in sizes.split(",")
    #             if s.strip()]
    #     rect_w = 350
    #     rect_x1 = sizes_box_x
    #     rect_y1 = 1550
    #     rect_color = lighten_color(main_color, 0.15)
    #     title_text = "Size:"
    #     bbox = font_mid.getbbox(title_text)
    #     title_w = bbox[2] - bbox[0]
    #     title_h = bbox[3] - bbox[1]
    #     line_spacing = 10
    #     sizes_heights = [
    #         font_mid.getbbox(s)[3] -
    #         font_mid.getbbox(s)[1]
    #         for s in sizes]
    #     total_text_h = (
    #         title_h
    #         + sum(sizes_heights)
    #         + line_spacing * (len(sizes) - 1)
    #     )
    #     rect_h = total_text_h + 80
    #     rect_x2 = rect_x1 + rect_w
    #     rect_y2 = rect_y1 + rect_h
    #     draw.rounded_rectangle(
    #         [rect_x1, rect_y1, rect_x2, rect_y2],
    #         radius=15,
    #         fill=rect_color)
    #     title_x = rect_x1 + (rect_w - title_w) // 2
    #     title_y = rect_y1 + 20
    #     draw.text(
    #         (title_x, title_y),
    #         title_text,
    #         fill=second_color,
    #         font=font_mid)

    #     current_y = title_y + title_h + 20
    #     for size in sizes:
    #         bbox = font_mid.getbbox(size)
    #         size_w = bbox[2] - bbox[0]
    #         size_h = bbox[3] - bbox[1]
    #         size_x = rect_x1 + (rect_w - size_w) // 2
    #         draw.text(
    #             (size_x, current_y),
    #             size,
    #             fill=second_color,
    #             font=font_mid)
    #         current_y += size_h + line_spacing

    # --- 7. Sizes box ---
    draw_sizes_box(
        canvas,
        sizes=sizes,
        show_box=True,
        box_color=bg,
        pos=(350, 1550),            
        show_box=False,
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
        footer_pos = (300, 1070)
    
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
