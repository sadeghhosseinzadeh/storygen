from rembg import remove
from io import BytesIO
import numpy as np
from sklearn.cluster import KMeans
from PIL import Image

def remove_background(path: str):
    """Remove background from an image file path."""
    with open(path, "rb") as f:
        input_bytes = f.read()
    output_bytes = remove(input_bytes)
    return Image.open(BytesIO(output_bytes))

def extract_colors(img: Image.Image):
    """Extract main and secondary colors using KMeans clustering."""
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
