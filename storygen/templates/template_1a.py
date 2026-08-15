from PIL import Image, ImageDraw, ImageFont
import random
from storygen.utils import lighten_color, load_font, place_shoe, remove_background, extract_colors

def template_1a(photo_1, model_name, sizes):
    W, H = 1080, 1920

    # Background: 15% main color blended with white
    photo_1_rem = remove_background(photo_1)
    main_color, second_color = extract_colors(photo_1_rem)
    bg = lighten_color(main_color, 0.15)
    canvas = Image.new("RGB", (W, H), bg)
    draw = ImageDraw.Draw(canvas)

    # Fonts
    font_big = load_font("Segoe.UI.Bold_p30download.com.ttf", 300)
    font_mid = load_font("Segoe.UI_p30download.com.ttf", 35)
    font_fid = load_font("A Mitra 04.ttf", 38)
    font_bid = load_font("Segoe.UI_p30download.com.ttf", 55)

    text_color = main_color

    # 1. Big NIKE text
    nike_text = "NIKE"
    bbox = font_big.getbbox(nike_text)
    nike_w = bbox[2] - bbox[0]
    nike_x = (W - nike_w) // 2
    draw.text((nike_x, 240), nike_text, fill=second_color, font=font_big)

    # 2. Model name
    bbox = font_bid.getbbox(model_name)
    model_w = bbox[2] - bbox[0]
    model_x = (W - model_w) // 2
    draw.text((model_x, 640), model_name, fill=second_color, font=font_bid)

    # 3. Bottom polygon
    bottom_shape_points = [(0, H), (W, H), (W, H - 300), (0, H - 950)]
    draw.polygon(bottom_shape_points, fill=second_color)

    # 4. Shoe photo (background removed + placed)
    place_shoe(canvas, photo_1_rem,
               pos=(None, (H - 1000)//2 + 100),  # same vertical offset logic
               max_size=(750, 750),
               angle=-31,
               center_x=True)

    # 5. Sizes box (unchanged)
    if sizes:
        rect_w = 350
        rect_x1 = 60
        rect_y1 = y + shoe_resized.size[1] + 40
        rect_color = main_color

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
        draw.text((title_x, title_y), title_text, fill=main_color, font=font_mid)

        current_y = title_y + title_h + 20
        for size in sizes:
            bbox = font_mid.getbbox(size)
            size_w, size_h = bbox[2]-bbox[0], bbox[3]-bbox[1]
            size_x = rect_x1 + (rect_w - size_w)//2
            draw.text((size_x, current_y), size, fill=main_color, font=font_mid)
            current_y += size_h + line_spacing

    # 6. Footer text (unchanged)
    rand_num = random.randint(100, 999)
    footer_text = f"برای اطلاعات بیشتر، {rand_num} رو دایرکت کن"
    temp_img = Image.new("RGBA", (W, H), (255, 255, 255, 0))
    temp_draw = ImageDraw.Draw(temp_img)
    bbox = font_mid.getbbox(footer_text)
    temp_draw.text((10, 1370), footer_text, fill=rect_color, font=font_fid)
    rotated_text = temp_img.rotate(-31, expand=True)
    canvas.paste(rotated_text, (0, 0), rotated_text)

    return canvas
