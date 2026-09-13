from PIL import ImageDraw, ImageFont
import colorsys
 
from storygen.utils import load_font, darken_color, lighten_color, adjust_saturation

# 1. size box grid 
def draw_sizes_grid(
    canvas,
    sizes,
    pos=(None, None),

    # Colors for alternating rows
    box_colors=((220,220,220), (180,180,180)),

    box_radius=12,

    # Grid limits
    max_rows=3,
    max_cols=4,
    max_sizes=12,   # hard limit

    # Auto shrink settings
    shrink_threshold=12,
    box_size=(160, 80),
    font_path="Segoe.UI.Semibold_p30download.com.ttf",
    font_size=40,

    # Text colors auto-detected
    dark_threshold=140,   # avg RGB < this → use white text
    light_threshold=200,  # avg RGB > this → use black text

    # Padding inside each box
    padding_left=10,
    padding_right=10,
    padding_top=5,
    padding_bottom=5,

    # Spacing between boxes
    h_spacing=20,
    v_spacing=20
):
    if not sizes:
        return

    # Normalize sizes input FIRST
    if isinstance(sizes, str):
        sizes = [s.strip() for s in sizes.split(",") if s.strip()]
    else:
        sizes = list(sizes)

    # Apply max limit
    sizes = sizes[:max_sizes]
    if not sizes:
        return

    draw = ImageDraw.Draw(canvas)
    W, H = canvas.size

    # Auto shrink if too many sizes
    n = len(sizes)
    if n >= shrink_threshold:
        box_w, box_h = box_size
        box_w = int(box_w * 0.85)
        box_h = int(box_h * 0.85)
        box_size = (box_w, box_h)
        font_size = max(20, font_size - 10)
    else:
        box_w, box_h = box_size

    font = load_font(font_path, font_size)

    # Determine grid layout
    rows = min(max_rows, n)
    cols = min(max_cols, (n + rows - 1) // rows)

    pos_x, pos_y = pos

    # Total grid size including spacing
    grid_w = cols * box_w + (cols - 1) * h_spacing
    grid_h = rows * box_h + (rows - 1) * v_spacing

    # Center if None
    if pos_x is None:
        pos_x = (W - grid_w) // 2
    else:
        pos_x = pos_x - grid_w // 2

    if pos_y is None:
        pos_y = (H - grid_h) // 2
    else:
        pos_y = pos_y - grid_h // 2

    x0 = pos_x
    y0 = pos_y

    # Row-based alternating colors, columns continue pattern
    def get_box_color(col, row):
        idx = (row + col) % len(box_colors)
        return box_colors[idx]

    def auto_text_color(rgb):
        avg = sum(rgb) / 3
        if avg < dark_threshold:
            return (255, 255, 255)  # white
        if avg > light_threshold:
            return (0, 0, 0)        # black
        return (255, 255, 255) if avg < 160 else (0, 0, 0)

    # Draw boxes
    idx = 0
    for r in range(rows):
        for c in range(cols):
            if idx >= n:
                break

            s = sizes[idx]

            bx1 = x0 + c * (box_w + h_spacing)
            by1 = y0 + r * (box_h + v_spacing)
            bx2 = bx1 + box_w
            by2 = by1 + box_h

            color = get_box_color(c, r)
            draw.rounded_rectangle([bx1, by1, bx2, by2], radius=box_radius, fill=color)

            # Measure text
            b = font.getbbox(s)
            tw = b[2] - b[0]
            th = b[3] - b[1]

            # Perfect centering with padding
            available_w = box_w - padding_left - padding_right
            available_h = box_h - padding_top - padding_bottom

            tx = bx1 + padding_left + max(0, (available_w - tw) // 2)
            ty = by1 + padding_top + max(0, (available_h - th) // 2)

            tcolor = auto_text_color(color)
            draw.text((tx, ty), s, fill=tcolor, font=font)

            idx += 1
