import cairo
import random
from PIL import Image, ImageDraw
from storygen.utils import (
    remove_background, extract_colors, lighten_color, darken_color,
    adjust_saturation, load_font, add_brand_logo, place_shoe,
    draw_trapezoid, add_user_logo, draw_text, draw_sizes_box3
)


def template_2a(photo_1, photo_2, model_name, shop_name_en, sizes, brand, logo=None):
    W, H = 1080, 1920

    # Remove background and get colors
    photo_1_rem = remove_background(photo_1)
    photo_2_rem = remove_background(photo_2)
    main_color, second_color = extract_colors(photo_1_rem)


    # --- 1. Background with trapezoids ---
    surface = cairo.ImageSurface(cairo.FORMAT_ARGB32, W, H)
    ctx = cairo.Context(surface)

    # Fill background with black
    ctx.set_source_rgb(0, 0, 0)
    ctx.rectangle(0, 0, W, H)
    ctx.fill()

    # Generate shades of the main color
    shades = [
        adjust_saturation(darken_color(main_color, 0.55), 0.25),
        lighten_color(main_color, 0.90),
        darken_color(main_color, 0.10),
        adjust_saturation(lighten_color(main_color, 0.3), 0.1),
    ]

    # Convert to 0–1 range for Cairo
    def rgb_norm(c): return (c[0]/255, c[1]/255, c[2]/255)

    # Draw trapezoids with your coordinates
    draw_trapezoid(ctx, 35, 35, W-35, 35, 405, 540, rgb_norm(shades[0]))
    draw_trapezoid(ctx, 35, 440, W-35, 575, 900, 900, rgb_norm(shades[1]))
    draw_trapezoid(ctx, 35, 935, W-35, 935, 1260, 1405, rgb_norm(shades[2]))
    draw_trapezoid(ctx, 35, 1295, W-35, 1440, H-30, H-30, rgb_norm(shades[3]))

    # Export Cairo surface to PIL for the rest of the workflow
    surface.write_to_png("bg.png")
    canvas = Image.open("bg.png").convert("RGBA")
    draw = ImageDraw.Draw(canvas)

    # --- 2. Logo overlay ---
    add_brand_logo(canvas, brand, mode=0, opacity=60, color=(0,0,0), max_size=(950,800))

    # --- 3. Shoe photos ---
    place_shoe(canvas, photo_1_rem, pos=(None,490), max_size=(770,400), angle=0, center_x=True)
    place_shoe(canvas, photo_2_rem, pos=(None,920), max_size=(770,400), angle=0, center_x=True)


    # --- 4. Model name with brand: BRAND | MODEL ---
    combined = f"{brand.upper()} | {model_name}"
    
    font_model = load_font("GOTHICB.TTF", 90)
    
    bbox = font_model.getbbox(combined)
    combined_w = bbox[2] - bbox[0]
    
    model_x = (W - combined_w) // 2
    
    draw.text((model_x, 190), combined, fill=shades[3], font=font_model)


    # --- 5. Shop name ---
    font_shop = load_font("GOTHIC.TTF", 50)
    if shop_name_en:   # <-- skips if None, empty, or ""
        bbox = font_shop.getbbox(shop_name_en)
        shop_x = (W - (bbox[2]-bbox[0])) // 2
        draw.text((shop_x, 295), shop_name_en, fill=shades[3], font=font_shop)


    # --- 6. Sizes box ---
    draw_sizes_box3(
        canvas,
        sizes=sizes,
        pos=(80, H - 340),
        show_box=False,
        max_height=700,
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
    
       

    # --- 7. Footer text (two-line, aligned, mixed fonts) ---
    rand_num = random.randint(100, 999)
    
    line1 = "برای اطلاعات بیشتر"
    line2_main = "رو دایرکت کن!"
    line2_num  = to_english_digits(str(rand_num))   # English digits
    
    # Colors
    color_main = shades[0]
    color_num  = (255, 140, 0)   # orange
    
    # Fonts
    font_per = load_font("Homa.ttf", 55)   # Persian lines (bigger)
    font_num = load_font("Segoe.UI.Bold_p30download.com.ttf", 60)  # English number
    
    # --- Render helper (visual-center aligned) ---
    def render_text(text, font, color):
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
    
    # Render line 1 (Persian)
    img_line1, w1, h1, c1 = render_text(line1, font_per, color_main)
    
    # Render line 2 → number + Persian text
    img_num,  w_num,  h_num,  c_num  = render_text(line2_num, font_num, color_num)
    img_main2, w_main2, h_main2, c_main2 = render_text(line2_main, font_per, color_main)
    
    # Combine line 2 horizontally
    line2_w = w_num + 20 + w_main2
    line2_h = max(h_num, h_main2)
    
    line2_img = Image.new("RGBA", (line2_w + 40, line2_h + 40), (0,0,0,0))
    
    num_y  = (line2_h // 2) - c_num
    main2_y = (line2_h // 2) - c_main2
    
    line2_img.paste(img_num,  (10, num_y),  img_num)
    line2_img.paste(img_main2, (10 + w_num + 20, main2_y), img_main2)
    
    # Final placement
    footer_x = W//2 + 50
    footer_y = H - 340
    
    canvas.paste(img_line1, (footer_x, footer_y), img_line1)
    canvas.paste(line2_img, (footer_x, footer_y + h1 + 25), line2_img)


    # --- 8. User logo ---
    add_user_logo(canvas,
                  logo_path=logo,
                  pos=(None, 1300),
                  max_size=(180,180),
                  center_x=False,
                  opacity=105)


    return canvas
