from .common_utils import is_json_key_present


def append_first_image_to_similar_images_map(image1, image2, similar_images_map):
    if not is_json_key_present(similar_images_map, image1):
        similar_images_map[image1] = []
    similar_images_map[image1].append(image2)

def append_to_similar_images_map(image1, image2, similar_images_map):
    append_first_image_to_similar_images_map(image1, image2, similar_images_map)
    append_first_image_to_similar_images_map(image2, image1, similar_images_map)
