import base64
from pdf2image import convert_from_bytes
from io import BytesIO


def pdf_bytes_to_base64_images(pdf_bytes: bytes):

    images = convert_from_bytes(pdf_bytes, dpi=200)

    base64_images = []

    for image in images:
        buffer = BytesIO()
        image.save(buffer, format="PNG")

        base64_images.append(
            base64.b64encode(buffer.getvalue()).decode()
        )

    return base64_images
