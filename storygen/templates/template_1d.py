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
    draw_trapezoid)


def template_1d(photo_1, model_name, sizes, shop_name_en, brand, logo):
    W, H = 1080, 1920

    # -------------------------
    # Colors
    # -------------------------
    photo_1_rem = remove_background(photo_1)  
    main_color, second_color, saturated_color = extract_colors(
        photo_1_rem,
        include_saturated=True)

    first = adjust_saturation(darken_color(saturated_color, 0.55), 0.25)
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
        pos=(100, 1550),
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
        max_size=(1000, 600))

    # -------------------------
    # User logo
    # -------------------------
    add_user_logo(
        canvas,
        logo_path=logo,
        pos=(800, 1550),
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
        font_size_eng=68,
        font_path_per="A Mitra 04.ttf",
        font_size_per=60,
        pos=(None, 240),
        rotation=0,
        fill=(0, 0, 0),
        padding_top=3,
        padding_bottom=5)

    # -------------------------
    # Sizes Box
    # -------------------------
    draw_sizes_grid(
        canvas,
        sizes,
        pos=(None, 1780),
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
    shadow_path = package_root / "bg" / "template1c_shadow.png"
    shadow_png = Image.open(shadow_path)
    
    place_shoe_1c(
        canvas,
        photo_1_rem,
        shadow_png,
        pos=(None, 1250),
        max_size=(1100, 600),
        angle_left=20,
        angle_right=-20,
        center_x=True,
        shadow_scale=0.5,
        shadow_rotation=0,
        shadow_opacity=0.5,
        shadow_offset=(0,-200),
        toe_offset=(-10, -5),
        flip_shadow_for_left=True,
        shadow_blend_mode="darken"
    )

    # -------------------------
    # Detect direction
    # -------------------------
    shoe_direction = detect_shoe_direction(photo_1_rem)
    is_left = shoe_direction == "left"

    # -------------------------
    # Footer Text (MIRROR WHEN LEFT)
    # -------------------------
    rand_num = random.randint(100, 999)
    footer_main = "استعلام قیمت عدد"
    footer_number = f"({to_english_digits(str(rand_num))})"

    main_color_footer = (0, 0, 0)
    number_color_footer = (255, 140, 0)

    font_main = load_font("Homa.ttf", 48)
    font_num  = load_font("Segoe.UI.Bold_p30download.com.ttf", 49)

    def render_and_center(text, font, color):
        bbox = font.getbbox(text)
        w = bbox[2] - bbox[0]
        h = bbox[3] - bbox[1]

        temp = Image.new("RGBA", (w + 20, h + 20), (0,0,0,0))
        d = ImageDraw.Draw(temp)
        d.text((10, 10), text, font=font, fill=color)

        alpha = np.array(temp)[:,:,3]
        ys, xs = np.where(alpha > 0)
        top = ys.min()
        bottom = ys.max()

        visual_h = bottom - top
        center_offset = (visual_h // 2) + top

        return temp, w, visual_h, center_offset

    img_main, main_w, main_h, main_center = render_and_center(footer_main, font_main, main_color_footer)
    img_num,  num_w,  num_h,  num_center  = render_and_center(footer_number, font_num, number_color_footer)

    max_h = max(main_h, num_h)
    main_y = (max_h // 2) - main_center
    num_y  = (max_h // 2) - num_center

    gap = 20
    total_w = num_w + gap + main_w

    temp_img = Image.new("RGBA", (total_w + 40, max_h + 40), (0,0,0,0))
    temp_img.paste(img_num, (10, num_y), img_num)
    temp_img.paste(img_main, (10 + num_w + gap, main_y), img_main)

    # MIRROR FOOTER IF LEFT
    if is_left:
        temp_img = temp_img.transpose(Image.FLIP_LEFT_RIGHT)
        final_pos = (W - 275 - temp_img.width, 1620)
    else:
        final_pos = (275, 1620)

    canvas.paste(temp_img, final_pos, temp_img)

    # -------------------------
    # Model Name (MIRROR WHEN LEFT)
    # -------------------------
    model_text = model_name.upper()

    if is_left:
        # draw normally on a temp layer then flip
        temp_model = Image.new("RGBA", (W, 300), (0,0,0,0))
        d2 = ImageDraw.Draw(temp_model)

        draw_text(
            temp_model,
            text=model_text,
            font_path_eng="calibrib.ttf",
            font_size_eng=68,
            font_path_per="A Mitra 04.ttf",
            font_size_per=60,
            pos=(None, 0),
            rotation=0,
            fill=(0, 0, 0),
            padding_top=3,
            padding_bottom=5)

        temp_model = temp_model.transpose(Image.FLIP_LEFT_RIGHT)
        canvas.paste(temp_model, (0, 240), temp_model)

    else:
        draw_text(
            canvas,
            text=model_text,
            font_path_eng="calibrib.ttf",
            font_size_eng=68,
            font_path_per="A Mitra 04.ttf",
            font_size_per=60,
            pos=(None, 240),
            rotation=0,
            fill=(0, 0, 0),
            padding_top=3,
            padding_bottom=5)

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
