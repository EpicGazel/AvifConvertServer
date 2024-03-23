from flask import Flask, send_file
from flask_caching import Cache
from PIL import Image
import pillow_avif
import os
import io
import datetime

app = Flask(__name__)

cache = Cache(app, config={'CACHE_TYPE': 'simple'})

# Define the route for serving the image
@app.route('/<image_name>.webp')
def serve_image(image_name):
    # Check if the image with the given name exists in avif format
    avif_path = f'./images/avifs/{image_name}.avif'
    if os.path.exists(avif_path):
        # Convert the avif image to webp
        #webp_data = convert_image(avif_path)
        #return send_file(io.BytesIO(webp_data), mimetype='image/webp')
        return send_file(avif_path, mimetype='image/avif')
    else:
        return 'Image not found', 404


# Function to convert image format
@cache.memoize(timeout=15)  # Cache the converted image for 1 hour
def convert_image(input_path):
    with Image.open(input_path) as img:
        output_buffer = io.BytesIO()
        img.save(output_buffer, format='WEBP', quality=80)
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        print(f"Cache generated at: {timestamp}")
        return output_buffer.getvalue()

# Function to convert image format
# def convert_image(input_path, output_path):
#     with Image.open(input_path) as img:
#         img.save(output_path)


if __name__ == '__main__':
    app.run(debug=True)
