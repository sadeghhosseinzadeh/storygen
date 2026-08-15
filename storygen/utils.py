# --- CORE FUNCTIONS ---
from importlib.resources import files
from rembg import remove
from io import BytesIO
import numpy as np
from sklearn.cluster import KMeans
from PIL import Image, ImageFont
import colorsys
import cairosvg
import io
import cairo

BRAND_CONFIG = {
    "adidas": "brands/addidas-1.svg",
    "nike": "brands/nike-1.svg",
    "newbalance": "brands/new balance-1.svg",
}


# 1. Remove background
def remove_background(path: str, margin: int = 50):
    # Step 1: Remove background
    with open(path, "rb") as f:
        input_bytes = f.read()
    output_bytes = remove(input_bytes)
    img = Image.open(BytesIO(output_bytes)).convert("RGBA")

    # Step 2: Get bounding box of non-transparent pixels
    bbox = img.getbbox()
    if bbox:
        x1, y1, x2, y2 = bbox

        # Step 3: Expand bounding box by margin
        x1 = max(0, x1 - margin)
        y1 = max(0, y1 - margin)
        x2 = min(img.width, x2 + margin)
        y2 = min(img.height, y2 + margin)

        # Step 4: Crop to expanded bounding box
        img = img.crop((x1, y1, x2, y2))

    return img
# 2. Extract main + secondary colors
def extract_colors(img: Image.Image):
    img = img.convert("RGBA")
    arr = np.array(img)
    alpha = arr[:, :, 3]
    mask = alpha > 0
    pixels = arr[mask][:, :3]

    kmeans = KMeans(n_clusters=3, n_init=5)
    kmeans.fit(pixels)

    centers = kmeans.cluster_centers_.astype(int)
    labels, counts = np.unique(kmeans.labels_, return_counts=True)
    idx = np.argsort(-counts)

    main = tuple(int(c) for c in centers[idx[0]])
    second = tuple(int(c) for c in centers[idx[1]])
    return main, second

# 3. Lighten color
def lighten_color(color, strength=0.15):
    return tuple(int(c * strength + 255 * (1 - strength)) for c in color)

# 4. Darken color
def darken_color(color, factor):
    r, g, b = color
    return (
        int(r * (1-factor)),
        int(g * (1-factor)),
        int(b * (1-factor)))

# 5. Adjust saturation
def adjust_saturation(color, factor):
    r, g, b = [c/255.0 for c in color]
    h, l, s = colorsys.rgb_to_hls(r, g, b)
    s = max(0.0, min(1.0, s * factor))
    r2, g2, b2 = colorsys.hls_to_rgb(h, l, s)
    return (int(r2*255), int(g2*255), int(b2*255))

# 6. Load font (LOCAL version for Colab)
def load_font(name: str, size: int):
    """Load a font from the bundled fonts folder."""
    font_path = files("storygen.fonts").joinpath(name)
    return ImageFont.truetype(str(font_path), size)

# 7. add brand logo
def add_brand_logo(canvas, brand, mode=0, opacity=128, color=(0,0,0), pos=None, max_size=(400,400)):
    W, H = canvas.size
    brand = brand.lower()
    logo_path = BRAND_CONFIG.get(brand)

    if mode == 0 and logo_path:
        # Convert SVG to PNG at target size
        if logo_path.endswith(".svg"):
            png_bytes = cairosvg.svg2png(url=logo_path,
                                         output_width=max_size[0],
                                         output_height=max_size[1])
            logo_img = Image.open(io.BytesIO(png_bytes)).convert("RGBA")
        else:
            logo_img = Image.open(logo_path).convert("RGBA")

        # Resize to fit max_size
        lw, lh = logo_img.size
        ratio = min(max_size[0]/lw, max_size[1]/lh)
        logo_img = logo_img.resize((int(lw*ratio), int(lh*ratio)))

        # Auto-center if pos not provided
        if pos is None:
            pos_x = (W - logo_img.size[0]) // 2
            pos_y = (H - logo_img.size[1]) // 2 - 65
            pos = (pos_x, pos_y)

        # Tint using alpha mask
        r, g, b = color
        colored_logo = Image.new("RGBA", logo_img.size, (r, g, b, opacity))
        logo_img = Image.composite(colored_logo,
                                   Image.new("RGBA", logo_img.size, (0,0,0,0)),
                                   logo_img)

        # Paste onto canvas
        canvas.paste(logo_img, pos, logo_img)

    else:
        # Fallback: text overlay
        font_logo = load_font("Segoe.UI_p30download.com.ttf", 220)
        bbox = font_logo.getbbox(brand.upper())
        logo_w = bbox[2] - bbox[0]
        logo_h = bbox[3] - bbox[1]

        # Resize text if too big
        if logo_w > max_size[0]:
            scale = max_size[0]/logo_w
            font_logo = load_font("Segoe.UI_p30download.com.ttf", int(220*scale))

        # Auto-center text if pos not provided
        if pos is None:
            pos_x = (W - logo_w) // 2
            pos_y = (H - logo_h) // 2
            pos = (pos_x, pos_y)

        temp_logo = Image.new("RGBA", canvas.size, (255,255,255,0))
        temp_draw = ImageDraw.Draw(temp_logo)
        temp_draw.text(pos, brand.upper(),
                       fill=(color[0], color[1], color[2], opacity),
                       font=font_logo)
        canvas.paste(temp_logo, (0,0), temp_logo)


