from config import config
import cv2
import numpy as np
from utils.db_utils import get_raw_db, close_db_sqlite
from models.photo_manager import PhotoManager
from utils.common_utils import is_json_key_present


TIME_THRESHOLD = 300  # 5 minutes in seconds
SIMILARITY_THRESHOLD = 0.8

def calculate_similarity(photo1_path, photo2_path):
    # Load images
    img1 = cv2.imread(photo1_path, cv2.IMREAD_GRAYSCALE)
    img2 = cv2.imread(photo2_path, cv2.IMREAD_GRAYSCALE)
    
    # Initialize ORB detector
    orb = cv2.ORB()
    
    # Find keypoints and descriptors
    try:
        kp1, des1 = orb.detectAndCompute(img1, None)
        kp2, des2 = orb.detectAndCompute(img2, None)
    except cv2.error as e:
        # print("Error in image", photo1_path, photo2_path, e)
        return 0
    
    # Match descriptors using BFMatcher
    bf = cv2.BFMatcher(cv2.NORM_HAMMING, crossCheck=True)
    matches = bf.match(des1, des2)
    
    # Calculate similarity score based on the number of good matches
    good_matches = [m for m in matches if m.distance < 50]  # Adjust threshold as needed
    similarity_score = len(good_matches) / max(len(kp1), len(kp2))
    
    return similarity_score


config_params = config()
db = get_raw_db()
photo_manager = PhotoManager(base_path=config_params['basepath'], fav_path=config_params['favoritespath'], db=db)

cursor = db.cursor()
cursor.execute("""
    CREATE TABLE IF NOT EXISTS image_similarity (
    id INTEGER PRIMARY KEY,
    image1 TEXT NOT NULL,
    image2 TEXT,
    similarity_index REAL NOT NULL
    )
""")
db.commit()

photos = photo_manager.get_all_unmarked_photos()

cursor = db.cursor()
DB_COMMIT_SIZE = 10


similar_images = db.execute("SELECT image1, image2 FROM image_similarity")
similar_images_map = {}  # Image -> List of similar images

def append_to_similar_images_map(image1, image2, similar_images_map):
    if not is_json_key_present(similar_images_map, image1):
        similar_images_map[image1] = []
    if not is_json_key_present(similar_images_map, image2):
        similar_images_map[image2] = []
    similar_images_map[image1].append(image2)
    similar_images_map[image2].append(image1)

for row in similar_images:
    row = row
    image1 = row[0]
    image2 = row[1]
    if image2 is None:
        similar_images_map[image1] = []
    else:
        append_to_similar_images_map(image1, image2, similar_images_map)

img_pointer = 0
for photo in photos:
    img_pointer = img_pointer + 1
    path = photo['path']
    print("Processing", path)
    if is_json_key_present(similar_images_map, path):
        continue

    # timestamp is saved like this
    # capture_date_epoch = int(time.mktime(capture_date.timetuple()))
    # cursor.execute("INSERT OR IGNORE INTO photos (path, size, capture_date) VALUES (?, ?, ?)", (photo, size, capture_date_epoch))
    # db.commit()
    
    # Query for all images that are +-5min from the current image
    time_filtered_images = cursor.execute("SELECT path FROM photos WHERE capture_date BETWEEN ? AND ?", (photo['capture_date'] - TIME_THRESHOLD, photo['capture_date'] + TIME_THRESHOLD))
    duplicate_found = False
    for image in time_filtered_images:
        image = image[0]
        if image == path:
            continue
        similarity_score = calculate_similarity(path, image)
        if similarity_score >= SIMILARITY_THRESHOLD:
            duplicate_found = True
            cursor.execute("INSERT INTO image_similarity (image1, image2, similarity_index) VALUES (?, ?, ?)", (path, image, similarity_score))
            append_to_similar_images_map(path, image, similar_images_map)
            print("Similar images found", path, image, similarity_score)

    if not duplicate_found:
        cursor.execute("INSERT INTO image_similarity (image1, image2, similarity_index) VALUES (?, ?, ?)", (path, None, 0))
        append_to_similar_images_map(path, None, similar_images_map)

    if (img_pointer%DB_COMMIT_SIZE == 0):
        print("Entries committed", img_pointer)
        db.commit()

if (img_pointer%DB_COMMIT_SIZE != 0):
    db.commit()

close_db_sqlite(db)
