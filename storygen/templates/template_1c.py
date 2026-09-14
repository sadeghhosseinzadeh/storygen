from PIL import Image, ImageDraw, ImageFont
import cairo
import random
import numpy as np
from storygen.Utils.sizes_utils import draw_sizes_grid
from storygen.Utils.shoe_utils import place_shoe_1c

from pathlib import Path
import storygen

from storygen.utils import (
    lighten_color,
    darken_color,
    draw_text,
    load_font,
    place_shoe2,
    remove_background,
    adjust_saturation,
    extract_colors,
    add_brand_logo2,
    detect_shoe_direction,
    to_english_digits,
    add_user_logo,
    protect_color,
    draw_trapezoid,
    draw_scaled_text)


def template_1c(photo_1, model_name, sizes, shop_name_en, brand, logo):
    W, H = 1080, 1920

    # -------------------------
    # Colors
    # -------------------------
    photo_1_rem = remove_background(photo_1)  
    main_color, second_color, saturated_color = extract_colors(
        photo_1_rem,
        include_saturated=True)

    # Lighten main color → protect from becoming white
    first = adjust_saturation(darken_color(saturated_color, 0.55), 0.25)
    second = lighten_color(saturated_color, 0.45)
    third = darken_color(saturated_color, 0.20)
    fourth = adjust_saturation(lighten_color(saturated_color, 0.3), 0.1)

    canvas = Image.new("RGB", (W, H), second)
    draw = ImageDraw.Draw(canvas)
    
    # -------------------------
    #  white req
    # -------------------------
    package_root = Path(storygen.__file__).parent
    overlay_path = package_root / "bg" / "template1c_bg.png"
    
    overlay = Image.open(overlay_path).convert("RGBA").resize((W, H))
    canvas.paste(overlay, (0, 0), overlay)
    
    # -------------------------
    # Detect direction
    # -------------------------
    shoe_direction = detect_shoe_direction(photo_1_rem)
    is_left = shoe_direction == "left"

    # -------------------------
    # middle req
    # -------------------------
    # --- Cairo surface for trapezoid drawing ---
    surface = cairo.ImageSurface(cairo.FORMAT_ARGB32, W, H)
    ctx = cairo.Context(surface)
    
    # Transparent background for Cairo layer
    ctx.set_source_rgba(0, 0, 0, 0)
    ctx.set_operator(cairo.OPERATOR_SOURCE)
    ctx.paint()
    
    def normalize_color(rgb):
        return tuple(c/255.0 for c in rgb)
    
    draw_trapezoid(
        ctx,
        x_left=354,
        y_top=0,
        x_right=W-354,
        y_top_right=0,
        y_bottom_left=H,
        y_bottom_right=H,
        color=normalize_color(third),  # normalized
        radius=0
    )

    
    # Merge trapezoid into Pillow canvas
    buf = surface.get_data()
    cairo_img = Image.frombuffer("RGBA", (W, H), buf, "raw", "BGRA", 0, 1)
    canvas.paste(cairo_img, (0, 0), cairo_img)


    # -------------------------
    # Brand Logo
    # -------------------------
    add_brand_logo2(
        canvas,
        brand,
        mode=0,
        variant=1,
        opacity=255,
        pos=(None, 60),
        color=(255,255,255),
        max_size=(260, 200))

    
    # -------------------------
    # Model Name
    # -------------------------
    model_text = model_name.upper()
    draw_scaled_text(
        draw,
        text=model_text,
        font_path="calibrib.ttf",
        max_font_size=80,
        max_width= 370,
        max_height=200,
        start_pos= (None, 255),
        fill=(255,255,255),
        allow_multiline=False
    )

    # -------------------------
    # Shop Name
    # -------------------------
    draw_scaled_text(
        draw,
        text=shop_name_en,
        font_path="calibrili.ttf",
        max_font_size=50,
        max_width= 370,
        max_height=200,
        start_pos= (None, 335),
        fill=(255,255,255),
        allow_multiline=False
    )
    
    # -------------------------
    #  User logo 
    # -------------------------
    add_user_logo(
        canvas,
        logo_path=logo,
        pos=(None, 395),
        max_size=(105, 105),
        center_x=True,
        opacity=230)
    

    # -------------------------
    # Shoe
    # -------------------------
    place_shoe_1c(
        canvas,
        photo_1_rem,
        pos=(None, 1300),
        max_size=(1100, 600),
        angle_left=40,
        angle_right=-40,
        center_x=True,
    
        shadow_front_width=70,   # thicker under toe
        shadow_back_width=30,     # thinner under heel
        shadow_length=0.8,       # shorter shadow
        shadow_darkness=190,      # darker
        shadow_softness=10,       # softer blur
        shadow_offset=(0, 0),    # move shadow down a bit
    )




    # -------------------------
    # Sizes Box
    # -------------------------
    # Parse sizes (comma separated)
    sizes_list = [s.strip() for s in sizes.split(",") if s.strip()]

    # First up to 5
    sizes_left = sizes_list[:5]

    # Second up to 5 (only if more than 5)
    sizes_right = sizes_list[5:10]

    # Left column 
    draw_sizes_grid(
        canvas,
        sizes_left,
        pos=(200, 1600),
        box_colors=(second, third),
        box_radius=12,
        max_rows=12,
        max_cols=1,
        shrink_threshold=12,
        font_path="Segoe.UI.Semibold_p30download.com.ttf",
        font_size=40,
        box_size=(220, 60),
        padding_left=0,
        padding_right=0,
        padding_top=0,
        padding_bottom=25,
        h_spacing=10,
        v_spacing=35
    )

    # Right column 
    if sizes_right:
        draw_sizes_grid(
            canvas,
            sizes_right,
            pos=(880, 1600),  
            box_colors=(second, third),
            box_radius=12,
            max_rows=12,
            max_cols=1,
            shrink_threshold=12,
            font_path="Segoe.UI.Semibold_p30download.com.ttf",
            font_size=40,
            box_size=(220, 60),
            padding_left=0,
            padding_right=0,
            padding_top=0,
            padding_bottom=25,
            h_spacing=10,
            v_spacing=35
        )


    # -------------------------
    # Footer Text
    # -------------------------
    rand_num = random.randint(100, 999)
    footer_main = "استعلام قیمت"
    footer_number = f"({to_english_digits(str(rand_num))})"
    
    base_x = 420
    base_y = 1735
    
    font_main = load_font("Homa.ttf", 45)          # Persian font
    font_num  = load_font("Segoe.UI.Bold_p30download.com.ttf", 55)      # English font
    
    draw.text((base_x, base_y), footer_main, fill=(255, 255, 255), font=font_main)
    
    bbox_main = font_main.getbbox(footer_main)
    main_w = bbox_main[2] - bbox_main[0]
    
    bbox_num = font_num.getbbox(footer_number)
    num_w = bbox_num[2] - bbox_num[0]
    
    num_x = base_x + (main_w - num_w) // 2
    num_y = base_y + bbox_main[3] - bbox_main[1] + 10
    
    draw.text((num_x, num_y), footer_number, fill=(255,255,255), font=font_num)

    return canvas
