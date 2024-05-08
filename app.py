from flask import Flask, g, render_template, request, redirect, url_for, abort, send_file
from utils.photo_manager import PhotoManager
import os
import io
import base64
from PIL import Image
from config import config
import sqlite3

app = Flask(__name__)

# Load configuration
config_params = config()

def get_db():
    if 'db' not in g:
        g.db = sqlite3.connect('photo_manager.db')
        g.db.row_factory = sqlite3.Row
    return g.db

def close_db(e=None):
    db = g.pop('db', None)
    if db is not None:
        db.close()

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
    # Get a random photo from the album
    db = get_db()
    photo_manager = PhotoManager(base_path=config_params['basepath'], fav_path=config_params['favoritespath'], db=db)
    photo = photo_manager.get_random_photo()
    # base64 encode the photo path

    # photo_name is the relative path to the image
    photo_relative_path = photo.replace(config_params['basepath'], '')
    # Separate the album name and photo name
    album_name, photo_name = os.path.split(photo_relative_path)
    photo = base64.b64encode(photo.encode('utf-8')).decode('utf-8')
    return render_template('index.html', photo=photo, photo_album=album_name, photo_name=photo_name)

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
    app.run(debug=True)
