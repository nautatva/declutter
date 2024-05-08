import os
import random
import sqlite3
from shutil import move, copy2

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
                status TEXT
            )
        """)
        self.conn.commit()

    def get_random_photo(self):
        # List all photos that are not yet marked in the database
        cursor = self.conn.cursor()
        cursor.execute("SELECT path FROM photos WHERE status IS NULL")
        unchecked_photos = cursor.fetchall()

        if not unchecked_photos:
            # If all photos are checked, scan for new ones
            all_photos = [os.path.join(dp, f) for dp, dn, filenames in os.walk(self.base_path) for f in filenames if os.path.splitext(f)[1].lower() in ['.png', '.jpg', '.jpeg']]
            new_photos = [p for p in all_photos if p not in [x[0] for x in unchecked_photos]]
            for photo in new_photos:
                cursor.execute("INSERT OR IGNORE INTO photos (path) VALUES (?)", (photo,))
            self.conn.commit()
            return random.choice(new_photos) if new_photos else None
        return random.choice([x[0] for x in unchecked_photos])

    def update_photo_status(self, photo_path, status):
        cursor = self.conn.cursor()
        cursor.execute("UPDATE photos SET status = ? WHERE path = ?", (status, photo_path))
        self.conn.commit()

    def move_to_bin(self, photo_path):
        bin_path = self.bin_path
        if not self.bin_path:
            album_path = os.path.dirname(photo_path)
            bin_path = os.path.join(album_path, 'Bin')
            if not os.path.exists(bin_path):
                os.makedirs(bin_path)
        print(bin_path)
        print(f"Moving photo to bin: {photo_path}")
        dest_path = os.path.join(bin_path, os.path.basename(photo_path))
        move(photo_path, dest_path)
        self.update_photo_status(photo_path, 'deleted')

    def accept_photo(self, photo_path):
        # Accepting a photo doesn't need to move it, just a placeholder
        self.update_photo_status(photo_path, 'accepted')

    def favorite_photo(self, photo_path):
        # Copy to favorites and adjust metadata if needed
        copy2(photo_path, self.fav_path)
        # Set metadata to 5 stars (this is just a placeholder)
        self.update_photo_status(photo_path, 'favorited')
