import io
from PIL import Image
from ..config import settings

def resize_image_bytes(image_bytes: bytes, max_dim: int = None, quality: int = None) -> bytes:
    """
    Downscales image if dimensions exceed max_dim, keeping aspect ratio.
    Converts RGBA/P to RGB and re-encodes as JPEG to minimize transfer payload and API token cost.
    """
    if max_dim is None:
        max_dim = settings.max_image_dimension
    if quality is None:
        quality = settings.image_jpeg_quality

    try:
        image = Image.open(io.BytesIO(image_bytes))
        
        # Convert to RGB if necessary
        if image.mode in ("RGBA", "P", "LA"):
            image = image.convert("RGB")
            
        width, height = image.size
        if width > max_dim or height > max_dim:
            if width > height:
                new_width = max_dim
                new_height = int((height / width) * max_dim)
            else:
                new_height = max_dim
                new_width = int((width / height) * max_dim)
            image = image.resize((new_width, new_height), Image.Resampling.LANCZOS)
            
        output_buffer = io.BytesIO()
        image.save(output_buffer, format="JPEG", quality=quality, optimize=True)
        return output_buffer.getvalue()
    except Exception as e:
        # If pillow processing fails, return original bytes
        print(f"Warning: Image resizing failed: {e}")
        return image_bytes
