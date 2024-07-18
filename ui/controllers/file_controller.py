from config import get_setting
import json
import os

class FileManager:
    def __init__(self, main_window):
        self.main_window = main_window
        self.files = []
        self.front_images = []
        self.back_images = []

    def add_files(self, new_files, auto_select_front=False, auto_select_back=False):
        for file in new_files:
            if file not in self.files and os.path.exists(file):
                self.files.append(file)
                image_widget = self.main_window.file_list.add_item(file)
                if auto_select_front:
                    image_widget.front_checkbox.setChecked(True)
                    if file not in self.front_images:
                        self.front_images.append(file)
                elif auto_select_back:
                    image_widget.back_checkbox.setChecked(True)
                    if file not in self.back_images:
                        self.back_images.append(file)

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
                json.dump(self.files, f)

    def clear_files(self):
        self.files.clear()
        self.front_images.clear()
        self.back_images.clear()
        self.main_window.file_list.clear()
        self.main_window.file_list._setup_header()

    def get_selected_images(self):
        self.front_images.clear()
        self.back_images.clear()
        for index in range(1, self.main_window.file_list.count()):
            item = self.main_window.file_list.item(index)
            image_widget = self.main_window.file_list.itemWidget(item)
            if image_widget.front_checkbox.isChecked():
                self.front_images.append(image_widget.image_path)
            if image_widget.back_checkbox.isChecked():
                self.back_images.append(image_widget.image_path)
        return self.front_images, self.back_images

    def select_all_front(self, checked):
        self.front_images.clear()
        for index in range(1, self.main_window.file_list.count()):
            item = self.main_window.file_list.item(index)
            image_widget = self.main_window.file_list.itemWidget(item)
            image_widget.front_checkbox.setChecked(checked)
            if checked:
                self.front_images.append(image_widget.image_path)

    def select_all_back(self, checked):
        self.back_images.clear()
        for index in range(1, self.main_window.file_list.count()):
            item = self.main_window.file_list.item(index)
            image_widget = self.main_window.file_list.itemWidget(item)
            image_widget.back_checkbox.setChecked(checked)
            if checked:
                self.back_images.append(image_widget.image_path)
