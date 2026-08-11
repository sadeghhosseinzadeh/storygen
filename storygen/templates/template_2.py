from PIL import Image, ImageDraw, ImageFont, ImageFilter
import random
from storygen.utils import lighten_color, load_font

def template_2(shoe_img, main_color, second_color, brand_name, model_name, sizes):
    W, H = 1080, 1920

    # Background: 15% main color blended with white
    bg = lighten_color(main_color, 0.15)
    canvas = Image.new("RGB", (W, H), bg)
    draw = ImageDraw.Draw(canvas)

    # Fonts
    font_big = load_font("Segoe.UI.Bold_p30download.com.ttf", 300)
    font_mid = load_font("Segoe.UI_p30download.com.ttf", 35)
    font_fid = load_font("Segoe.UI_p30download.com.ttf", 43)
    font_bid = load_font("Segoe.UI_p30download.com.ttf", 55)

    text_color = main_color

    # 1. Big brand text at the top (centered horizontally)
    brand_text = brand_name.upper()
    bbox = font_big.getbbox(brand_text)
    brand_w = bbox[2] - bbox[0]
    brand_x = (W - brand_w) // 2
    draw.text((brand_x, 240), brand_text, fill=second_color, font=font_big)

    # 2. Model name below shoe (centered horizontally)
    bbox = font_bid.getbbox(model_name)
    model_w = bbox[2] - bbox[0]
    model_x = (W - model_w) // 2
    draw.text((model_x, 640), model_name, fill=second_color, font=font_bid)

    # 3. Bottom polygon (background shape)
    bottom_shape_points = [
        (0, H), (W, H),
        (W, H - 300),
        (0, H - 950)
    ]
    draw.polygon(bottom_shape_points, fill=second_color)

    # 4. Rotate and enlarge shoe
    shoe_rotated = shoe_img.rotate(-31, expand=True)
    max_w, max_h = 1000, 1000
    sw, sh = shoe_rotated.size
    ratio = min(max_w / sw, max_h / sh)
    shoe_resized = shoe_rotated.resize((int(sw * ratio), int(sh * ratio)))

    x = (W - shoe_resized.size[0]) // 2 + 60
    y = (H - shoe_resized.size[1]) // 2 + 100
    
    # Shadow
    shadow = shoe_resized.convert("RGBA")
    shadow_data = shadow.getdata()
    new_data = []
    for item in shadow_data:
        new_data.append((0, 0, 0, int(item[3] * 0.5)))  # 40% opacity
    shadow.putdata(new_data)
    shadow = shadow.filter(ImageFilter.GaussianBlur(10))
    shadow_x, shadow_y = x + 5, y + 20
    canvas.paste(shadow, (shadow_x, shadow_y), shadow)

    # Paste shoe on top
    canvas.paste(shoe_resized, (x, y), shoe_resized)

    # 5. Sizes inside a rounded rectangle
    if sizes:
        rect_w = 350
        rect_x1 = 60
        rect_y1 = y + shoe_resized.size[1] + 40
        rect_color = lighten_color(main_color, 0.15)
        corner_radius = 15

        title_text = "Sizes:"
        bbox = font_mid.getbbox(title_text)
        title_w, title_h = bbox[2] - bbox[0], bbox[3] - bbox[1]

        line_spacing = 10
        sizes_heights = [font_mid.getbbox(size)[3] - font_mid.getbbox(size)[1] for size in sizes]
        total_text_h = title_h + sum(sizes_heights) + line_spacing * (len(sizes) - 1)

        margin_top, margin_bottom, margin_sides = 20, 20, 20
        rect_h = total_text_h + margin_top + margin_bottom + 40
        rect_x2, rect_y2 = rect_x1 + rect_w, rect_y1 + rect_h

        draw.rounded_rectangle([rect_x1, rect_y1, rect_x2, rect_y2],
                               radius=corner_radius, fill=rect_color)

        title_x = rect_x1 + (rect_w - title_w) // 2
        title_y = rect_y1 + margin_top
        draw.text((title_x, title_y), title_text, fill=text_color, font=font_mid)

        current_y = title_y + title_h + 20
        for size in sizes:
            bbox = font_mid.getbbox(size)
            size_w, size_h = bbox[2] - bbox[0], bbox[3] - bbox[1]
            size_x = rect_x1 + (rect_w - size_w) // 2
            draw.text((size_x, current_y), size, fill=text_color, font=font_mid)
            current_y += size_h + line_spacing

    # 6. Footer text under shoe, rotated with same slope
    rand_num = random.randint(100, 999)
    footer_text = f"For more info, direct {rand_num}"

    temp_img = Image.new("RGBA", (W, H), (255, 255, 255, 0))
    temp_draw = ImageDraw.Draw(temp_img)
    temp_draw.text((10, 1370), footer_text, fill=rect_color, font=font_fid)
    rotated_text = temp_img.rotate(-31, expand=True)
    canvas.paste(rotated_text, (0, 0), rotated_text)

    return canvas