# 8. place shoe
def place_shoe(canvas, img, pos=None, max_size=(800,600), angle=0,
               center_x=True, center_y=False, shadow=True):
    """
    Place a shoe image onto the canvas.
    - canvas: PIL Image (background/template)
    - img: PIL Image (shoe, background removed)
    - pos: (x,y) top-left position. If None, auto-centers based on flags.
    - max_size: (max_w, max_h) bounding box for shoe
    - angle: rotation in degrees (positive = clockwise, negative = counter-clockwise)
    - center_x: if True, auto-center horizontally
    - center_y: if True, auto-center vertically
    """

    sw, sh = img.size
    max_w, max_h = max_size

    # Compute scale ratio
    ratio = min(max_w/sw, max_h/sh)
    if ratio > 1:
        ratio = min(max_w/sw, max_h/sh)

    new_w, new_h = int(sw * ratio), int(sh * ratio)
    shoe_resized = img.resize((new_w, new_h), Image.LANCZOS)

    # Rotate around center
    if angle != 0:
        shoe_resized = shoe_resized.rotate(angle, expand=True)

    # Auto-center logic
    W, H = canvas.size
    if pos is None:
        pos_x = (W - shoe_resized.size[0]) // 2 if center_x else 0
        pos_y = (H - shoe_resized.size[1]) // 2 if center_y else 0
    else:
        pos_x, pos_y = pos
        if center_x:
            pos_x = (W - shoe_resized.size[0]) // 2
        if center_y:
            pos_y = (H - shoe_resized.size[1]) // 2

    # --- SHADOW (same style as template_1) ---
    if shadow:
        sh_img = shoe_resized.convert("RGBA")

        # Reduce alpha → 50% shadow
        shadow_data = [(0,0,0,int(px[3]*0.5)) for px in sh_img.getdata()]
        sh_img.putdata(shadow_data)

        # Blur shadow
        sh_img = sh_img.filter(ImageFilter.GaussianBlur(10))

        # Offset shadow slightly
        canvas.paste(sh_img, (pos_x + 5, pos_y + 20), sh_img)

    # --- Paste shoe ---
    canvas.paste(shoe_resized, (pos_x, pos_y), shoe_resized)

    return canvas


# 9. draw trapezoid
def draw_trapezoid(ctx, x_left, y_top, x_right, y_top_right, y_bottom_left, y_bottom_right, color, radius=77):
    """
    Draws a trapezoid with rounded corners.
    Parameters:
        ctx: Cairo context
        x_left, y_top: top-left corner
        x_right: right x coordinate
        y_top_right: top y for right side
        y_bottom_left: bottom y for left side
        y_bottom_right: bottom y for right side
        color: tuple (r,g,b) in 0-1 range
        radius: corner radius
    """
    ctx.set_source_rgb(*color)

    # Start top-left
    ctx.move_to(x_left+radius, y_top)

    # Top edge
    ctx.line_to(x_right-radius, y_top_right)
    ctx.arc(x_right-radius, y_top_right+radius, radius, -0.5*3.14, 0)

    # Right edge
    ctx.line_to(x_right, y_bottom_right-radius)
    ctx.arc(x_right-radius, y_bottom_right-radius, radius, 0, 0.5*3.14)

    # Bottom edge (slanted)
    ctx.line_to(x_left+radius, y_bottom_left)
    ctx.arc(x_left+radius, y_bottom_left-radius, radius, 0.5*3.14, 3.14)

    # Left edge
    ctx.line_to(x_left, y_top+radius)
    ctx.arc(x_left+radius, y_top+radius, radius, 3.14, 1.5*3.14)

    ctx.close_path()
    ctx.fill()


