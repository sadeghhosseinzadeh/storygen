from PIL import Image, ImageDraw, ImageFont
import random
from PIL import ImageFilter
from storygen.utils import lighten_color, load_font

def template_1(shoe_img, main_color, second_color, model_name, sizes):
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

    # 1. Big NIKE text at the top (centered horizontally)
    nike_text = "NIKE"
    bbox = font_big.getbbox(nike_text)
    nike_w = bbox[2] - bbox[0]
    nike_x = (W - nike_w) // 2
    draw.text((nike_x, 240), nike_text, fill=second_color, font=font_big)

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
    
    # Duplicate shoe as RGBA
    shadow = shoe_resized.convert("RGBA")
    # Tint it black with some transparency
    shadow_data = shadow.getdata()
    new_data = []
    for item in shadow_data:
        # keep alpha channel, but make it dark
        new_data.append((0, 0, 0, int(item[3] * 0.5)))  # 40% opacity
    shadow.putdata(new_data)

    # Blur the shadow to make it soft
    shadow = shadow.filter(ImageFilter.GaussianBlur(10))

    # Offset the shadow slightly (down and right)
    shadow_x = x + 5
    shadow_y = y + 20

    # Paste shadow first
    canvas.paste(shadow, (shadow_x, shadow_y), shadow)

    # Paste shoe on top
    canvas.paste(shoe_resized, (x, y), shoe_resized)

    # 5. Sizes inside a rounded rectangle
    if sizes:
      # Rectangle width fixed
      rect_w = 350
      rect_x1 = 60
      rect_y1 = y + shoe_resized.size[1] + 40

      rect_color = lighten_color(main_color, 0.15)
      corner_radius = 15

      # Title "Sizes:"
      title_text = "Sizes:"
      bbox = font_mid.getbbox(title_text)
      title_w, title_h = bbox[2] - bbox[0], bbox[3] - bbox[1]

      # Each size line height
      line_spacing = 10
      sizes_heights = []
      for size in sizes:
          bbox = font_mid.getbbox(size)
          size_h = bbox[3] - bbox[1]
          sizes_heights.append(size_h)

      # Total text height = title + all sizes + spacing
      total_text_h = title_h + sum(sizes_heights) + line_spacing * (len(sizes) - 1)

      # Margin around text
      margin_top = 20
      margin_bottom = 20
      margin_sides = 20

      # Rectangle height = text height + margins
      rect_h = total_text_h + margin_top + margin_bottom + 40  # extra padding for title spacing
      rect_x2 = rect_x1 + rect_w
      rect_y2 = rect_y1 + rect_h

      # Draw rounded rectangle
      draw.rounded_rectangle([rect_x1, rect_y1, rect_x2, rect_y2],
                            radius=corner_radius, fill=rect_color)

      # Draw title centered
      title_x = rect_x1 + (rect_w - title_w) // 2
      title_y = rect_y1 + margin_top
      draw.text((title_x, title_y), title_text, fill=text_color, font=font_mid)

      # Draw sizes in column
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

    # Temporary transparent image for rotated text
    temp_img = Image.new("RGBA", (W, H), (255, 255, 255, 0))
    temp_draw = ImageDraw.Draw(temp_img)

    bbox = font_mid.getbbox(footer_text)
    text_w, text_h = bbox[2] - bbox[0], bbox[3] - bbox[1]

    # Position: centered under shoe
    text_x =  10
    text_y =  1370

    temp_draw.text((text_x, text_y), footer_text, fill=rect_color, font=font_fid)

    # Rotate text by same slope as shoe (-31 degrees)
    rotated_text = temp_img.rotate(-31, expand=True)

    # Paste rotated text back
    canvas.paste(rotated_text, (0, 0), rotated_text)

    return canvas
