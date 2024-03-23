from flask import Flask, request, send_file
from flask_caching import Cache
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from PIL import Image
import pillow_avif
# import os
import io
import datetime
import requests
import logging
from urllib.parse import urlparse

app = Flask(__name__)

app.logger.addHandler(logging.StreamHandler())
app.logger.setLevel(logging.INFO)

cache = Cache(app, config={'CACHE_TYPE': 'filesystem', 'CACHE_DIR': 'cache', 'CACHE_THRESHOLD': 15})

limiter = Limiter(get_remote_address, app=app, default_limits=["30 per minute"], storage_uri="memory://")

SIZE_LIMIT = 10 * 1024 * 1024
MAX_PIXELS = 2560 * 1440


def get_time():
    return datetime.datetime.now().strftime("%m-%d-%Y %H:%M:%S")


def get_image_size(image_url):
    try:
        response = requests.head(image_url)
        response.raise_for_status()  # Raise an exception for invalid response
        if 'content-length' in response.headers:
            print(f'response.headers:\n{response.headers}')
            return int(response.headers['content-length'])
        else:
            return None  # Unable to determine image size
    except requests.exceptions.RequestException as e:
        # Handle request errors
        app.logger.error(f"{get_time()} - Request error: {e}")
        return None


# Define the route for serving the converted image
@app.route('/convert', methods=['GET'])
@limiter.limit("30 per minute")
def convert_image():
    app.logger.info(f"{get_time()} - Request from {request.remote_addr}")
    # Get the image URL from the query parameters
    image_url = request.args.get('url')
    if len(request.args) > 1:
        for key, value in request.args.items():
            image_url += f"&{key}={value}"

    # Check if the URL is provided
    if not image_url:
        return 'Image URL is required', 400

    try:
        result = convert(image_url)
        if result:
            return send_file(result, mimetype='image/webp')
        else:
            return 'Could not convert image. Maybe not a valid avif image link or image too large?', 400
    except Exception as e:
        return str(e), 500


@cache.memoize(timeout=3600)
def convert(image_url):
    image_name = urlparse(image_url).path.split('/')[-1]
    if image_name.split('.')[-1] != 'avif':
        app.logger.warning(f"{get_time()} - Not an avif image: {image_name}")
        return None

    app.logger.info(f"{get_time()} - Cache miss for {image_name}")

    # Check if image is within size limits
    size = get_image_size(image_url)
    if size is None:
        app.logger.warning(f"{get_time()} - Unable to determine image size: {image_name}")
        return None
    if size > SIZE_LIMIT:
        app.logger.warning(f"{get_time()} - Image size larger than {SIZE_LIMIT} bytes: {image_name}")
        return None

    # Download the image from the provided URL
    response = requests.get(image_url)
    response.raise_for_status()  # Raise an exception for invalid response

    # Open the downloaded image with PIL
    img = Image.open(io.BytesIO(response.content))
    num_pixels = img.size[0] * img.size[1]

    if num_pixels > MAX_PIXELS:
        app.logger.warning(f"{get_time()} - Image dimensions larger than {MAX_PIXELS} pixels: {image_name}")
        return None

    # Convert the image to webp format
    webp_buffer = io.BytesIO()
    img.save(webp_buffer, format='WEBP')
    webp_buffer.seek(0)

    # Return the converted image
    return webp_buffer


if __name__ == '__main__':
    app.run(debug=True)

# DEPRECATED
# Define the route for serving the image
# @app.route('/local/<image_name>.webp')
# def serve_image(image_name):
#     # Check if the image with the given name exists in avif format
#     avif_path = f'./images/{image_name}.avif'
#     if os.path.exists(avif_path):
#         # Convert the avif image to webp
#         webp_data = convert_image(avif_path)
#         return send_file(io.BytesIO(webp_data), mimetype='image/webp')
#         # return send_file(avif_path, mimetype='image/avif')
#     else:
#         return 'Image not found', 404
#
#
# # Function to convert image format
# @cache.memoize(timeout=3600)  # Cache the converted image for 1 hour
# def convert_image(input_path):
#     with Image.open(input_path) as img:
#         output_buffer = io.BytesIO()
#         img.save(output_buffer, format='WEBP', quality=80)
#
#         timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
#         app.logger.info(f"Cache generated at: {timestamp}")
#
#         return output_buffer.getvalue()

# DEPRECATED
# Function to convert image format and store on disk
# def convert_image(input_path, output_path):
#     with Image.open(input_path) as img:
#         img.save(output_path)
