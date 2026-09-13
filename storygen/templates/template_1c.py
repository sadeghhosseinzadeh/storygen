from PIL import Image, ImageDraw, ImageFont
import cairo
import random
import numpy as np
from storygen.Utils.sizes_utils import draw_sizes_grid
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
    second = lighten_color(saturated_color, 0.90)
    third = darken_color(saturated_color, 0.10)
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
    
    # Make Cairo surface transparent
    ctx.set_source_rgba(0, 0, 0, 0)
    ctx.set_operator(cairo.OPERATOR_SOURCE)
    ctx.paint()

    draw_trapezoid(ctx,
                   x_left=354,
                   y_top=0,
                   x_right=W-354,
                   y_top_right=0,
                   y_bottom_left=H,
                   y_bottom_right=H,
                   color=third,
                   radius=0)

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
        max_width= H-712,
        start_pos= (None, 200),
        fill=(255,255,255),
        allow_multiline=F
    )

    # -------------------------
    # Shop Name
    # -------------------------
    draw_text(
        canvas,
        text=shop_name_en,
        font_path_eng="calibrili.ttf",
        font_size_eng=50,
        font_path_per="A Mitra 04.ttf",
        font_size_per=60,
        pos=(None, 320),
        rotation=0,
        fill=(255, 255, 255),
        padding_top=3,
        padding_bottom=5)
    

    # -------------------------
    #  User logo 
    # -------------------------
    add_user_logo(
        canvas,
        logo_path=logo,
        pos=(None, 380),
        max_size=(110, 110),
        center_x=True,
        opacity=150)
    

    # -------------------------
    # Shoe
    # -------------------------
    place_shoe2(
        canvas, photo_1_rem,
        pos=(None, 1250),  
        max_size=(1000, 600),
        angle_left=40,
        angle_right=-40,
        center_x=True)
    
    # -------------------------
    # Sizes Box
    # -------------------------

    draw_sizes_grid(
        canvas,
        sizes,
        pos=(250, 1650),
        box_colors=(second, third),  
        box_radius=12,
    
        # Grid limits
        max_rows=12,
        max_cols=1,
    
        # Auto shrink settings
        shrink_threshold=12,
        font_path="Segoe.UI.Semibold_p30download.com.ttf",
        font_size=40,
        box_size=(210, 60),
    
        # Padding inside each box
        padding_left=0,
        padding_right=0,
        padding_top=0,
        padding_bottom=25,
        h_spacing=10,
        v_spacing=35)

    # -------------------------
    # Footer Text
    # -------------------------
    rand_num = random.randint(100, 999)
    footer_main = "استعلام قیمت عدد"
    footer_number = f"({to_english_digits(str(rand_num))})"
    
    # Colors
    main_color_footer = (255, 255, 255)
    number_color_footer = (255, 140, 0)
    
    # Fonts
    font_main = load_font("Homa.ttf", 48)
    font_num  = load_font("Segoe.UI.Bold_p30download.com.ttf", 49)
    
    # --- Render each text separately to measure REAL pixel center ---
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
    
    # Render both texts
    img_main, main_w, main_h, main_center = render_and_center(footer_main, font_main, main_color_footer)
    img_num,  num_w,  num_h,  num_center  = render_and_center(footer_number, font_num, number_color_footer)
    
    # Unified height
    max_h = max(main_h, num_h)
    
    # Align visual centers
    main_y = (max_h // 2) - main_center
    num_y  = (max_h // 2) - num_center
    
    # RTL order: number first
    gap = 20
    total_w = num_w + gap + main_w
    
    # Final footer image
    temp_img = Image.new("RGBA", (total_w + 40, max_h + 40), (0,0,0,0))
    
    # Paste number
    temp_img.paste(img_num, (10, num_y), img_num)
    
    # Paste Persian text
    temp_img.paste(img_main, (10 + num_w + gap, main_y), img_main)
    
    final_pos = (270, 1620)   
    
    canvas.paste(temp_img, final_pos, temp_img)



    return canvas
