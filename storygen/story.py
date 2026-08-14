import importlib
import pkgutil
from storygen.utils import remove_background, extract_colors

# Dynamically import all modules in storygen.templates
import storygen.templates as templates_pkg

TEMPLATES = {}

for loader, module_name, is_pkg in pkgutil.iter_modules(templates_pkg.__path__):
    module = importlib.import_module(f"{templates_pkg.__name__}.{module_name}")
    # convention: each template file defines a function with the same name
    if hasattr(module, module_name):
        TEMPLATES[module_name] = getattr(module, module_name)

def generate_story(template_name, shoe_path, model_name, sizes,
                   brand_name=None, shop_name=None, username=None, photo_2=None):
    shoe_img = remove_background(shoe_path)
    main_color, second_color = extract_colors(shoe_img)

    if template_name not in TEMPLATES:
        raise ValueError(f"Unknown template: {template_name}")

    # Call the template function dynamically
    return TEMPLATES[template_name](
        shoe_img, main_color, second_color,
        model_name, sizes, brand_name, shop_name, username, photo_2
    )
