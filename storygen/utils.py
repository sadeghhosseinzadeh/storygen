# --- CORE FUNCTIONS ---
from importlib.resources import files
from rembg import remove
from io import BytesIO
import numpy as np
from sklearn.cluster import KMeans
from PIL import Image, ImageFont, ImageDraw, ImageFilter
import colorsys
import cairosvg
import io
import cairo
from pathlib import Path
import storygen


def to_english_digits(s):
    persian_digits = "۰۱۲۳۴۵۶۷۸۹"
    english_digits = "0123456789"
    table = str.maketrans(persian_digits, english_digits)
    return s.translate(table)
    
# 1. Remove background 
def remove_background(path: str, pad: int = 50):
    # Step 1: Remove background
    with open(path, "rb") as f:
        input_bytes = f.read()
    output_bytes = remove(input_bytes)
    img = Image.open(BytesIO(output_bytes)).convert("RGBA")

    # Step 2: Crop tightly to the shoe edges (margin = 0)
    bbox = img.getbbox()
    if bbox:
        img = img.crop(bbox)

    # Step 3: Add transparent padding around all sides
    new_w = img.width + pad * 2
    new_h = img.height + pad * 2
    padded = Image.new("RGBA", (new_w, new_h), (0, 0, 0, 0))
    padded.paste(img, (pad, pad), img)

    return padded
    
# 2. Extract main + secondary colors
def extract_colors(img: Image.Image, n_clusters=4, include_saturated=False):
    img = img.convert("RGBA")
    arr = np.array(img)
    alpha = arr[:, :, 3]
    mask = alpha > 0
    pixels = arr[mask][:, :3]

    # Cluster colors
    kmeans = KMeans(n_clusters=n_clusters, n_init=5)
    kmeans.fit(pixels)
    centers = kmeans.cluster_centers_.astype(int)
    labels, counts = np.unique(kmeans.labels_, return_counts=True)
    idx = np.argsort(-counts)

    # Most frequent colors
    main = tuple(int(c) for c in centers[idx[0]])
    second = tuple(int(c) for c in centers[idx[1]])

    # Find most saturated color
    def saturation(c):
        r, g, b = [x/255.0 for x in c]
        h, l, s = colorsys.rgb_to_hls(r, g, b)
        return s

    sat_idx = max(range(len(centers)), key=lambda i: saturation(centers[i]))
    saturated = tuple(int(c) for c in centers[sat_idx])

    if include_saturated:
        return main, second, saturated
    else:
        return main, second

# 2.5 protect color
def protect_color(color, sat_boost=1.4, darken_factor=0.25, threshold=220):
    r, g, b = color
    if r > threshold and g > threshold and b > threshold:
        color = (
            int(r * (1 - darken_factor)),
            int(g * (1 - darken_factor)),
            int(b * (1 - darken_factor))
        )
        color = adjust_saturation(color, sat_boost)
    return color

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

# 6. Load font 
def load_font(font_filename, size):
    try:
        # Try package resource first
        try:
            font_path = files("storygen.fonts").joinpath(font_filename)
        except:
            font_path = None

        # If resource lookup failed, fallback to direct path
        if not font_path or not Path(font_path).exists():
            package_root = Path(storygen.__file__).parent
            font_path = package_root / "fonts" / font_filename

        return ImageFont.truetype(str(font_path), size)

    except Exception as e:
        print(f"Warning: font {font_filename} not found or unreadable ({e}), using default")
        return ImageFont.load_default()

