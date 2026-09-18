from PIL import Image, ImageDraw, ImageFont
import cairo
import random
import numpy as np

from pathlib import Path
import storygen

from storygen.Utils.sizes_utils import draw_sizes_grid
from storygen.Utils.shoe_utils import place_shoe_1c

from storygen.utils import (
    lighten_color,
    darken_color,
    draw_text,
    load_font,
    remove_background,
    adjust_saturation,
    extract_colors,
    add_brand_logo2,
    detect_shoe_direction,
    to_english_digits,
    add_user_logo,
    draw_trapezoid,
    draw_scaled_text)


def template_1d(photo_1, model_name, sizes, shop_name_en, brand, logo):
    W, H = 1080, 1920

    # -------------------------
    # Colors
    # -------------------------
    photo_1_rem = remove_background(photo_1)  
    main_color, second_color, saturated_color = extract_colors(
        photo_1_rem,
        include_saturated=True)

    first = adjust_saturation(darken_color(main_color, 0.55), 0.25)
    second = lighten_color(saturated_color, 0.45)
    third = darken_color(saturated_color, 0.20)
    fourth = adjust_saturation(lighten_color(saturated_color, 0.3), 0.1)
    
    canvas = Image.new("RGB", (W, H), (255,255,255))
    draw = ImageDraw.Draw(canvas)

    # -------------------------
    # Shop Name
    # -------------------------
    draw_text(
        canvas,
        text=shop_name_en,
        font_path_eng="calibrili.ttf",
        font_size_eng=47,
        font_path_per="A Mitra 04.ttf",
        font_size_per=60,
        pos=(100, 1450),
        rotation=0,
        fill=(0, 0, 0),
        padding_top=3,
        padding_bottom=5)

    # -------------------------
    # Brand Logo
    # -------------------------
    add_brand_logo2(
        canvas,
        brand,
        mode=0,
        variant=1,
        opacity=245,
        pos=(None, None),
        color=third,
        max_size=(950, 600))

    # -------------------------
    # User logo
    # -------------------------
    add_user_logo(
        canvas,
        logo_path=logo,
        pos=(800, 1450),
        max_size=(110, 110),
        center_x=False,
        opacity=200)

    # -------------------------
    # Brand Name
    # -------------------------
    brand_text = brand.upper()
    
    draw_text(
        canvas,
        text=brand_text,
        font_path_eng="calibrib.ttf",
        font_size_eng=122,
        font_path_per="A Mitra 04.ttf",
        font_size_per=60,
        pos=(None, 400),
        rotation=0,
        fill=second,
        padding_top=3,
        padding_bottom=5)

    # -------------------------
    # Sizes Box
    # -------------------------
    draw_sizes_grid(
        canvas,
        sizes,
        pos=(None, 1700),
        box_colors=(second, third),  
        box_radius=12,
        max_rows=3,
        max_cols=4,
        max_sizes=12,
        font_path="Segoe.UI.Semibold_p30download.com.ttf",
        font_size=37,
        box_size=(220, 65),
        dark_threshold=140,
        light_threshold=200,
        padding_left=0,
        padding_right=0,
        padding_top=0,
        padding_bottom=20,
        h_spacing=35,
        v_spacing=10)

    # -------------------------
    # Shoe
    # -------------------------
    package_root = Path(storygen.__file__).parent
    shadow_path = package_root / "bg" / "template1d_shadow2.png"
    shadow_png = Image.open(shadow_path)
    
    place_shoe_1c(
        canvas,
        photo_1_rem,
        shadow_png,
        pos=(None, 1250),
        max_size=(1000, 500),
        angle_left=20,
        angle_right=-20,
        center_x=True,
        shadow_scale=0.5,
        shadow_rotation=0,
        shadow_opacity=0.5,
        shadow_offset=(0, 0),
        toe_offset=(0, 0),
        flip_shadow_for_left=True,
        shadow_blend_mode="multiply"
    )

    # -------------------------
    # Detect direction
    # -------------------------
    shoe_direction = detect_shoe_direction(photo_1_rem)
    is_left = shoe_direction == "left"

    # -------------------------
    # Footer Text 
    # -------------------------
    rand_num = random.randint(100, 999)
    footer_main = "استعلام قیمت عدد"
    footer_number = f"({to_english_digits(str(rand_num))})"

    if is_left:
        base_x = 120
        base_y = 300
    else:
        base_x = 700
        base_y = 300
        
    font_main = load_font("Homa.ttf", 45)          # Persian font
    font_num  = load_font("Segoe.UI.Bold_p30download.com.ttf", 55)      # English font
    
    draw.text((base_x, base_y), footer_main, fill=(0, 0, 0), font=font_main)
    
    bbox_main = font_main.getbbox(footer_main)
    main_w = bbox_main[2] - bbox_main[0]
    
    bbox_num = font_num.getbbox(footer_number)
    num_w = bbox_num[2] - bbox_num[0]
    
    num_x = base_x + (main_w - num_w) // 2
    num_y = base_y + bbox_main[3] - bbox_main[1] + 10
    
    draw.text((num_x, num_y), footer_number, fill=(0,0,0), font=font_num)

    
    # -------------------------
    # Model Name (MIRROR WHEN LEFT)
    # -------------------------
    model_text = model_name.upper()

    if is_left:

        draw_scaled_text(
            draw,
            text=model_text,
            font_path="GILSANUB.TTF",
            max_font_size=83,
            max_width= 400,
            max_height=500,
            start_pos= (100, 1200),
            fill=(0,0,0),
            allow_multiline=True)

    else:
        draw_scaled_text(
            draw,
            text=model_text,
            font_path="GILSANUB.TTF",
            max_font_size=83,
            max_width= 400,
            max_height=500,
            start_pos= (700, 1200),
            fill=(0,0,0),
            allow_multiline=True)

    # -------------------------
    # Side trapezoid (MIRROR WHEN LEFT)
    # -------------------------
    surface = cairo.ImageSurface(cairo.FORMAT_ARGB32, W, H)
    ctx = cairo.Context(surface)

    ctx.set_source_rgba(0, 0, 0, 0)
    ctx.set_operator(cairo.OPERATOR_SOURCE)
    ctx.paint()

    def normalize_color(rgb):
        return tuple(c/255.0 for c in rgb)

    if is_left:
        # mirror trapezoid to right side
        draw_trapezoid(
            ctx,
            x_left=W-25,
            y_top=0,
            x_right=W,
            y_top_right=0,
            y_bottom_left=H,
            y_bottom_right=H,
            color=normalize_color(third),
            radius=0
        )
    else:
        draw_trapezoid(
            ctx,
            x_left=0,
            y_top=0,
            x_right=25,
            y_top_right=0,
            y_bottom_left=H,
            y_bottom_right=H,
            color=normalize_color(third),
            radius=0
        )

    buf = surface.get_data()
    cairo_img = Image.frombuffer("RGBA", (W, H), buf, "raw", "BGRA", 0, 1)
    canvas.paste(cairo_img, (0, 0), cairo_img)

    return canvas
