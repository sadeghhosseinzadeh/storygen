from storygen.processing import remove_background, extract_colors
from storygen.templates import template_1

def generate_story(template_name, shoe_path, model_name, sizes):
    shoe_img = remove_background(shoe_path)
    main_color, second_color = extract_colors(shoe_img)

    if template_name == "template_1":
        story = template_1.template_1(shoe_img, main_color, second_color, model_name, sizes)
    else:
        raise ValueError(f"Unknown template: {template_name}")

    return story
