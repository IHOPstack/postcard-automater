from config import get_setting
import os
import json

import tempfile
 

class FileManager:
    def __init__(self):
        self.images = []
        self.front_images = []
        self.back_images = []
        self.load_persisted_files()
        self.temp_dir = tempfile.mkdtemp()


    def add_files(self, new_files):
        for file in new_files:
            if file not in self.images:
                self.images.append(file)
                
                # Auto-select logic
                if not self.front_images:
                    self.front_images.append(file)
                elif not self.back_images:
                    self.back_images.append(file)

    def remove_file(self, file_path):
        if file_path in self.images:
            self.images.remove(file_path)
        if file_path in self.front_images:
            self.front_images.remove(file_path)
        if file_path in self.back_images:
            self.back_images.remove(file_path)

    def update_image_list(self, file_path, is_checked, is_front):
        target_list = self.front_images if is_front else self.back_images
        if is_checked and file_path not in target_list:
            target_list.append(file_path)
        elif not is_checked and file_path in target_list:
            target_list.remove(file_path)

    def clear_files(self):
        self.images.clear()
        self.front_images.clear()
        self.back_images.clear()

    def get_images(self):
        return self.images

    def get_selected_images(self):
        return self.front_images, self.back_images

    def select_all(self, is_front, checked):
        target_list = self.front_images if is_front else self.back_images
        if checked:
            target_list.clear()
            target_list.extend(self.images)
        else:
            target_list.clear()

    def load_persisted_files(self):
        if get_setting("user_modifiable.persist_files"):
            try:
                with open("persisted_files.json", "r") as f:
                    persisted_files = json.load(f)
                self.add_files(persisted_files)
            except FileNotFoundError:
                print("No persisted files found.")

    def save_persisted_files(self):
        if get_setting("user_modifiable.persist_files"):
            with open("persisted_files.json", "w") as f:
                json.dump(self.images, f)
