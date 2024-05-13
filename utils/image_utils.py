import cv2
import numpy as np

def dizziness_factor(photo_path):
    image = cv2.imread(photo_path)
    # Convert to grayscale
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    # Calculate the difference between consecutive frames (which is the same as the image itself)
    diff = cv2.absdiff(gray, cv2.GaussianBlur(gray, (5, 5), 0))
    # Calculate the mean of the absolute differences
    dizziness_factor = np.mean(diff)
    return dizziness_factor
