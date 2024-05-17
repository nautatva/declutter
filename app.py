from flask import Flask, render_template, request, redirect, url_for, abort, send_file, jsonify
import os
import io
import base64
from PIL import Image
from config import config

from models.photo_manager import PhotoManager, Metric
from utils.db_utils import get_db, close_db

app = Flask(__name__)

# Load configuration
config_params = config()


app.teardown_appcontext(close_db)

def get_filename(filename_base64):
    # Decode the base64 filename
    try:
        filename = base64.b64decode(filename_base64).decode('utf-8')
    except Exception as e:
        abort(404)

    print(f"Requested image: {filename}")
    # filename is the absolute path to the image
    file_path = filename

    # base_dir = os.path.abspath("/path/to/your/images")  # Update to your images directory
    # file_path = os.path.join(base_dir, filename)

    # Security: Prevent directory traversal
    if ".." in filename or filename.startswith("/"):
        abort(404)

    # Check if file exists
    if not os.path.exists(file_path):
        abort(404)
    
    return file_path


@app.route('/static/images/<path:filename_base64>')
def serve_compressed_image(filename_base64):
    file_path = get_filename(filename_base64)

    # Open the image, compress it, and save to a BytesIO buffer
    try:
        img = Image.open(file_path)
        img_io = io.BytesIO()
        img.save(img_io, 'JPEG', quality=70)  # Compress and convert to JPEG
        img_io.seek(0)  # Rewind the file pointer to the start
    except Exception as e:
        abort(500)  # Internal server error if something goes wrong

    return send_file(img_io, mimetype='image/jpeg', as_attachment=True, download_name='compressed.jpg')

@app.route('/')
def index():    
    # Get the metric from the query parameters
    metric_name = request.args.get('metric', default=None, type=str)

    db = get_db()
    photo_manager = PhotoManager(base_path=config_params['basepath'], fav_path=config_params['favoritespath'], db=db)

    if metric_name is None or metric_name.upper() == "NONE":
        photo_dict = photo_manager.get_random_photo()
    else:
        # Map the metric name to the corresponding Enum member
        metric = getattr(Metric, metric_name.upper())
        if metric == Metric.DUPLICATES:
            photo_dict = photo_manager.get_duplicates()
        else:
            photo_dict = photo_manager.get_photos_by_metric_desc(metric)

    photo: str = photo_dict['path']
    # photo_name is the relative path to the image
    photo_relative_path = photo.replace(config_params['basepath'], '')
    # Separate the album name and photo name
    album_name, photo_name = os.path.split(photo_relative_path)
    # base64 encode the photo path
    photo = base64.b64encode(photo.encode('utf-8')).decode('utf-8')
    
    metrics = [metric.name for metric in Metric]
    return render_template('index.html', metrics=metrics, photo=photo, photo_size=round(photo_dict['size'], 2), dizziness=round(photo_dict['dizziness'] or 0, 2), photo_album=album_name, photo_name=photo_name)

@app.route('/swipe', methods=['POST'])
def swipe():
    db = get_db()
    photo_manager = PhotoManager(base_path=config_params['basepath'], fav_path=config_params['favoritespath'], db=db)
    photo_id = request.form['photo_id']
    action = request.form['action']

    photo_id = get_filename(photo_id)
    
    if action == 'left':
        photo_manager.move_to_bin(photo_id)
    elif action == 'right':
        photo_manager.accept_photo(photo_id)
    elif action == 'top':
        photo_manager.favorite_photo(photo_id)
    
    return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0')
