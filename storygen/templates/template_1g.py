from PIL import Image, ImageDraw, ImageFont
import cairo
import random
import numpy as np
from storygen.utils import lighten_color, draw_text, load_font, place_shoe, remove_background, extract_colors


def prepare_shoe(photo, angle=-31, baseline_y=700, max_size=(750,600)):
    # 1. Remove background
    shoe = remove_background(photo)
    shoe = shoe.convert("RGBA")

    # 2. Crop tightly
    bbox = shoe.getbbox()
    shoe = shoe.crop(bbox)

    # 3. Resize to fit max_size
    w, h = shoe.size
    ratio = min(max_size[0]/w, max_size[1]/h)
    shoe = shoe.resize((int(w*ratio), int(h*ratio)), Image.LANCZOS)

    # 4. Rotate
    shoe = shoe.rotate(angle, expand=True)

    # 5. Detect bottom-most non-transparent pixel
    data = np.array(shoe)
    alpha = data[:,:,3]
    ys, xs = np.where(alpha > 0)
    bottom_y = ys.max()

    # 6. Shift shoe so bottom_y aligns with baseline_y
    offset_y = baseline_y - bottom_y

    return shoe, offset_y



def template_1g(photo_1, model_name, sizes, shop_name_en, brand):
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
    font_brand = load_font("Segoe.UI.Semibold_p30download.com.ttf", 55)

    text_color = main_color

    # --- 1. Big brand name text with limit ---
    brand_text = brand.upper()
    
    font_size = 300
    font_big = load_font("Segoe.UI.Bold_p30download.com.ttf", font_size)
    
    bbox = font_big.getbbox(brand_text)
    brand_w = bbox[2] - bbox[0]
    
    max_width = 900
    
    while brand_w > max_width and font_size > 50:
        font_size -= 10
        font_big = load_font("Segoe.UI.Bold_p30download.com.ttf", font_size)
        bbox = font_big.getbbox(brand_text)
        brand_w = bbox[2] - bbox[0]
    
    brand_x = (W - brand_w) // 2
    draw.text((brand_x, 240), brand_text, fill=second_color, font=font_big)

    # 2. Model name
    bbox = font_bid.getbbox(model_name)
    model_w = bbox[2] - bbox[0]
    model_x = (W - model_w) // 2
    draw.text((model_x, 570), model_name, fill=second_color, font=font_bid)

    # 2.5 shop name
    bbox = font_bid.getbbox(shop_name_en)
    shop_name_en_w = bbox[2] - bbox[0]
    shop_name_en_x = (W - shop_name_en_w) // 2
    draw.text((shop_name_en_x, 645), shop_name_en, fill=second_color, font=font_brand)

    # 3. Bottom polygon
    bottom_shape_points = [(0, H), (W, H), (W, H - 300), (0, H - 950)]
    draw.polygon(bottom_shape_points, fill=second_color)

    # 4. Shoe photo (NEW BASELINE SYSTEM)
    shoe_img, offset_y = prepare_shoe(photo_1, baseline_y=1400)

    # Center horizontally
    shoe_x = (W - shoe_img.width) // 2

    # Paste shoe aligned by bottom pixel
    canvas.paste(shoe_img, (shoe_x, offset_y), shoe_img)

    # 5. Sizes box
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

    # 6. Footer text
    rand_num = random.randint(100, 999)
    footer_text = f"برای اطلاعات بیشتر، {rand_num} رو دایرکت کن"
    temp_img = Image.new("RGBA", (W, H), (255, 255, 255, 0))
    temp_draw = ImageDraw.Draw(temp_img)
    bbox = font_mid.getbbox(footer_text)
    temp_draw.text((10, 1370), footer_text, fill=rect_color, font=font_fid)
    rotated_text = temp_img.rotate(-31, expand=True)
    canvas.paste(rotated_text, (0, 0), rotated_text)

    return canvas
