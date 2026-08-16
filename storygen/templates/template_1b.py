from PIL import Image, ImageDraw
import random
import cairo
from storygen.utils import (
    lighten_color, load_font, place_shoe,
    remove_background, extract_colors, draw_trapezoid
)

def template_1b(photo_1, model_name, sizes, brand, shop_name_en):
    W, H = 1080, 1920

    # --- Background ---
    photo_1_rem = remove_background(photo_1)
    main_color, second_color = extract_colors(photo_1_rem)
    bg = lighten_color(main_color, 0.15)

    # Cairo surface for trapezoid + background
    surface = cairo.ImageSurface(cairo.FORMAT_ARGB32, W, H)
    ctx = cairo.Context(surface)

    # Fill background
    ctx.set_source_rgb(bg[0]/255, bg[1]/255, bg[2]/255)
    ctx.rectangle(0, 0, W, H)
    ctx.fill()

    # --- Top trapezoid banner ---
    brand_color = (second_color[0]/255, second_color[1]/255, second_color[2]/255)
    draw_trapezoid(ctx,
                   x_left=35, y_top=35,
                   x_right=W-35, y_top_right=35,
                   y_bottom_left=240, y_bottom_right=240,
                   color=brand_color, radius=77)

    # Export Cairo surface to PIL
    surface.write_to_png("bg.png")
    canvas = Image.open("bg.png").convert("RGBA")
    draw = ImageDraw.Draw(canvas)

    # --- Fonts ---
    font_big = load_font("Segoe.UI.Bold_p30download.com.ttf", 150)
    font_bid = load_font("Segoe.UI_p30download.com.ttf", 70)
    font_mid = load_font("Segoe.UI_p30download.com.ttf", 35)
    font_fid = load_font("A Mitra 04.ttf", 38)

    # --- Brand name ---
    brand_text = brand.upper()
    bbox = font_big.getbbox(brand_text)
    brand_w = bbox[2] - bbox[0]
    brand_x = (W - brand_w) // 2
    draw.text((brand_x, 100), brand_text, fill=second_color, font=font_big)

    # --- Shop name (English) ---
    bbox = font_bid.getbbox(shop_name_en)
    shop_w = bbox[2] - bbox[0]
    shop_x = (W - shop_w) // 2
    draw.text((shop_x, 220), shop_name_en, fill=second_color, font=font_bid)

    # --- Model name ---
    bbox = font_bid.getbbox(model_name)
    model_w = bbox[2] - bbox[0]
    model_x = (W - model_w) // 2
    draw.text((model_x, 640), model_name, fill=second_color, font=font_bid)

    # --- Bottom polygon ---
    bottom_shape_points = [(0, H), (W, H), (W, H - 300), (0, H - 950)]
    draw.polygon(bottom_shape_points, fill=second_color)

    # --- Shoe photo ---
    place_shoe(canvas, photo_1_rem,
               pos=(None, 700),
               max_size=(750, 600),
               angle=-31,
               center_x=True)

    # --- Sizes box ---
    if sizes:
        if isinstance(sizes, str):
            sizes = [s.strip() for s in sizes.split(",") if s.strip()]

        rect_w = 350
        rect_x1 = 60
        rect_y1 = 1550
        rect_color = lighten_color(main_color, 0.15)

        title_text = "Size:"
        bbox = font_mid.getbbox(title_text)
        title_w, title_h = bbox[2]-bbox[0], bbox[3]-bbox[1]

        line_spacing = 10
        sizes_heights = [font_mid.getbbox(s)[3]-font_mid.getbbox(s)[1] for s in sizes]
        total_text_h = title_h + sum(sizes_heights) + line_spacing*(len(sizes)-1)

        rect_h = total_text_h + 20 + 20 + 40
        rect_x2 = rect_x1 + rect_w
        rect_y2 = rect_y1 + rect_h

        draw.rounded_rectangle([rect_x1, rect_y1, rect_x2, rect_y2],
                               radius=15, fill=rect_color)

        title_x = rect_x1 + (rect_w - title_w)//2
        title_y = rect_y1 + 20
        draw.text((title_x, title_y), title_text, fill=second_color, font=font_mid)

        current_y = title_y + title_h + 20
        for size in sizes:
            bbox = font_mid.getbbox(size)
            size_w, size_h = bbox[2]-bbox[0], bbox[3]-bbox[1]
            size_x = rect_x1 + (rect_w - size_w)//2
            draw.text((size_x, current_y), size, fill=second_color, font=font_mid)
            current_y += size_h + line_spacing

    # --- Footer text ---
    rand_num = random.randint(100, 999)
    footer_text = f"برای اطلاعات بیشتر، {rand_num} رو دایرکت کن"
    temp_img = Image.new("RGBA", (W, H), (255, 255, 255, 0))
    temp_draw = ImageDraw.Draw(temp_img)
    bbox = font_mid.getbbox(footer_text)
    temp_draw.text((10, 1370), footer_text, fill=rect_color, font=font_fid)
    rotated_text = temp_img.rotate(-31, expand=True)
    canvas.paste(rotated_text, (0, 0), rotated_text)

    return canvas