# 7. add brand logo
def add_brand_logo(canvas, brand, variant=1, mode=0, opacity=255, color=(0,0,0), pos=None, max_size=(400,400)):
    W, H = canvas.size
    brand = brand.lower()

    # --- Variant fallback logic ---
    requested_filename = f"{brand}-{variant}.svg"
    default_filename   = f"{brand}-1.svg"

    package_root = Path(storygen.__file__).parent
    requested_path = package_root / "brands" / requested_filename
    default_path   = package_root / "brands" / default_filename

    # If requested variant doesn't exist → use default variant 1
    if requested_path.exists():
        logo_path = requested_path
    else:
        logo_path = default_path
    # -------------------------------

    if mode == 0 and logo_path.exists():
        if logo_path.suffix.lower() == ".svg":
            png_bytes = cairosvg.svg2png(url=str(logo_path),
                                         output_width=max_size[0],
                                         output_height=max_size[1])
            logo_img = Image.open(io.BytesIO(png_bytes)).convert("RGBA")
        else:
            logo_img = Image.open(logo_path).convert("RGBA")

        lw, lh = logo_img.size
        ratio = min(max_size[0]/lw, max_size[1]/lh)
        logo_img = logo_img.resize((int(lw*ratio), int(lh*ratio)))

        if pos is None:
            pos_x = (W - logo_img.size[0]) // 2
            pos_y = (H - logo_img.size[1]) // 2 - 65
            pos = (pos_x, pos_y)

        r, g, b = color
        colored_logo = Image.new("RGBA", logo_img.size, (r, g, b, opacity))
        logo_img = Image.composite(colored_logo,
                                   Image.new("RGBA", logo_img.size, (0,0,0,0)),
                                   logo_img)

        canvas.paste(logo_img, pos, logo_img)

    else:
        font_logo = load_font("Segoe.UI_p30download.com.ttf", 220)
        bbox = font_logo.getbbox(brand.upper())
        logo_w = bbox[2] - bbox[0]
        logo_h = bbox[3] - bbox[1]

        if logo_w > max_size[0]:
            scale = max_size[0]/logo_w
            font_logo = load_font("Segoe.UI_p30download.com.ttf", int(220*scale))

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
    Hybrid version:
    - If angle == 0 → old behavior (top-left anchor)
    - If angle != 0 → new behavior (bottom-middle anchor + stable rotation)
    """

    import numpy as np
    W, H = canvas.size

    # --- Resize shoe ---
    sw, sh = img.size
    max_w, max_h = max_size
    ratio = min(max_w/sw, max_h/sh)
    if ratio > 1:
        ratio = min(max_w/sw, max_h/sh)

    new_w, new_h = int(sw * ratio), int(sh * ratio)
    shoe = img.resize((new_w, new_h), Image.LANCZOS)

    # ============================================================
    #  MODE 1: OLD BEHAVIOR (angle == 0)
    # ============================================================
    if angle == 0:
        # Auto-center logic (old behavior)
        if pos is None:
            pos_x = (W - new_w) // 2 if center_x else 0
            pos_y = (H - new_h) // 2 if center_y else 0
        else:
            pos_x, pos_y = pos
            if center_x:
                pos_x = (W - new_w) // 2
            if center_y:
                pos_y = (H - new_h) // 2

        # --- SHADOW ---
        if shadow:
            sh_img = shoe.convert("RGBA")
            shadow_data = [(0,0,0,int(px[3]*0.5)) for px in sh_img.getdata()]
            sh_img.putdata(shadow_data)
            sh_img = sh_img.filter(ImageFilter.GaussianBlur(10))
            canvas.paste(sh_img, (pos_x + 5, pos_y + 20), sh_img)

        # Paste shoe
        canvas.paste(shoe, (pos_x, pos_y), shoe)
        return canvas

    # ============================================================
    #  MODE 2: NEW BEHAVIOR (angle != 0)
    # ============================================================

    # --- Find bottom-middle pixel ---
    arr = np.array(shoe)
    alpha = arr[:,:,3]

    ys, xs = np.where(alpha > 0)
    bottom_y = ys.max()
    xs_bottom = xs[ys == bottom_y]
    bottom_mid_x = int((xs_bottom.min() + xs_bottom.max()) / 2)

    # --- Determine target Y ---
    if pos is None:
        target_y = (H // 2) if center_y else (H // 2)
    else:
        _, target_y = pos

    # --- Initial placement BEFORE rotation ---
    pos_x = (W - new_w) // 2 if center_x else 0
    pos_y = target_y - bottom_y

    # --- Rotate AFTER placement ---
    rotated = shoe.rotate(angle, expand=True)
    rw, rh = rotated.size

    # Recompute bottom-middle after rotation
    arr2 = np.array(rotated)
    alpha2 = arr2[:,:,3]
    ys2, xs2 = np.where(alpha2 > 0)
    new_bottom_y = ys2.max()
    xs2_bottom = xs2[ys2 == new_bottom_y]
    new_bottom_mid_x = int((xs2_bottom.min() + xs2_bottom.max()) / 2)

    # Re-anchor bottom-middle to target_y
    pos_y = target_y - new_bottom_y

    # Re-center horizontally
    pos_x = (W - rw) // 2 if center_x else pos_x

    shoe = rotated

    # --- SHADOW ---
    if shadow:
        sh_img = shoe.convert("RGBA")
        shadow_data = [(0,0,0,int(px[3]*0.5)) for px in sh_img.getdata()]
        sh_img.putdata(shadow_data)
        sh_img = sh_img.filter(ImageFilter.GaussianBlur(10))
        canvas.paste(sh_img, (pos_x + 5, pos_y + 20), sh_img)

    # --- Paste shoe ---
    canvas.paste(shoe, (pos_x, pos_y), shoe)

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
                  center_x=False, center_y=False,
                  opacity=255): 
    """
    Add a user logo PNG/SVG from the assets folder.
    If logo_path is None or invalid, skip gracefully.
    Opacity: 0–255 (default 255 = fully opaque)
    """
    if not logo_path:
        return canvas

    try:
        # Handle SVG → convert to PNG in memory
        if str(logo_path).lower().endswith(".svg"):
            png_data = cairosvg.svg2png(url=str(logo_path))
            logo = Image.open(io.BytesIO(png_data)).convert("RGBA")
        else:
            logo = Image.open(logo_path).convert("RGBA")
    except Exception as e:
        print(f"Warning: could not load logo {logo_path}: {e}")
        return canvas

    # Resize to fit max_size
    lw, lh = logo.size
    max_w, max_h = max_size
    ratio = min(max_w/lw, max_h/lh)
    new_w, new_h = int(lw * ratio), int(lh * ratio)
    logo_resized = logo.resize((new_w, new_h), Image.LANCZOS)

    # Apply opacity (ONLY CHANGE)
    if opacity < 255:
        alpha = logo_resized.split()[3]
        alpha = alpha.point(lambda p: p * (opacity / 255.0))
        logo_resized.putalpha(alpha)

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
              spacing=20,
              padding_left=0,
              padding_right=0,
              padding_top=0,
              padding_bottom=0):
    """
    Draw shop name text with rotation, auto-centering, language detection,
    line spacing, and SEPARATE padding for each side.
    """

    # Resolve fonts relative to storygen/fonts
    font_path_eng = files("storygen.fonts").joinpath(font_path_eng)
    font_path_per = files("storygen.fonts").joinpath(font_path_per)

    # Detect Persian vs English
    try:
        if any('\u0600' <= ch <= '\u06FF' for ch in text):
            font = ImageFont.truetype(str(font_path_per), font_size_per)
        else:
            font = ImageFont.truetype(str(font_path_eng), font_size_eng)
    except OSError:
        print("Warning: font not found, using default")
        font = ImageFont.load_default()

    # Split into lines
    lines = text.split("\n")

    # Measure width and height
    line_widths = [font.getbbox(line)[2] - font.getbbox(line)[0] for line in lines]
    line_heights = [font.getbbox(line)[3] - font.getbbox(line)[1] for line in lines]

    # Extra bottom offset to prevent clipping
    BOTTOM_OFFSET = 12
    BASELINE_OFFSET = -4

    text_w = max(line_widths) + padding_left + padding_right
    text_h = sum(line_heights) + spacing * (len(lines)-1) + padding_top + padding_bottom + BOTTOM_OFFSET

    # Transparent image for text
    text_img = Image.new("RGBA", (text_w, text_h), (0,0,0,0))
    text_draw = ImageDraw.Draw(text_img)

    # Draw each line with spacing and padding
    current_y = padding_top + BASELINE_OFFSET
    for line in lines:
        text_draw.text((padding_left, current_y), line, font=font, fill=fill)
        current_y += (font.getbbox(line)[3] - font.getbbox(line)[1]) + spacing

    # Rotate
    rotated_text = text_img.rotate(rotation, expand=True)

    # Position logic
    W, H = canvas.size
    rx, ry = rotated_text.size
    x, y = pos

    if x is None:
        x = (W - rx)//2
    if y is None:
        y = (H - ry)//2

    canvas.paste(rotated_text, (x,y), rotated_text)
    return canvas


# 12. Draw sizes box
def draw_sizes_box(
    canvas,
    sizes,
    pos=None,                 
    show_box=True,
    box_color=None,
    box_radius=15,
    max_height=None,
    min_height=None,
    title_text="Size:",
    title_font_path="Segoe.UI.Semibold_p30download.com.ttf",
    title_font_size=60,
    title_color=(220,0,0),
    size_font_path="Segoe.UI.Semibold_p30download.com.ttf",
    size_font_size=45,
    size_color=(0,0,0),
    padding_x=40,
    padding_y=30,
    spacing=10
):
    # Skip if no sizes
    if not sizes:
        return

    # Normalize sizes input
    if isinstance(sizes, str):
        sizes = [s.strip() for s in sizes.split(",") if s.strip()]

    draw = ImageDraw.Draw(canvas)
    W, H = canvas.size

    # Load fonts
    font_title = load_font(title_font_path, title_font_size)
    font_size = load_font(size_font_path, size_font_size)

    # Measure title
    bbox_title = font_title.getbbox(title_text)
    title_w = bbox_title[2] - bbox_title[0]
    title_h = bbox_title[3] - bbox_title[1]

    # Measure sizes
    size_heights = []
    size_widths = []
    for s in sizes:
        b = font_size.getbbox(s)
        size_widths.append(b[2] - b[0])
        size_heights.append(b[3] - b[1])

    total_sizes_h = sum(size_heights) + spacing * (len(sizes) - 1)

    # Total block size
    block_w = max(title_w, max(size_widths)) + padding_x * 2
    block_h = title_h + total_sizes_h + padding_y * 2

    # Apply height limits
    if max_height and block_h > max_height:
        block_h = max_height
    if min_height and block_h < min_height:
        block_h = min_height

    # Determine position
    if pos is None:
        center_x = W // 2
        center_y = H // 2
    else:
        center_x, center_y = pos

    # Top-left corner of block
    x1 = center_x - block_w // 2
    y1 = center_y - block_h // 2
    x2 = x1 + block_w
    y2 = y1 + block_h

    # Draw background box
    if show_box:
        if box_color is None:
            box_color = (240, 240, 240)  # default light gray
        draw.rounded_rectangle([x1, y1, x2, y2], radius=box_radius, fill=box_color)

    # Draw title
    title_x = center_x - title_w // 2
    title_y = y1 + padding_y
    draw.text((title_x, title_y), title_text, fill=title_color, font=font_title)

    # Draw sizes
    current_y = title_y + title_h + spacing
    for i, s in enumerate(sizes):
        b = font_size.getbbox(s)
        sw = b[2] - b[0]
        sh = b[3] - b[1]
        sx = center_x - sw // 2
        draw.text((sx, current_y), s, fill=size_color, font=font_size)
        current_y += sh + spacing


# 13.draw scaled text
def draw_scaled_text(
    draw,
    text,
    font_path,
    max_font_size,
    max_width,
    max_height,
    start_pos,
    fill,
    allow_multiline=True
):
    canvas_w, canvas_h = draw.im.size

    for size in range(max_font_size, 10, -2):
        font = load_font(font_path, size)

        # Measure full text
        bbox = font.getbbox(text)
        w = bbox[2] - bbox[0]
        h = bbox[3] - bbox[1]

        # --- SINGLE LINE MODE ---
        if not allow_multiline:
            if w <= max_width and h <= max_height:
                # Smart centering
                x = start_pos[0] if start_pos[0] is not None else (canvas_w - w) // 2
                y = start_pos[1] if start_pos[1] is not None else (canvas_h - h) // 2
                draw.text((x, y), text, fill=fill, font=font)
                return h, w, font
            else:
                continue

        # --- MULTILINE MODE ---
        words = text.split()

        if w <= max_width and h <= max_height:
            # Single line fits → compute total height
            lines = [text]
            total_h = h
            max_line_w = w

            # Extra safeguard: if single word still too wide, skip
            if len(words) == 1 and max_line_w > max_width:
                continue
        else:
            # Word wrapping
            lines = []
            line = ""
            for word in words:
                test = line + " " + word if line else word
                bbox = font.getbbox(test)
                if (bbox[2] - bbox[0]) <= max_width:
                    line = test
                else:
                    lines.append(line)
                    line = word
            if line:
                lines.append(line)

            # Compute total height
            total_h = sum(font.getbbox(l)[3] - font.getbbox(l)[1] for l in lines) \
                      + (len(lines)-1)*10

            if total_h > max_height:
                continue

            max_line_w = max(font.getbbox(l)[2] - font.getbbox(l)[0] for l in lines)

        # Final safeguard: reject if width still exceeds max
        if max_line_w > max_width:
            continue

        # Smart centering
        x = start_pos[0] if start_pos[0] is not None else (canvas_w - max_line_w) // 2
        y = start_pos[1] if start_pos[1] is not None else (canvas_h - total_h) // 2

        # Draw lines
        yy = y
        for l in lines:
            bbox = font.getbbox(l)
            lh = bbox[3] - bbox[1]
            draw.text((x, yy), l, fill=fill, font=font)
            yy += lh + 10

        return total_h, max_line_w, font

    return 0, 0, None




# detect shoe direction
def detect_shoe_direction(img):
    """
    Returns 'left' if the shoe is pointing left,
    Returns 'right' if the shoe is pointing right.
    """
    arr = np.array(img)
    alpha = arr[:,:,3]

    h, w = alpha.shape
    mid = w // 2

    left_pixels  = np.sum(alpha[:, :mid] > 0)
    right_pixels = np.sum(alpha[:, mid:] > 0)

    # Narrow side = front of shoe
    if left_pixels < right_pixels:
        return "left"
    else:
        return "right"



def draw_sizes_box3(
    canvas,
    sizes,
    pos=None,
    show_box=True,
    box_color=None,
    box_radius=15,

    # Size limits
    max_height=None,
    min_height=None,

    # Title
    title_text="Size:",
    title_font_path="Segoe.UI.Semibold_p30download.com.ttf",
    title_font_size=55,
    title_color=(220,0,0),

    # Sizes
    size_font_path="Segoe.UI.Semibold_p30download.com.ttf",
    size_font_size=45,
    size_color=(0,0,0),

    # Padding controls
    padding_left=40,
    padding_right=40,
    padding_top=30,
    padding_bottom=30,

    # Spacing controls
    gap_title_to_sizes=30,   # space under "Size:"
    spacing=10,              # space between sizes

    # Auto shrink settings
    max_sizes_before_shrink=7,
    min_size_font=30
):
    if not sizes:
        return

    # Normalize sizes input
    if isinstance(sizes, str):
        sizes = [s.strip() for s in sizes.split(",") if s.strip()]

    draw = ImageDraw.Draw(canvas)
    W, H = canvas.size

    # Load fonts
    font_title = load_font(title_font_path, title_font_size)
    font_size = load_font(size_font_path, size_font_size)

    # Baseline correction
    TITLE_OFFSET_Y = -6
    SIZE_OFFSET_Y = -4

    # Measure title
    bbox_title = font_title.getbbox(title_text)
    title_w = bbox_title[2] - bbox_title[0]
    title_h = bbox_title[3] - bbox_title[1]

    # Measure sizes
    def measure_sizes(font):
        heights = []
        widths = []
        for s in sizes:
            b = font.getbbox(s)
            widths.append(b[2] - b[0])
            heights.append(b[3] - b[1])
        return widths, heights

    size_widths, size_heights = measure_sizes(font_size)

    # Auto shrink if too many sizes
    if len(sizes) > max_sizes_before_shrink:
        while len(sizes) > max_sizes_before_shrink and size_font_size > min_size_font:
            size_font_size -= 2
            font_size = load_font(size_font_path, size_font_size)
            size_widths, size_heights = measure_sizes(font_size)

    # Total height
    total_sizes_h = sum(size_heights) + spacing * (len(sizes) - 1)

    block_w = max(title_w, max(size_widths)) + padding_left + padding_right
    block_h = (
        padding_top +
        title_h +
        gap_title_to_sizes +
        total_sizes_h +
        padding_bottom
    )

    # Apply height limits
    if max_height and block_h > max_height:
        block_h = max_height
    if min_height and block_h < min_height:
        block_h = min_height

    # Position
    if pos is None:
        center_x = W // 2
        center_y = H // 2
    else:
        center_x, center_y = pos

    x1 = center_x - block_w // 2
    y1 = center_y - block_h // 2
    x2 = x1 + block_w
    y2 = y1 + block_h

    # Draw box
    if show_box:
        if box_color is None:
            box_color = (240, 240, 240)
        draw.rounded_rectangle([x1, y1, x2, y2], radius=box_radius, fill=box_color)

    # Draw title
    title_x = x1 + (block_w - title_w) // 2
    title_y = y1 + padding_top + TITLE_OFFSET_Y
    draw.text((title_x, title_y), title_text, fill=title_color, font=font_title)

    # Draw sizes
    current_y = title_y + title_h + gap_title_to_sizes
    for s in sizes:
        b = font_size.getbbox(s)
        sw = b[2] - b[0]
        sh = b[3] - b[1]
        sx = x1 + (block_w - sw) // 2
        draw.text((sx, current_y + SIZE_OFFSET_Y), s, fill=size_color, font=font_size)
        current_y += sh + spacing



def place_shoe2(canvas, img, pos=None, max_size=(800,600),
               angle_left=20, angle_right=-20,
               center_x=True, center_y=False, shadow=True):
    """
    Smart version:
    - Detects shoe direction (left/right)
    - Uses angle_left for left-facing shoes
    - Uses angle_right for right-facing shoes
    """
    W, H = canvas.size

    # --- Resize shoe ---
    sw, sh = img.size
    max_w, max_h = max_size
    ratio = min(max_w/sw, max_h/sh)
    if ratio > 1:
        ratio = min(max_w/sw, max_h/sh)

    new_w, new_h = int(sw * ratio), int(sh * ratio)
    shoe = img.resize((new_w, new_h), Image.LANCZOS)

    # ============================================================
    #  AUTO DIRECTION DETECTION
    # ============================================================
    direction = detect_shoe_direction(shoe)

    if direction == "left":
        final_angle = angle_left
    else:
        final_angle = angle_right

    # ============================================================
    #  MODE 1: OLD BEHAVIOR (final_angle == 0)
    # ============================================================
    if final_angle == 0:
        if pos is None:
            pos_x = (W - new_w) // 2 if center_x else 0
            pos_y = (H - new_h) // 2 if center_y else 0
        else:
            pos_x, pos_y = pos
            if center_x:
                pos_x = (W - new_w) // 2
            if center_y:
                pos_y = (H - new_h) // 2

        if shadow:
            sh_img = shoe.convert("RGBA")
            shadow_data = [(0,0,0,int(px[3]*0.5)) for px in sh_img.getdata()]
            sh_img.putdata(shadow_data)
            sh_img = sh_img.filter(ImageFilter.GaussianBlur(10))
            canvas.paste(sh_img, (pos_x + 5, pos_y + 20), sh_img)

        canvas.paste(shoe, (pos_x, pos_y), shoe)
        return canvas

    # ============================================================
    #  MODE 2: NEW BEHAVIOR (final_angle != 0)
    # ============================================================

    # --- Find bottom-middle pixel ---
    arr = np.array(shoe)
    alpha = arr[:,:,3]

    ys, xs = np.where(alpha > 0)
    bottom_y = ys.max()
    xs_bottom = xs[ys == bottom_y]
    bottom_mid_x = int((xs_bottom.min() + xs_bottom.max()) / 2)

    # --- Determine target position ---
    if pos is None:
        pos_x = (W - new_w) // 2 if center_x else 0
        target_y = (H // 2) if center_y else (H // 2)
    else:
        user_x, target_y = pos
    
        if center_x:
            pos_x = (W - new_w) // 2
        else:
            pos_x = user_x

    
    # --- Initial placement BEFORE rotation ---
    pos_y = target_y - bottom_y

    # --- Rotate AFTER placement ---
    rotated = shoe.rotate(final_angle, expand=True)
    rw, rh = rotated.size

    # Recompute bottom-middle after rotation
    arr2 = np.array(rotated)
    alpha2 = arr2[:,:,3]
    ys2, xs2 = np.where(alpha2 > 0)
    new_bottom_y = ys2.max()
    xs2_bottom = xs2[ys2 == new_bottom_y]
    new_bottom_mid_x = int((xs2_bottom.min() + xs2_bottom.max()) / 2)

    # Re-anchor bottom-middle to target_y
    pos_y = target_y - new_bottom_y

    # Re-center horizontally only when requested
    if center_x:
        pos_x = (W - rw) // 2

    shoe = rotated

    # --- SHADOW ---
    if shadow:
        sh_img = shoe.convert("RGBA")
        shadow_data = [(0,0,0,int(px[3]*0.5)) for px in sh_img.getdata()]
        sh_img.putdata(shadow_data)
        sh_img = sh_img.filter(ImageFilter.GaussianBlur(10))
        canvas.paste(sh_img, (pos_x + 5, pos_y + 20), sh_img)

    # --- Paste shoe ---
    canvas.paste(shoe, (pos_x, pos_y), shoe)

    return canvas
