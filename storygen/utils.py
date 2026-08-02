def lighten_color(color, strength=0.15):
    return tuple(int(c * strength + 255 * (1 - strength)) for c in color)
