from flask import Flask, request, send_file
from flask_caching import Cache
from PIL import Image
import pillow_avif
import os
import io
import datetime
import requests
import logging

app = Flask(__name__)

app.logger.addHandler(logging.StreamHandler())
app.logger.setLevel(logging.INFO)

cache = Cache(app, config={'CACHE_TYPE': 'simple'})


# Define the route for serving the converted image
@cache.memoize(timeout=3600)
@app.route('/convert', methods=['GET'])
def convert_image():
    # Get the image URL from the query parameters
    image_url = request.args.get('url')
    if len(request.args) > 1:
        for key, value in request.args.items():
            image_url += f"&{key}={value}"

    # Check if the URL is provided
    if not image_url:
        return 'Image URL is required', 400

    try:
        # Download the image from the provided URL
        response = requests.get(image_url)
        response.raise_for_status()  # Raise an exception for invalid response

        # Open the downloaded image with PIL
        img = Image.open(io.BytesIO(response.content))

        # Convert the image to webp format
        webp_buffer = io.BytesIO()
        img.save(webp_buffer, format='WEBP')
        webp_buffer.seek(0)

        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        app.logger.info(f"Cache generated at: {timestamp}")

        # Return the converted image
        return send_file(webp_buffer, mimetype='image/webp')
    except Exception as e:
        return str(e), 500


# Define the route for serving the image
@app.route('/local/<image_name>.webp')
def serve_image(image_name):
    # Check if the image with the given name exists in avif format
    avif_path = f'./images/{image_name}.avif'
    if os.path.exists(avif_path):
        # Convert the avif image to webp
        webp_data = convert_image(avif_path)
        return send_file(io.BytesIO(webp_data), mimetype='image/webp')
        # return send_file(avif_path, mimetype='image/avif')
    else:
        return 'Image not found', 404


# Function to convert image format
@cache.memoize(timeout=3600)  # Cache the converted image for 1 hour
def convert_image(input_path):
    with Image.open(input_path) as img:
        output_buffer = io.BytesIO()
        img.save(output_buffer, format='WEBP', quality=80)

        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        app.logger.info(f"Cache generated at: {timestamp}")

        return output_buffer.getvalue()


# Function to convert image format and store on disk
# def convert_image(input_path, output_path):
#     with Image.open(input_path) as img:
#         img.save(output_path)


if __name__ == '__main__':
    app.run(debug=True)
