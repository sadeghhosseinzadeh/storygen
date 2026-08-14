import importlib
import pkgutil
import inspect
from storygen.utils import remove_background, extract_colors
import storygen.templates as templates_pkg

# Discover all template modules and functions
TEMPLATES = {}
for loader, module_name, is_pkg in pkgutil.iter_modules(templates_pkg.__path__):
    module = importlib.import_module(f"{templates_pkg.__name__}.{module_name}")
    if hasattr(module, module_name):
        func = getattr(module, module_name)
        TEMPLATES[module_name] = func

def generate_story(template_name, shoe_path, **kwargs):
    if template_name not in TEMPLATES:
        raise ValueError(f"Unknown template: {template_name}")

    # Preprocess shoe image + colors once
    shoe_img = remove_background(shoe_path)
    main_color, second_color = extract_colors(shoe_img)

    # Build argument dict with common values
    base_args = {
        "shoe_img": shoe_img,
        "main_color": main_color,
        "second_color": second_color,
    }
    # Merge with user‑provided extras
    all_args = {**base_args, **kwargs}

    # Introspect the template function
    func = TEMPLATES[template_name]
    sig = inspect.signature(func)
    accepted_args = {
        name: value for name, value in all_args.items()
        if name in sig.parameters
    }

    # Call with only the arguments that function expects
    return func(**accepted_args)
