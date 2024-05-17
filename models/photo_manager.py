import os
import random
from shutil import move, copy2
from .Metric import Metric
from utils.file_utils import get_most_accurate_creation_date_from_file
import time
from utils.app_utils import append_to_similar_images_map

BIN = "Bin"
IMAGE_EXTENSIONS = ['.png', '.jpg', '.jpeg']
DB_COMMIT_SIZE = 100

class PhotoManager:
    def __init__(self, base_path, fav_path, db, bin_path=None):
        self.base_path = base_path
        self.bin_path = bin_path
        self.fav_path = fav_path
        self.db = db
        self._init_db()

    def _init_db(self):
        self.conn = self.db  # sqlite3.connect(self.db_path, check_same_thread=False)
        cursor = self.conn.cursor()
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS photos (
        id INTEGER PRIMARY KEY,
        path TEXT UNIQUE,
        size INTEGER,
        capture_date INTEGER,
        dizziness INTEGER,
        status TEXT
        )
        """)
        self.conn.commit()

    def refresh_scan(self):
        cursor = self.conn.cursor()

        # Get existing photos from DB
        existing_photos = cursor.execute("SELECT path FROM photos")
        existing_photos = [row[0] for row in existing_photos.fetchall()]

        # Scan for new photos
        all_photos = [os.path.join(dp, f) for dp, dn, filenames in os.walk(self.base_path) for f in filenames if os.path.splitext(f)[1].lower() in IMAGE_EXTENSIONS]
        new_photos = [photo for photo in all_photos if photo not in existing_photos]
        
        # Insert new photos into DB
        img_count = 0
        for photo in new_photos:
            img_count += 1
            folder = os.path.basename(os.path.dirname(photo))
            if folder == BIN:
                continue
            size = os.path.getsize(photo) / 1024 / 1024
            capture_date, _ = get_most_accurate_creation_date_from_file(photo, quick=True)
            
            # Convert capture_date to epoch timestamp
            if capture_date:
                capture_date_epoch = int(time.mktime(capture_date.timetuple()))
            else:
                capture_date_epoch = None

            cursor.execute("INSERT OR IGNORE INTO photos (path, size, capture_date) VALUES (?, ?, ?)", (photo, size, capture_date_epoch))

            if img_count % DB_COMMIT_SIZE == 0:
                print("Img count is", img_count)
                self.conn.commit()

        if img_count % DB_COMMIT_SIZE != 0:
            self.conn.commit()

        self.conn.commit()
        return len(new_photos)

    def get_all_unmarked_photos(self, sort_by_desc="id", photo_paths=None, refresh_photos_if_nothing_found=True):
        # List all photos that are not yet marked in the database
        cursor = self.conn.cursor()
        if photo_paths is not None:
            # photo_paths separated by ,
            # photo_paths = photo_paths.split(",")
            query = f"SELECT * FROM photos WHERE path in ({','.join(['?']*len(photo_paths))}) ORDER BY {sort_by_desc} desc"
            photos = cursor.execute(query, photo_paths)
        else:
            photos = cursor.execute(f"SELECT * FROM photos WHERE status IS NULL ORDER BY {sort_by_desc} desc")
        unchecked_photos = photos.fetchall()

        if not unchecked_photos and refresh_photos_if_nothing_found:
            self.refresh_scan()
            return self.get_all_unmarked_photos(refresh_photos_if_nothing_found=False)

        # Get column names
        column_names = [description[0] for description in cursor.description]

        # Convert photos to JSON format
        photos_json = []
        for photo in unchecked_photos:
            photo_dict = {}
            for idx, column in enumerate(column_names):
                photo_dict[column] = photo[idx]
            photos_json.append(photo_dict)

        return photos_json

    def get_photos_by_metric_desc(self, metric: Metric):
        photos = self.get_all_unmarked_photos(metric.name)
        return photos[0] if photos else None

    def get_random_photo(self):
        unchecked_photos = self.get_all_unmarked_photos()
        return random.choice(unchecked_photos) if unchecked_photos else None
    
    def get_duplicates(self):
        # SELECT image1, image2 FROM image_similarity
        cursor = self.conn.cursor()
        similar_images = cursor.execute("SELECT image1, image2 FROM image_similarity")
        similar_images_map = {}  # Image -> List of similar images
        for row in similar_images:
            row = row
            image1 = row[0]
            image2 = row[1]
            if image2 is None:
                continue
            else:
                append_to_similar_images_map(image1, image2, similar_images_map)
        
        # Remove image keys that are present in values
        keys = list(similar_images_map.keys())
        for key in keys:
            if key not in similar_images_map.keys():
                continue
            similar_images = similar_images_map[key]
            for image in similar_images:
                if image in similar_images_map:
                    del similar_images_map[image]

        print(similar_images_map)

        return similar_images_map

    def get_duplicates_given_images(self, photo_path: str):
        cursor = self.conn.cursor()
        similar_images = cursor.execute("SELECT image1, image2 FROM image_similarity where image1 = ? or image2 = ?", (photo_path, photo_path))
        similar_images = similar_images.fetchall()
        similar_images = [img[0] for img in similar_images]
        images = self.get_all_unmarked_photos(photo_paths=similar_images)
        return images

    def update_photo_status(self, photo_path, status):
        cursor = self.conn.cursor()
        cursor.execute("UPDATE photos SET status = ? WHERE path = ?", (status, photo_path))
        self.conn.commit()

    def move_to_bin(self, photo_path):
        bin_path = self.bin_path
        if not self.bin_path:
            album_path = os.path.dirname(photo_path)
            bin_path = os.path.join(album_path, BIN)
            if not os.path.exists(bin_path):
                os.makedirs(bin_path)
        print(bin_path)
        print(f"Moving photo to bin: {photo_path}")
        dest_path = os.path.join(bin_path, os.path.basename(photo_path))
        move(photo_path, dest_path)
        self.update_photo_status(photo_path, BIN)

    def accept_photo(self, photo_path):
        # Accepting a photo doesn't need to move it, just a placeholder
        self.update_photo_status(photo_path, 'accepted')

    def favorite_photo(self, photo_path):
        # Copy to favorites and adjust metadata if needed
        copy2(photo_path, self.fav_path)
        # Set metadata to 5 stars (this is just a placeholder)
        self.update_photo_status(photo_path, 'favorited')

    def flag_image(self, photo_path):
        # Flag an image for review
        self.update_photo_status(photo_path, "Flagged")
