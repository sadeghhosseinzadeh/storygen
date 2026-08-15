import cairo
from PIL import Image, ImageDraw
from storygen.processing import remove_background, extract_colors
from storygen.utils import lighten_color, load_font
from storygen.utils import (
    remove_background, extract_colors, lighten_color, darken_color,
    adjust_saturation, load_font, add_brand_logo, place_shoe,
    draw_trapezoid, add_user_logo, draw_text
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
    place_shoe(canvas, photo_1_rem, pos=(None,550), max_size=(600,400), angle=0, center_x=True)
    place_shoe(canvas, photo_2_rem, pos=(None,950), max_size=(600,400), angle=0, center_x=True)

    # --- 4. Model name ---
    font_model = load_font("Segoe.UI_p30download.com.ttf", 60)
    bbox = font_model.getbbox(model_name)
    model_x = (W - (bbox[2]-bbox[0])) // 2
    draw.text((model_x, 190), model_name, fill=shades[3], font=font_model)

    # --- 5. Shop name ---
    font_shop = load_font("Segoe.UI_p30download.com.ttf", 50)
    bbox = font_shop.getbbox(shop_name_en)
    shop_x = (W - (bbox[2]-bbox[0])) // 2
    draw.text((shop_x, 255), shop_name_en, fill=shades[3], font=font_shop)


    # --- 6. Sizes box ---
    if sizes:
        # If sizes is a string like "55, 56, 67", split it into a list
        if isinstance(sizes, str):
            sizes_list = [s.strip() for s in sizes.split(",") if s.strip()]
        else:
            sizes_list = sizes  # already a list

        font_mid = load_font("Segoe.UI_p30download.com.ttf", 40)
        title_text = "Size:"
        bbox = font_mid.getbbox(title_text)
        title_w, title_h = bbox[2]-bbox[0], bbox[3]-bbox[1]

        # Shift everything up and left by changing these anchors
        rect_x1 = 80
        rect_y1 = H - 440
        rect_w = 400

        # Position title
        title_x = rect_x1 + (rect_w - title_w)//2
        title_y = rect_y1 + 20
        draw.text((title_x, title_y), title_text, fill=shades[0], font=font_mid)

        # Draw each size below the title
        current_y = title_y + title_h + 30
        for size in sizes_list:
            bbox = font_mid.getbbox(size)
            size_w, size_h = bbox[2]-bbox[0], bbox[3]-bbox[1]
            size_x = rect_x1 + (rect_w - size_w)//2
            draw.text((size_x, current_y), size, fill=shades[0], font=font_mid)
            current_y += size_h + 15

    # --- 7. Footer text ---
    rand_num = random.randint(100, 999)
    footer_text = f"برای اطلاعات بیشتر\n {rand_num} رو دایرکت کن!"
    font_footer = load_font("A Mitra 04.ttf", 42)
    draw.multiline_text((W//2 + 50, H-340), footer_text, fill=shades[0] , font=font_footer, align="center", spacing=20)

    # --- 8. User logo ---
    add_user_logo(canvas,
                  logo_path=logo,
                  pos=(None, 1300),
                  max_size=(180,180),
                  center_x=False)



    return canvas
