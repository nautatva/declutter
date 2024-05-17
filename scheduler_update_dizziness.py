from config import config
import cv2
import numpy as np
from utils.db_utils import get_raw_db, close_db_sqlite
from models.photo_manager import PhotoManager, Metric


config_params = config()
db = get_raw_db()
photo_manager = PhotoManager(base_path=config_params['basepath'], fav_path=config_params['favoritespath'], db=db)
photos = photo_manager.get_all_unmarked_photos()

cursor = db.cursor()
DB_COMMIT_SIZE = 100

def dizziness_factor(photo_path):
    image = cv2.imread(photo_path)
    # Convert to grayscale
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    # Calculate the difference between consecutive frames (which is the same as the image itself)
    diff = cv2.absdiff(gray, cv2.GaussianBlur(gray, (5, 5), 0))
    # Calculate the mean of the absolute differences
    dizziness_factor = np.mean(diff)
    return dizziness_factor

img_pointer = 0
for photo in photos:
    img_pointer = img_pointer + 1
    path = photo['path']
    if (photo[Metric.DIZZINESS.value] is not None):
        continue
    dizziness = dizziness_factor(path)
    print("Dizziness for", path, dizziness)
    cursor.execute("UPDATE photos SET dizziness = ? WHERE path = ?", (dizziness, path))
    if (img_pointer%DB_COMMIT_SIZE == 0):
        print("Entries committed", img_pointer)
        db.commit()

if (img_pointer%DB_COMMIT_SIZE != 0):
    db.commit()

close_db_sqlite(db)