# 10. Add user logo
def add_user_logo(canvas, logo_path=None,
                  pos=(None, None), max_size=(200,200),
                  center_x=False, center_y=False):
    """
    Add a user logo PNG/SVG from the assets folder.
    If logo_path is None, skip.
    """
    if not logo_path:
        return canvas

    # Open logo (handle PNG or SVG)
    if str(logo_path).lower().endswith(".svg"):
        import cairosvg
        # Convert SVG to PNG in memory
        png_data = cairosvg.svg2png(url=str(logo_path))
        from PIL import Image
        import io
        logo = Image.open(io.BytesIO(png_data)).convert("RGBA")
    else:
        from PIL import Image
        logo = Image.open(logo_path).convert("RGBA")

    # Resize to fit max_size
    lw, lh = logo.size
    max_w, max_h = max_size
    ratio = min(max_w/lw, max_h/lh)
    new_w, new_h = int(lw * ratio), int(lh * ratio)
    logo_resized = logo.resize((new_w, new_h), Image.LANCZOS)

    # Canvas size
    W, H = canvas.size
    pos_x, pos_y = pos

    # Auto-center logic
    if pos_x is None:
        pos_x = (W - new_w) // 2
    if pos_y is None:
        pos_y = (H - new_h) // 2
    if center_x:
        pos_x = (W - new_w) // 2
    if center_y:
        pos_y = (H - new_h) // 2

    # Paste
    canvas.paste(logo_resized, (pos_x, pos_y), logo_resized)
    return canvas

# 11. Draw text
def draw_text(canvas, text,
                   font_path_eng, font_size_eng,
                   font_path_per, font_size_per,
                   pos=(None, None), rotation=0, fill=(0,0,0),
                   spacing=20, padding=10):
    """
    Draw shop name text with rotation, auto-centering, language detection,
    line spacing, and padding.
    - canvas: PIL Image
    - text: shop name string (can contain '\n' for multiple lines)
    - font_path_eng: path to English font
    - font_size_eng: font size for English text
    - font_path_per: path to Persian font
    - font_size_per: font size for Persian text
    - pos: (x,y) coordinates; use None for auto-centering
    - rotation: rotation angle in degrees (e.g. 90, 270)
    - fill: text color (default black)
    - spacing: extra pixels between lines
    - padding: extra pixels around text box (top/bottom/left/right)
    """

    # Detect Persian vs English
    if any('\u0600' <= ch <= '\u06FF' for ch in text):
        font = ImageFont.truetype(font_path_per, font_size_per)
    else:
        font = ImageFont.truetype(font_path_eng, font_size_eng)

    # Split into lines
    lines = text.split("\n")

    # Measure width and height
    line_widths = [font.getbbox(line)[2] - font.getbbox(line)[0] for line in lines]
    line_heights = [font.getbbox(line)[3] - font.getbbox(line)[1] for line in lines]

    text_w = max(line_widths) + 2*padding
    text_h = sum(line_heights) + spacing * (len(lines)-1) + 2*padding

    # Transparent image for text
    text_img = Image.new("RGBA", (text_w, text_h), (0,0,0,0))
    text_draw = ImageDraw.Draw(text_img)

    # Draw each line with spacing and padding
    current_y = padding
    for line in lines:
        text_draw.text((padding, current_y), line, font=font, fill=fill)
        current_y += (font.getbbox(line)[3] - font.getbbox(line)[1]) + spacing

    # Rotate
    rotated_text = text_img.rotate(rotation, expand=True)

    # Position logic
    W, H = canvas.size
    rx, ry = rotated_text.size
    x, y = pos

    if x is None:  # auto-center horizontally
        x = (W - rx)//2
    if y is None:  # auto-center vertically
        y = (H - ry)//2

    # Paste with transparency
    canvas.paste(rotated_text, (x,y), rotated_text)
    return canvas
