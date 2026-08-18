import cairo
import random
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont, ImageFilter
import io
import cairosvg
import storygen

from storygen.utils import (
    remove_background, extract_colors, lighten_color, darken_color,
    adjust_saturation, load_font, add_brand_logo, place_shoe,
    draw_trapezoid, add_user_logo, draw_text
)

def template_2b(photo_1, photo_2, model_name, shop_name_en, sizes, brand, logo=None):
    W, H = 1080, 1920

    # --- 1. Background image ---
    # Load a background PNG/JPG from your folder
    package_root = Path(storygen.__file__).parent
    bg_path = package_root / "bg" / "template2b_bg.png"
    
    canvas = Image.open(bg_path).convert("RGBA").resize((W, H))
    draw = ImageDraw.Draw(canvas)

    # --- 2. Remove shoe backgrounds ---
    photo_1_rem = remove_background(photo_1)
    photo_2_rem = remove_background(photo_2)

    # --- 3. Brand logo overlay ---
    add_brand_logo(canvas, brand, mode=0, opacity=255, pos=(720, 940), color=(0,0,0), max_size=(180,180))

    # --- 4. Shoe photos ---
    place_shoe(canvas, photo_1_rem, pos=(None,225), max_size=(700,480), angle=0, center_x=True)
    place_shoe(canvas, photo_2_rem, pos=(None,1310), max_size=(700,480), angle=0, center_x=True)

    # --- 5. Model name ---
    font_model = load_font("Segoe.UI.Bold_p30download.com.ttf", 70)
    bbox = font_model.getbbox(model_name)
    model_x = (W - (bbox[2]-bbox[0])) // 2
    draw.text((model_x, 757), model_name, fill=(0,0,0), font=font_model)

    # --- 6. Shop name ---
    if shop_name_en and shop_name_en.strip():
        draw_text(canvas,
                   text=shop_name_en,
                   font_path_eng="Segoe.UI.Semibold_p30download.com.ttf",
                   font_size_eng=55,
                   font_path_per="A Mitra 04.ttf",
                   font_size_per=60,
                   pos=(None, 845),
                   rotation=0,
                   fill=(0,0,0))



    # --- 7. Sizes box ---
    if sizes:
        if isinstance(sizes, str):
            sizes_list = [s.strip() for s in sizes.split(",") if s.strip()]
        else:
            sizes_list = sizes

        font_mid = load_font("Segoe.UI.Semibold_p30download.com.ttf", 45)
        title_text = "Size:"
        bbox = font_mid.getbbox(title_text)
        title_w, title_h = bbox[2]-bbox[0], bbox[3]-bbox[1]

        rect_x1 = 50
        rect_y1 = 900
        rect_w = 400

        title_x = rect_x1 + (rect_w - title_w)//2
        title_y = rect_y1 + 20
        draw.text((title_x, title_y), title_text, fill=(0,0,0), font=font_mid)

        current_y = title_y + title_h + 30
        for size in sizes_list:
            bbox = font_mid.getbbox(size)
            size_w, size_h = bbox[2]-bbox[0], bbox[3]-bbox[1]
            size_x = rect_x1 + (rect_w - size_w)//2
            draw.text((size_x, current_y), size, fill=(0,0,0), font=font_mid)
            current_y += size_h + 15

    # --- 8. Footer text ---
    rand_num = random.randint(100, 999)
    footer_text = f"برای اطلاعات بیشتر\n {rand_num} رو دایرکت کن!"
    draw_text(canvas,
               text= footer_text,
               font_path_eng="Segoe.UI_p30download.com.ttf",
               font_size_eng=55,
               font_path_per="Homa.ttf",
               font_size_per=40,
               pos=(20, 1350),
               rotation=90,
               fill=(0,0,0),
               spacing=20,
               padding=30)

    # --- 9. User logo ---
    add_user_logo(canvas,
                  logo_path=logo,
                  pos=(None, 1300),
                  max_size=(180,180),
                  center_x=False)

    return canvas
