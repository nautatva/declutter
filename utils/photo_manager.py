import os
import random
import sqlite3
from shutil import move, copy2

BIN = "Bin"
IMAGE_EXTENSIONS = ['.png', '.jpg', '.jpeg']

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
        status TEXT
                    )
        """)
        self.conn.commit()

    def refresh_scan(self):
        cursor = self.conn.cursor()

        # Get existing photos from DB
        cursor.execute("SELECT path FROM photos")
        existing_photos = [row[0] for row in cursor.fetchall()]

        # Scan for new photos
        all_photos = [os.path.join(dp, f) for dp, dn, filenames in os.walk(self.base_path) for f in filenames if os.path.splitext(f)[1].lower() in IMAGE_EXTENSIONS]
        new_photos = [photo for photo in all_photos if photo not in existing_photos]

        # Insert new photos into DB
        for photo in new_photos:
            folder = os.path.dirname(photo)
            if folder == BIN:
                continue
            size = os.path.getsize(photo)
            cursor.execute("INSERT OR IGNORE INTO photos (path, size) VALUES (?, ?)", (photo, size))

        self.conn.commit()
        return len(new_photos)

    def get_all_unmarked_photos(self, refresh_photos_if_nothing_found=True):
        # List all photos that are not yet marked in the database
        cursor = self.conn.cursor()
        cursor.execute("SELECT path, size FROM photos WHERE status IS NULL ORDER BY size desc")
        unchecked_photos = cursor.fetchall()

        if not unchecked_photos and refresh_photos_if_nothing_found:
            self.refresh_scan()
            return self.get_all_unmarked_photos(refresh_photos_if_nothing_found=False)

        return unchecked_photos

    def get_photos_by_size_desc(self):
        photos = self.get_all_unmarked_photos()
        return photos[0][0], photos[0][1] if photos else None

    def get_random_photo(self):
        unchecked_photos = self.get_all_unmarked_photos()
        return random.choice([x[0] for x in unchecked_photos]) if unchecked_photos else None

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
