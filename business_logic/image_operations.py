from typing import List

def add_image(image_list: List[str], new_image: str) -> List[str]:
    if new_image not in image_list:
        image_list.append(new_image)
    return image_list

def remove_image(image_list: List[str], image: str) -> List[str]:
    if image in image_list:
        image_list.remove(image)
    return image_list

def get_images(image_list: List[str]) -> List[str]:
    return image_list.copy()

def is_supported_image(file_path: str) -> bool:
    supported_extensions = ('.png', '.jpg', '.jpeg', '.bmp')
    return file_path.lower().endswith(supported_extensions)
